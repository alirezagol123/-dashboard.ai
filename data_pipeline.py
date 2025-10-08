import json
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import math
import os
import time
import threading
import queue
from contextlib import contextmanager
from dotenv import load_dotenv
import dateutil.parser

# Load environment variables
load_dotenv()

# LangChain imports for LLM preprocessing
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Configure logging with UTF-8 encoding
file_handler = logging.FileHandler('data_pipeline.log', encoding='utf-8')
stream_handler = logging.StreamHandler()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s - %(message)s',
    handlers=[file_handler, stream_handler]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database connection manager to prevent locks"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._lock = threading.RLock()
        self._connection_pool = {}
        self._max_retries = 3
        self._retry_delay = 0.1
    
    @contextmanager
    def get_connection(self):
        """Get a thread-safe database connection with automatic cleanup"""
        conn = None
        try:
            # Create connection while holding lock to safely set PRAGMAs
            with self._lock:
                conn = sqlite3.connect(
                    self.db_file,
                    timeout=30.0,
                    check_same_thread=False,
                    isolation_level=None
                )
                # Performance-friendly pragmas for WAL mode
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA cache_size=10000;")
                conn.execute("PRAGMA temp_store=MEMORY;")
            # Yield after releasing lock (so other threads can create connections)
            yield conn
        finally:
            if conn:
                try:
                    conn.close()
                except Exception:
                    pass
    
    def execute_with_retry(self, query: str, params: tuple = (), max_retries: int = 3, retry_delay: float = 0.5):
        """Execute query with automatic retry on lock - returns rows for SELECT, rowcount for INSERT/UPDATE"""
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                with self.get_connection() as conn:
                    cur = conn.cursor()
                    cur.execute(query, params)
                    qtype = query.strip().split()[0].upper()
                    if qtype == "SELECT":
                        rows = cur.fetchall()
                        return rows
                    else:
                        conn.commit()
                        return {"rowcount": cur.rowcount, "lastrowid": cur.lastrowid}
            except sqlite3.OperationalError as e:
                last_exc = e
                logger.warning(f"DB OperationalError (attempt {attempt}) - {e}")
                time.sleep(retry_delay * (attempt + 1))
        logger.error("execute_with_retry failed: %s", last_exc)
        raise last_exc

class DataPipeline:
    """Data pipeline for processing raw sensor data through validation and normalization"""
    
    def __init__(self, db_file="smart_dashboard.db", batch_size=100, flush_interval=2.0):
        self.db_file = db_file
        self.processed_count = 0
        self.rejected_count = 0
        self.normalized_count = 0
        
        # Initialize database manager for thread-safe operations
        self.db_manager = DatabaseManager(db_file)
        
        # Initialize batch writer
        self.insert_queue = queue.Queue()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._writer_thread = threading.Thread(target=self._writer_loop, daemon=True)
        self._stop_event = threading.Event()
        self._writer_thread.start()
        
        # Initialize LLM for intelligent preprocessing
        self._init_llm()
        
        # Initialize database
        self._init_database()
        
        logger.info("Data Pipeline initialized successfully")
    
    def _init_llm(self):
        """Initialize LLM for intelligent data preprocessing"""
        try:
            # Get LLM configuration
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
            
            if self.api_key and self.api_key != "your-openai-api-key-here" and len(self.api_key) > 10:
                self.llm = ChatOpenAI(
                    openai_api_key=self.api_key,
                    openai_api_base=self.base_url,
                    model_name=self.model_name,
                    temperature=0.1
                )
                logger.info(f"LLM initialized for data pipeline: {self.model_name}")
                self.llm_enabled = True
            else:
                logger.warning("LLM not available - using rule-based processing only")
                self.llm_enabled = False
                self.llm = None
                
        except Exception as e:
            logger.error(f"LLM initialization failed: {e}")
            self.llm_enabled = False
            self.llm = None
    
    def _init_database(self):
        """Initialize database with sensor_data table using thread-safe manager"""
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create sensor_data table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sensor_data (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        sensor_type TEXT NOT NULL,
                        value REAL NOT NULL,
                        unit TEXT,
                        source TEXT,
                        raw_json TEXT
                    )
                ''')
                
                # Add indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sensor_type_timestamp ON sensor_data(sensor_type, timestamp);")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON sensor_data(timestamp);")
                
                conn.commit()
                logger.info(f"Database initialized: {self.db_file}")
                
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def _to_utc_iso(self, ts):
        """Normalize timestamps to UTC ISO format"""
        try:
            # If it's numeric (epoch)
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
                return dt.isoformat()
            # Try parsing with dateutil for robustness
            dt = dateutil.parser.parse(ts)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.isoformat()
        except Exception:
            # Fallback to now UTC
            return datetime.now(timezone.utc).isoformat()
    
    def validate_data(self, raw_record: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate raw sensor data against business rules
        
        Args:
            raw_record: Raw sensor data dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            sensor_type = raw_record.get('sensor', '')
            value = raw_record.get('value')
            unit = raw_record.get('unit', '')
            timestamp_str = raw_record.get('timestamp', '')
            
            # Check if value is None or invalid type
            if value is None:
                return False, f"Missing value for {sensor_type}"
            
            if not isinstance(value, (int, float)):
                return False, f"Invalid value type for {sensor_type}: {type(value)}"
            
            # Check for extreme values that indicate sensor malfunction
            if isinstance(value, (int, float)) and (math.isnan(value) or math.isinf(value)):
                return False, f"Invalid numeric value for {sensor_type}: {value}"
            
            # Sensor-specific validation rules
            if sensor_type == "temperature":
                # Convert to Celsius for validation if needed
                temp_celsius = self._convert_to_celsius(value, unit)
                if temp_celsius < -50 or temp_celsius > 70:
                    return False, f"Temperature out of range: {temp_celsius}°C (value: {value} {unit})"
            
            elif sensor_type == "humidity":
                if value < 0 or value > 100:
                    return False, f"Humidity out of range: {value}%"
            
            elif sensor_type == "soil_moisture":
                if value < 0 or value > 100:
                    return False, f"Soil moisture out of range: {value}%"
            
            elif sensor_type == "pest_count":
                if value < 0:
                    return False, f"Pest count cannot be negative: {value}"
            
            elif sensor_type == "soil_ph":
                if value < 0 or value > 14:
                    return False, f"pH out of range: {value}"
            
            elif sensor_type == "pressure":
                if value < 800 or value > 1200:
                    return False, f"Pressure out of range: {value} {unit}"
            
            elif sensor_type == "light":
                if value < 0:
                    return False, f"Light intensity cannot be negative: {value}"
            
            # Check timestamp validity (simplified - skip for now)
            # TODO: Fix timestamp validation
            pass
            
            # Check for extreme outliers (values that are clearly wrong)
            if isinstance(value, (int, float)):
                # Check for extreme values that indicate data corruption
                if abs(value) > 1e6:  # Values larger than 1 million
                    return False, f"Extreme value detected: {value} {unit}"
                
            # Check for values that are too precise (likely corrupted)
            if isinstance(value, float) and len(str(value).split('.')[-1]) > 10:
                return False, f"Overly precise value: {value} {unit}"
            
            # LLM-powered intelligent validation (optional - don't block on LLM issues)
            if self.llm_enabled:
                try:
                    llm_result = self._llm_validate_data(raw_record)
                    if llm_result.get("is_valid", True):
                        logger.info(f"LLM Quality Score: {llm_result.get('data_quality_score', 1.0):.2f}")
                    else:
                        logger.warning(f"LLM flagged data quality: {llm_result.get('reason', 'Unknown issue')} - but allowing through")
                except Exception as e:
                    logger.warning(f"LLM validation failed, proceeding with rule-based validation: {e}")
            
            return True, "Valid"
            
        except Exception as e:
            logger.error(f"Validation error for {raw_record}: {e}")
            return False, f"Validation error: {str(e)}"
    
    def _llm_validate_data(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM for intelligent data validation and preprocessing"""
        try:
            if not self.llm_enabled:
                return {"is_valid": True, "reason": "LLM not available", "suggestions": []}
            
            prompt = f"""You are an expert data quality analyst for agricultural sensor data. Analyze this raw sensor reading and determine if it's valid:

Raw Data: {json.dumps(raw_record, indent=2)}

Sensor Type: {raw_record.get('sensor', 'unknown')}
Value: {raw_record.get('value', 'N/A')} {raw_record.get('unit', '')}
Timestamp: {raw_record.get('timestamp', 'N/A')}

Please analyze and respond with JSON format:
{{
    "is_valid": true/false,
    "reason": "brief explanation",
    "confidence": 0.0-1.0,
    "suggestions": ["suggestion1", "suggestion2"],
    "data_quality_score": 0.0-1.0
}}

Consider:
- Realistic agricultural sensor ranges
- Temporal consistency
- Unit compatibility
- Data quality indicators
- Potential sensor malfunctions

Respond with valid JSON only:"""

            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Clean up response text to ensure valid JSON
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback to basic validation if JSON parsing fails
                logger.warning("LLM response not valid JSON, using fallback validation")
                return {
                    "is_valid": True,
                    "reason": "LLM JSON parsing failed, using fallback",
                    "confidence": 0.5,
                    "suggestions": [],
                    "data_quality_score": 0.8
                }
            
            logger.info(f"LLM Validation: {result.get('is_valid', True)} - {result.get('reason', 'No reason')}")
            return result
            
        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            return {"is_valid": True, "reason": f"LLM error: {str(e)}", "suggestions": []}
    
    def _writer_loop(self):
        """Background writer thread that batches inserts to reduce SQLite locks"""
        buffer = []
        while not self._stop_event.is_set() or not self.insert_queue.empty():
            try:
                item = None
                try:
                    # Get next item with timeout (so we can flush periodically)
                    item = self.insert_queue.get(timeout=self.flush_interval)
                    buffer.append(item)
                except queue.Empty:
                    pass

                # Flush if enough items or interval passed
                if len(buffer) >= self.batch_size or (buffer and self.insert_queue.empty()):
                    self._flush_batch(buffer)
                    buffer = []
            except Exception as e:
                logger.exception("Writer loop error: %s", e)
        # Flush remaining
        if buffer:
            self._flush_batch(buffer)

    def _flush_batch(self, records):
        """Flush a batch of records to the database"""
        if not records:
            return
        try:
            with self.db_manager.get_connection() as conn:
                cur = conn.cursor()
                cur.execute("BEGIN")
                cur.executemany(
                    "INSERT INTO sensor_data (timestamp, sensor_type, value, unit, source, raw_json) VALUES (?, ?, ?, ?, ?, ?)", 
                    [(r['timestamp'], r['sensor_type'], r['value'], r.get('unit'), r.get('source'), r.get('raw_json')) for r in records]
                )
                conn.commit()
            logger.info("Flushed %d records to sensor_data", len(records))
        except Exception as e:
            logger.exception("Failed to flush batch: %s", e)

    def stop(self):
        """Stop the batch writer and flush remaining data"""
        self._stop_event.set()
        self._writer_thread.join(timeout=10)
    
    def _convert_to_celsius(self, value: float, unit: str) -> float:
        """Convert temperature to Celsius for validation"""
        if unit.upper() in ['C', 'CELSIUS']:
            return value
        elif unit.upper() in ['F', 'FAHRENHEIT']:
            return (value - 32) * 5/9
        elif unit.upper() in ['K', 'KELVIN']:
            return value - 273.15
        else:
            # Assume Celsius if unit is unknown
            return value
    
    def normalize_data(self, raw_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize sensor data to standard format
        
        Args:
            raw_record: Raw sensor data dictionary
            
        Returns:
            Normalized sensor data dictionary
        """
        try:
            sensor_type = raw_record.get('sensor', '')
            value = raw_record.get('value')
            unit = raw_record.get('unit', '')
            timestamp_str = raw_record.get('timestamp', '')
            
            # Normalize timestamp to UTC ISO format
            normalized_timestamp = self._to_utc_iso(timestamp_str)
            
            # Start with base normalized record
            normalized = {
                "sensor": sensor_type,
                "value": value,
                "unit": unit,
                "timestamp": normalized_timestamp
            }
            
            # Handle None values
            if value is None:
                logger.warning(f"Null value for {sensor_type}, skipping normalization")
                return normalized
            
            # Convert temperature to Celsius
            if sensor_type == "temperature":
                normalized["value"] = self._convert_to_celsius(value, unit)
                normalized["unit"] = "C"
            
            # Standardize units for other sensors
            elif sensor_type == "humidity":
                normalized["unit"] = "%"
            
            elif sensor_type == "soil_moisture":
                normalized["unit"] = "%"
            
            elif sensor_type == "pest_count":
                normalized["unit"] = "count"
            
            elif sensor_type == "soil_ph":
                normalized["unit"] = "pH"
            
            elif sensor_type == "pressure":
                # Convert to hPa if needed
                if unit.upper() in ['PA', 'PASCAL']:
                    normalized["value"] = value / 100
                    normalized["unit"] = "hPa"
                elif unit.upper() in ['BAR']:
                    normalized["value"] = value * 1000
                    normalized["unit"] = "hPa"
                else:
                    normalized["unit"] = "hPa"
            
            elif sensor_type == "light":
                normalized["unit"] = "lux"
            
            elif sensor_type == "co2_level" or sensor_type == "co2":
                normalized["unit"] = "ppm"
            
            elif sensor_type == "wind_speed":
                # Convert to m/s if needed
                if unit.upper() in ['KM/H', 'KMH']:
                    normalized["value"] = value / 3.6
                    normalized["unit"] = "m/s"
                elif unit.upper() in ['MPH']:
                    normalized["value"] = value * 0.44704
                    normalized["unit"] = "m/s"
                else:
                    normalized["unit"] = "m/s"
            
            elif sensor_type == "rainfall":
                normalized["unit"] = "mm"
            
            elif sensor_type == "plant_height":
                # Convert to cm if needed
                if unit.upper() in ['INCHES', 'IN']:
                    normalized["value"] = value * 2.54
                    normalized["unit"] = "cm"
                elif unit.upper() in ['M', 'METERS']:
                    normalized["value"] = value * 100
                    normalized["unit"] = "cm"
                else:
                    normalized["unit"] = "cm"
            
            elif sensor_type == "fruit_size":
                # Convert to cm if needed
                if unit.upper() in ['INCHES', 'IN']:
                    normalized["value"] = value * 2.54
                    normalized["unit"] = "cm"
                else:
                    normalized["unit"] = "cm"
            
            elif sensor_type == "leaf_wetness":
                normalized["unit"] = "%"
            
            elif sensor_type in ["nitrogen_level", "phosphorus_level", "potassium_level"]:
                normalized["unit"] = "ppm"
            
            elif sensor_type == "nutrient_uptake":
                normalized["unit"] = "mg/L"
            
            elif sensor_type == "water_usage":
                # Convert to liters if needed
                if unit.upper() in ['GALLONS', 'GAL']:
                    normalized["value"] = value * 3.78541
                    normalized["unit"] = "L"
                else:
                    normalized["unit"] = "L"
            
            elif sensor_type == "water_efficiency":
                normalized["unit"] = "%"
            
            elif sensor_type == "yield_prediction":
                # Convert to kg if needed
                if unit.upper() in ['LBS', 'POUNDS']:
                    normalized["value"] = value * 0.453592
                    normalized["unit"] = "kg"
                else:
                    normalized["unit"] = "kg"
            
            elif sensor_type == "yield_efficiency":
                normalized["unit"] = "%"
            
            elif sensor_type in ["tomato_price", "lettuce_price", "pepper_price", "cost_per_kg"]:
                normalized["unit"] = "$/kg"
            
            elif sensor_type in ["demand_level", "supply_level", "profit_margin"]:
                normalized["unit"] = "%"
            
            elif sensor_type == "motion":
                normalized["unit"] = "count"
            
            elif sensor_type == "fertilizer_usage":
                normalized["unit"] = "kg"
            
            elif sensor_type == "energy_usage":
                # Convert to kWh if needed
                if unit.upper() in ['W', 'WATTS']:
                    normalized["value"] = value / 1000
                    normalized["unit"] = "kWh"
                else:
                    normalized["unit"] = "kWh"
            
            elif sensor_type == "disease_risk":
                normalized["unit"] = "%"
            
            elif sensor_type == "test_temperature":
                normalized["value"] = self._convert_to_celsius(value, unit)
                normalized["unit"] = "C"
            
            # Round numerical values to 2 decimal places
            if isinstance(normalized["value"], (int, float)):
                normalized["value"] = round(float(normalized["value"]), 2)
            
            # Ensure timestamp is properly formatted
            if normalized["timestamp"]:
                try:
                    # Parse and reformat timestamp
                    timestamp = datetime.fromisoformat(normalized["timestamp"].replace('Z', '+00:00'))
                    normalized["timestamp"] = timestamp.isoformat()
                except ValueError:
                    # If timestamp is invalid, use current time
                    normalized["timestamp"] = datetime.now().isoformat()
            else:
                normalized["timestamp"] = datetime.now().isoformat()
            
            return normalized
            
        except Exception as e:
            logger.error(f"Normalization error for {raw_record}: {e}")
            return raw_record  # Return original if normalization fails
    
    def store_data(self, normalized_record: Dict[str, Any], quality_score: float = 1.0, is_valid: bool = True) -> bool:
        """
        Store normalized data using batch writer queue
        
        Args:
            normalized_record: Normalized sensor data
            quality_score: Quality score (0.0 to 1.0)
            is_valid: Whether the data is valid
            
        Returns:
            True if queued successfully, False otherwise
        """
        try:
            # Add metadata to the record
            record_with_metadata = {
                'timestamp': normalized_record["timestamp"],
                'sensor_type': normalized_record["sensor"],
                'value': normalized_record["value"],
                'unit': normalized_record.get("unit"),
                'source': 'pipeline',
                'raw_json': json.dumps(normalized_record)
            }
            
            # Queue for batch insert
            self.insert_queue.put(record_with_metadata)
            
            logger.info(f"QUEUED: {normalized_record['sensor']} = {normalized_record['value']} {normalized_record['unit']}")
            return True
            
        except Exception as e:
            logger.error(f"Queue error for {normalized_record}: {e}")
            return False
    
    def process_and_store(self, raw_record: Dict[str, Any]) -> bool:
        """
        Complete pipeline: validate → normalize → store
        
        Args:
            raw_record: Raw sensor data dictionary
            
        Returns:
            True if processed successfully, False otherwise
        """
        try:
            sensor_type = raw_record.get('sensor', 'unknown')
            logger.info(f"Processing raw data: {sensor_type} = {raw_record.get('value')} {raw_record.get('unit')}")
            
            # Step 1: Validate data
            is_valid, error_message = self.validate_data(raw_record)
            
            if not is_valid:
                logger.warning(f"Validation failed for {sensor_type}: {error_message}")
                self.rejected_count += 1
                return False
            
            logger.info(f"Validation passed for {sensor_type}")
            
            # Step 2: Normalize data
            normalized_record = self.normalize_data(raw_record)
            logger.info(f"Normalized {sensor_type}: {normalized_record['value']} {normalized_record['unit']}")
            self.normalized_count += 1
            
            # Step 3: Store data
            quality_score = raw_record.get('quality_score', 1.0)
            is_valid_flag = raw_record.get('is_valid', True)
            
            success = self.store_data(normalized_record, quality_score, is_valid_flag)
            
            if success:
                self.processed_count += 1
                logger.info(f"Stored {sensor_type} successfully")
                return True
            else:
                logger.error(f"Failed to store {sensor_type}")
                return False
                
        except Exception as e:
            logger.error(f"Pipeline error for {raw_record}: {e}")
            return False
    
    def get_pipeline_stats(self) -> Dict[str, int]:
        """Get pipeline processing statistics using thread-safe database access"""
        try:
            # Get actual database counts using DatabaseManager
            db_count_result = self.db_manager.execute_with_retry('SELECT COUNT(*) FROM sensor_data')
            db_count = db_count_result[0][0] if db_count_result else 0
            
            # Get sensor type breakdown
            sensor_breakdown_result = self.db_manager.execute_with_retry(
                'SELECT sensor_type, COUNT(*) FROM sensor_data GROUP BY sensor_type ORDER BY COUNT(*) DESC'
            )
            sensor_breakdown = sensor_breakdown_result if sensor_breakdown_result else []
            
            logger.info(f"DATABASE STATUS: {db_count} total records in sensor_data table")
            logger.info(f"SENSOR BREAKDOWN: {sensor_breakdown}")
            
            return {
                "processed": self.processed_count,
                "rejected": self.rejected_count,
                "normalized": self.normalized_count,
                "database_count": db_count,
                "sensor_breakdown": sensor_breakdown,
                "success_rate": (self.processed_count / (self.processed_count + self.rejected_count) * 100) if (self.processed_count + self.rejected_count) > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting pipeline stats: {e}")
            return {
                "processed": self.processed_count,
                "rejected": self.rejected_count,
                "normalized": self.normalized_count,
                "success_rate": 0
            }
    
    def process_raw_data_batch(self, raw_data_list: list) -> Dict[str, int]:
        """
        Process a batch of raw sensor data
        
        Args:
            raw_data_list: List of raw sensor data dictionaries
            
        Returns:
            Processing statistics
        """
        logger.info(f"Processing batch of {len(raw_data_list)} raw records")
        
        for raw_record in raw_data_list:
            self.process_and_store(raw_record)
        
        stats = self.get_pipeline_stats()
        logger.info(f"Batch processing complete: {stats}")
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Initialize pipeline
    pipeline = DataPipeline()
    
    # Test with sample raw data
    test_data = [
        {
            "sensor": "temperature",
            "value": 75.5,
            "unit": "F",
            "timestamp": "2025-10-05T10:20:00Z",
            "quality": "good"
        },
        {
            "sensor": "humidity",
            "value": 65.2,
            "unit": "%",
            "timestamp": "2025-10-05T10:20:01Z",
            "quality": "good"
        },
        {
            "sensor": "temperature",
            "value": -999,
            "unit": "C",
            "timestamp": "2025-10-05T10:20:02Z",
            "quality": "bad"
        }
    ]
    
    # Process test data
    pipeline.process_raw_data_batch(test_data)
    
    # Print statistics
    stats = pipeline.get_pipeline_stats()
    print(f"\nPipeline Statistics:")
    print(f"Processed: {stats['processed']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Success Rate: {stats['success_rate']:.1f}%")
