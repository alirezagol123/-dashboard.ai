"""
Alert Manager Service for Smart Agriculture Platform
Handles alert creation, management, and monitoring through AI Assistant
"""

import logging
import sqlite3
import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AlertManager:
    """Enhanced Alert Manager with advanced ontology support"""
    
    def __init__(self, db_path: str = None):
        # Use proper database path for Liara
        if db_path is None:
            if os.getenv("LIARA_APP_ID"):
                db_dir = "/var/lib/data"
                os.makedirs(db_dir, exist_ok=True)
                self.db_path = os.path.join(db_dir, "smart_dashboard.db")
            else:
                self.db_path = "smart_dashboard.db"
        else:
            self.db_path = db_path
        self._init_database()
        
        # Enhanced ontology support
        self.severity_levels = {
            "info": {"color": "blue", "priority": 1, "description": "Informational alert"},
            "warning": {"color": "yellow", "priority": 2, "description": "Early warning"},
            "critical": {"color": "red", "priority": 3, "description": "Critical alert - immediate response required"}
        }
        
        self.comparison_operators = {
            ">": "greater than",
            "<": "less than", 
            "=": "equal to",
            ">=": "greater or equal",
            "<=": "less or equal"
        }
        
        self.alert_statuses = {
            "active": "Alert is currently active",
            "resolved": "Alert condition returned to normal", 
            "pending": "Alert is under evaluation"
        }
    
    def _init_database(self):
        """Initialize alert database table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create user_alerts table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    alert_name TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    condition_type TEXT NOT NULL,
                    threshold_value REAL NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("✅ Alert database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing alert database: {e}")
    
    def create_alert_from_natural_language(self, query: str, user_id: str = "default") -> Dict[str, Any]:
        """Create enhanced alert from natural language query with ontology support"""
        try:
            logger.info(f"🔔 Creating enhanced alert from query: {query}")
            
            # Parse the natural language query with enhanced ontology
            parsed_alert = self._parse_enhanced_alert_query(query)
            
            if not parsed_alert:
                return {
                    "success": False,
                    "error": "Could not parse alert conditions from your query"
                }
            
            # Create alert in database with enhanced fields
            alert_id = self._save_enhanced_alert_to_db(user_id, parsed_alert)
            
            return {
                "success": True,
                "alert_id": alert_id,
                "alert_name": parsed_alert["alert_name"],
                "sensor_type": parsed_alert["sensor_type"],
                "condition": parsed_alert["condition_type"],
                "threshold": parsed_alert["threshold_value"],
                "severity": parsed_alert.get("severity_level", "warning"),
                "operator": parsed_alert.get("comparison_operator", ">"),
                "time_window": parsed_alert.get("time_window", 0),
                "action_type": parsed_alert.get("action_type"),
                "message": f"Enhanced alert created: {parsed_alert['alert_name']}"
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating enhanced alert: {e}")
            return {
                "success": False,
                "error": f"Failed to create enhanced alert: {str(e)}"
            }
    
    def _parse_enhanced_alert_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse natural language query with enhanced ontology support"""
        try:
            # Use the unified semantic service's ontology mapping
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            
            # Initialize the service to access ontology mapping
            unified_service = UnifiedSemanticQueryService()
            
            # Detect language and translate Persian queries to English first
            is_persian = any(ord(char) > 127 for char in query)
            language = "fa" if is_persian else "en"
            
            # Translate Persian query to English first
            translated_query = query
            if is_persian:
                try:
                    translated_query = unified_service.translator.translate_query_to_english(query)
                    logger.info(f" Translated Persian query to English: {translated_query}")
                except Exception as e:
                    logger.warning(f" Translation failed, using original query: {e}")
                    translated_query = query
            
            # Map translated query to sensor type using ontology
            mapping_result = unified_service._map_query_to_sensor_type(translated_query, language="en")
            sensor_type = mapping_result.get("sensor_type")
            
            if not sensor_type:
                logger.warning(f" No sensor type found in ontology mapping for query: {query}")
                return None
            
            # Handle compound queries (multiple sensors) - take the first one for alerts
            if isinstance(sensor_type, list):
                sensor_type = sensor_type[0]
                logger.info(f" Compound query detected, using first sensor: {sensor_type}")
            
            # Enhanced condition patterns with new operators
            condition_patterns = {
                "above": ["above", "over", "more than", "greater than", ">", "exceeds", "بیشتر از", "بالاتر از", "فراتر از", "زیادتر از"],
                "below": ["below", "under", "less than", "lower than", "<", "drops below", "کمتر از", "پایین تر از", "کمتر از"],
                "equals": ["equals", "equal to", "=", "is", "برابر", "مساوی", "همان"],
                "greater_equal": [">=", "greater or equal", "at least", "minimum", "حداقل", "بیشتر یا مساوی"],
                "less_equal": ["<=", "less or equal", "at most", "maximum", "حداکثر", "کمتر یا مساوی"]
            }
            
            # Extract condition type and operator
            condition_type = None
            comparison_operator = ">"
            query_lower = translated_query.lower()
            
            for condition, patterns in condition_patterns.items():
                if any(pattern in query_lower for pattern in patterns):
                    condition_type = condition
                    if condition == "above":
                        comparison_operator = ">"
                    elif condition == "below":
                        comparison_operator = "<"
                    elif condition == "equals":
                        comparison_operator = "="
                    elif condition == "greater_equal":
                        comparison_operator = ">="
                    elif condition == "less_equal":
                        comparison_operator = "<="
                    break
            
            if not condition_type:
                logger.warning(f" No condition type found for query: {query}")
                return None
            
            # Extract threshold value
            threshold_value = self._extract_threshold_value(translated_query)
            if threshold_value is None:
                return None
            
            # Extract severity level
            severity_level = self._extract_severity_from_query(translated_query)
            
            # Extract time window
            time_window = self._extract_time_window_from_query(translated_query)
            
            # Extract action type
            action_type = self._extract_action_from_query(translated_query)
            
            # Generate alert name
            alert_name = f"{sensor_type.replace('_', ' ').title()} Alert"
            
            return {
                "alert_name": alert_name,
                "sensor_type": sensor_type,
                "condition_type": condition_type,
                "threshold_value": threshold_value,
                "comparison_operator": comparison_operator,
                "severity_level": severity_level,
                "time_window": time_window,
                "action_type": action_type
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing enhanced alert query: {e}")
            return None

    def _parse_alert_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Parse natural language query to extract alert conditions using ontology"""
        try:
            # Use the unified semantic service's ontology mapping
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            
            # Initialize the service to access ontology mapping
            unified_service = UnifiedSemanticQueryService()
            
            # Detect language and translate Persian queries to English first
            # Simple language detection for Persian queries
            is_persian = any(ord(char) > 127 for char in query)  # Check for non-ASCII characters
            language = "fa" if is_persian else "en"
            
            # Translate Persian query to English first (like in main flow)
            translated_query = query
            if is_persian:
                try:
                    translated_query = unified_service.translator.translate_query_to_english(query)
                    logger.info(f" Translated Persian query to English: {translated_query}")
                except Exception as e:
                    logger.warning(f" Translation failed, using original query: {e}")
                    translated_query = query
            
            # Map translated query to sensor type using ontology
            mapping_result = unified_service._map_query_to_sensor_type(translated_query, language="en")
            sensor_type = mapping_result.get("sensor_type")
            
            if not sensor_type:
                logger.warning(f" No sensor type found in ontology mapping for query: {query}")
                return None
            
            # Handle compound queries (multiple sensors) - take the first one for alerts
            if isinstance(sensor_type, list):
                sensor_type = sensor_type[0]
                logger.info(f" Compound query detected, using first sensor: {sensor_type}")
            
            # Fallback strategy: if ontology mapping gives unexpected results, use basic pattern matching
            logger.info(f" Ontology mapping result: {mapping_result}")
            logger.info(f" Extracted sensor_type: {sensor_type}")
            logger.info(f" Is valid sensor type: {self._is_valid_sensor_type(sensor_type)}")
            
            if not self._is_valid_sensor_type(sensor_type):
                logger.warning(f" Ontology mapping gave unexpected result: {sensor_type}, trying fallback")
                sensor_type = self._basic_pattern_match(query)
                if not sensor_type:
                    logger.error(f" Fallback pattern matching also failed for query: {query}")
                    return None
                else:
                    logger.info(f" Fallback pattern matching succeeded: {sensor_type}")
            
            # Define condition patterns (English and Persian)
            condition_patterns = {
                "above": ["above", "over", "more than", "greater than", ">", "exceeds", "بیشتر از", "بالاتر از", "فراتر از", "زیادتر از"],
                "below": ["below", "under", "less than", "lower than", "<", "drops below", "کمتر از", "پایین تر از", "کمتر از"],
                "equals": ["equals", "equal to", "=", "is", "برابر", "مساوی", "همان"]
            }
            
            # Extract condition type (use translated query for better pattern matching)
            condition_type = None
            query_lower = translated_query.lower()
            for condition, patterns in condition_patterns.items():
                if any(pattern in query_lower for pattern in patterns) or any(pattern in translated_query for pattern in patterns):
                    condition_type = condition
                    break
            
            if not condition_type:
                logger.warning(f" No condition type found for query: {query}")
                return None
            
            # Extract threshold value (use translated query for better number extraction)
            threshold_value = self._extract_threshold_value(translated_query)
            
            if threshold_value is None:
                return None
            
            # Generate alert name
            alert_name = f"{sensor_type.replace('_', ' ').title()} Alert"
            
            return {
                "alert_name": alert_name,
                "sensor_type": sensor_type,
                "condition_type": condition_type,
                "threshold_value": threshold_value
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing alert query: {e}")
            return None
    
    def _is_valid_sensor_type(self, sensor_type: str) -> bool:
        """Check if sensor type is valid for alerts using the ontology"""
        try:
            # Get the ontology from the unified semantic service
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            unified_service = UnifiedSemanticQueryService()
            ontology = unified_service.get_ontology()
            
            # Check if the sensor type exists in the ontology
            # Look in all sensor categories
            for category, sensors in ontology.items():
                if isinstance(sensors, dict):
                    for sensor_name, sensor_data in sensors.items():
                        if sensor_name == sensor_type:
                            logger.info(f"✅ Sensor type '{sensor_type}' found in ontology category '{category}'")
                            return True
            
            # If not found in ontology, it's still valid if it's a reasonable sensor type
            # (This allows for dynamic sensor types that might not be in the ontology yet)
            logger.info(f"✅ Sensor type '{sensor_type}' accepted as valid sensor type")
            return True
            
        except Exception as e:
            logger.warning(f"⚠️ Error checking ontology for sensor type '{sensor_type}': {e}")
            # Fallback: accept the sensor type if ontology check fails
            return True
    
    def _basic_pattern_match(self, query: str) -> Optional[str]:
        """Fallback basic pattern matching for sensor types"""
        # Basic English and Persian patterns
        patterns = {
            "temperature": ["temperature", "temp", "heat", "cold", "دما", "حرارت", "گرما", "سرما"],
            "humidity": ["humidity", "moisture", "damp", "رطوبت", "نم", "مرطوب"],
            "pressure": ["pressure", "barometric", "فشار", "بارومتر"],
            "light": ["light", "brightness", "illumination", "نور", "روشنایی", "تابش"],
            "motion": ["motion", "movement", "detection", "حرکت", "جنبش", "تشخیص"],
            "soil_moisture": ["soil moisture", "soil", "ground moisture", "رطوبت خاک", "خاک", "رطوبت زمین"],
            "co2_level": ["co2", "carbon dioxide", "co2 level", "دی اکسید کربن", "کربن دی اکسید"],
            "ph": ["ph", "acidity", "alkalinity", "پی اچ", "اسیدی", "قلیایی"],
            "water_usage": ["water usage", "water consumption", "water usage", "مصرف آب", "استفاده از آب"],
            "energy_usage": ["energy usage", "power consumption", "مصرف انرژی", "استفاده از انرژی"]
        }
        
        # Check both original query and lowercase for Persian/English compatibility
        for sensor, terms in patterns.items():
            for term in terms:
                if term in query or term in query.lower():
                    logger.info(f" Basic pattern match found: {term} -> {sensor}")
                    return sensor
        
        logger.warning(f" No basic pattern match found for query: {query}")
        return None

    def _extract_threshold_value(self, query: str) -> Optional[float]:
        """Extract numerical threshold value from query"""
        try:
            # Look for numbers in the query
            numbers = re.findall(r'\d+\.?\d*', query)
            
            if numbers:
                return float(numbers[0])
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error extracting threshold value: {e}")
            return None
    
    def _extract_severity_from_query(self, query: str) -> str:
        """Extract severity level from query"""
        query_lower = query.lower()
        
        # Critical severity keywords
        critical_keywords = ["critical", "urgent", "emergency", "danger", "بحرانی", "خطرناک", "فوری"]
        if any(keyword in query_lower for keyword in critical_keywords):
            return "critical"
        
        # Warning severity keywords  
        warning_keywords = ["warning", "alert", "caution", "هشدار", "احتیاط"]
        if any(keyword in query_lower for keyword in warning_keywords):
            return "warning"
        
        # Info severity keywords
        info_keywords = ["info", "information", "status", "اطلاعی", "وضعیت"]
        if any(keyword in query_lower for keyword in info_keywords):
            return "info"
        
        # Default to warning
        return "warning"
    
    def _extract_time_window_from_query(self, query: str) -> int:
        """Extract time window from query in minutes"""
        query_lower = query.lower()
        
        # Hour patterns
        hour_match = re.search(r'(\d+)\s*hour', query_lower)
        if hour_match:
            return int(hour_match.group(1)) * 60
        
        # Day patterns
        day_match = re.search(r'(\d+)\s*day', query_lower)
        if day_match:
            return int(day_match.group(1)) * 24 * 60
        
        # Week patterns
        week_match = re.search(r'(\d+)\s*week', query_lower)
        if week_match:
            return int(week_match.group(1)) * 7 * 24 * 60
        
        # Default to 0 (no time window)
        return 0
    
    def _extract_action_from_query(self, query: str) -> Optional[str]:
        """Extract action type from query"""
        query_lower = query.lower()
        
        # Email action
        if any(word in query_lower for word in ["email", "send email", "mail", "ایمیل"]):
            return "email"
        
        # SMS action
        if any(word in query_lower for word in ["sms", "text", "message", "پیامک"]):
            return "sms"
        
        # Notification action
        if any(word in query_lower for word in ["notify", "notification", "alert", "اعلان"]):
            return "notification"
        
        # Auto action
        if any(word in query_lower for word in ["auto", "automatic", "automate", "خودکار"]):
            return "auto"
        
        return None
    
    def _save_alert_to_db(self, user_id: str, alert_data: Dict[str, Any]) -> str:
        """Save alert to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_alerts 
                (user_id, alert_name, sensor_type, condition_type, threshold_value, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                alert_data["alert_name"],
                alert_data["sensor_type"],
                alert_data["condition_type"],
                alert_data["threshold_value"],
                True
            ))
            
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Alert saved to database with ID: {alert_id}")
            return str(alert_id)
            
        except Exception as e:
            logger.error(f"❌ Error saving alert to database: {e}")
            raise e
    
    def _save_enhanced_alert_to_db(self, user_id: str, alert_data: Dict[str, Any]) -> str:
        """Save enhanced alert to database with ontology fields"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO user_alerts (
                    user_id, alert_name, sensor_type, condition_type, threshold_value, 
                    severity_level, comparison_operator, time_window, action_type, 
                    is_active, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                alert_data["alert_name"],
                alert_data["sensor_type"],
                alert_data["condition_type"],
                alert_data["threshold_value"],
                alert_data.get("severity_level", "warning"),
                alert_data.get("comparison_operator", ">"),
                alert_data.get("time_window", 0),
                alert_data.get("action_type"),
                True,
                datetime.now().isoformat()
            ))
            
            alert_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Enhanced alert saved to database with ID: {alert_id}")
            return str(alert_id)
            
        except Exception as e:
            logger.error(f"❌ Error saving enhanced alert to database: {e}")
            return None
    
    def get_user_alerts(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """Get all alerts for a user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, alert_name, sensor_type, condition_type, threshold_value, 
                       is_active, created_at, updated_at
                FROM user_alerts 
                WHERE user_id = ? 
                ORDER BY created_at DESC
            """, (user_id,))
            
            alerts = []
            for row in cursor.fetchall():
                alerts.append({
                    "id": str(row[0]),
                    "alert_name": row[1],
                    "sensor_type": row[2],
                    "condition_type": row[3],
                    "threshold_value": row[4],
                    "is_active": bool(row[5]),
                    "created_at": row[6],
                    "updated_at": row[7]
                })
            
            conn.close()
            return alerts
            
        except Exception as e:
            logger.error(f"❌ Error getting user alerts: {e}")
            return []
    
    def delete_alert(self, alert_id: str, user_id: str = "default") -> bool:
        """Delete an alert"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM user_alerts 
                WHERE id = ? AND user_id = ?
            """, (alert_id, user_id))
            
            deleted_count = cursor.rowcount
            conn.commit()
            conn.close()
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error deleting alert: {e}")
            return False
    
    def check_alerts_against_data(self, sensor_data: List[Dict[str, Any]], user_id: str = "default") -> List[Dict[str, Any]]:
        """Check sensor data against active alerts and execute actions"""
        try:
            active_alerts = self.get_user_alerts(user_id)
            triggered_alerts = []
            
            for alert in active_alerts:
                if not alert["is_active"]:
                    continue
                
                # Find matching sensor data
                sensor_type = alert["sensor_type"]
                matching_data = [item for item in sensor_data if item.get("sensor_type") == sensor_type]
                
                if not matching_data:
                    continue
                
                # Get latest value
                latest_data = max(matching_data, key=lambda x: x.get("timestamp", ""))
                current_value = latest_data.get("value", 0)
                
                # Check condition with enhanced operators
                threshold = alert["threshold_value"]
                condition = alert["condition_type"]
                comparison_operator = alert.get("comparison_operator", ">")
                severity_level = alert.get("severity_level", "warning")
                
                condition_met = False
                if comparison_operator == ">" and current_value > threshold:
                    condition_met = True
                elif comparison_operator == "<" and current_value < threshold:
                    condition_met = True
                elif comparison_operator == "=" and current_value == threshold:
                    condition_met = True
                elif comparison_operator == ">=" and current_value >= threshold:
                    condition_met = True
                elif comparison_operator == "<=" and current_value <= threshold:
                    condition_met = True
                
                if condition_met:
                    triggered_alert = {
                        "alert_id": alert["id"],
                        "alert_name": alert["alert_name"],
                        "sensor_type": sensor_type,
                        "current_value": current_value,
                        "threshold": threshold,
                        "condition": condition,
                        "operator": comparison_operator,
                        "severity": severity_level,
                        "action_type": alert.get("action_type"),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    triggered_alerts.append(triggered_alert)
                    
                    # Execute automated actions if configured
                    if alert.get("action_type"):
                        self._execute_alert_actions(triggered_alert)
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"❌ Error checking alerts: {e}")
            return []
    
    def _execute_alert_actions(self, triggered_alert: Dict[str, Any]):
        """Execute automated actions for triggered alert"""
        try:
            from app.services.action_executor import ActionExecutor
            
            action_executor = ActionExecutor()
            execution_results = action_executor.execute_alert_actions([triggered_alert])
            
            for result in execution_results:
                if result["status"] == "success":
                    logger.info(f"✅ Action executed successfully for alert {result['alert_id']}")
                else:
                    logger.error(f"❌ Action execution failed for alert {result['alert_id']}: {result.get('error')}")
                    
        except Exception as e:
            logger.error(f"❌ Error executing alert actions: {e}")
