import asyncio
import sqlite3
import json
import time
from datetime import datetime
from data_pipeline import DataPipeline
from raw_sensor_generator import RawSensorDataGenerator

class IntegratedSensorSystem:
    """Integrated system that generates raw data and processes it through the pipeline"""
    
    def __init__(self, db_file="smart_dashboard.db"):
        self.db_file = db_file
        self.pipeline = DataPipeline(db_file)
        self.generator = RawSensorDataGenerator(db_file)
        self.running = False
        
        print("Integrated Sensor System initialized")
        print("Raw data -> Validation -> Normalization -> Clean database")
    
    async def process_raw_data_from_database(self):
        """Process raw sensor data from database through pipeline"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Get unprocessed raw data
            cursor.execute('''
                SELECT id, raw_data FROM raw_sensor_data 
                WHERE processed = 0 OR processed IS NULL
                ORDER BY timestamp DESC
                LIMIT 50
            ''')
            
            raw_records = cursor.fetchall()
            
            if not raw_records:
                return 0
            
            processed_count = 0
            
            for record_id, raw_data_json in raw_records:
                try:
                    # Parse raw data
                    raw_data = json.loads(raw_data_json)
                    
                    # Process through pipeline
                    success = self.pipeline.process_and_store(raw_data)
                    
                    if success:
                        # Mark as processed
                        cursor.execute('''
                            UPDATE raw_sensor_data 
                            SET processed = 1, processed_at = ?
                            WHERE id = ?
                        ''', (datetime.now().isoformat(), record_id))
                        
                        processed_count += 1
                        print(f"✅ Processed: {raw_data.get('sensor')} = {raw_data.get('value')} {raw_data.get('unit')}")
                    else:
                        print(f"❌ Failed to process: {raw_data.get('sensor')}")
                
                except Exception as e:
                    print(f"❌ Error processing record {record_id}: {e}")
            
            conn.commit()
            conn.close()
            
            return processed_count
            
        except Exception as e:
            print(f"Database processing error: {e}")
            return 0
    
    async def run_integrated_system(self):
        """Run the complete integrated system"""
        print("Starting Integrated Sensor System")
        print("=" * 60)
        print("Generating raw sensor data...")
        print("Processing through validation pipeline...")
        print("Storing clean data in database...")
        print("=" * 60)
        
        self.running = True
        cycle_count = 0
        
        try:
            while self.running:
                cycle_count += 1
                print(f"\nCycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
                
                # Step 1: Generate raw data (simulate sensor readings)
                print("Generating raw sensor data...")
                sensor_types = list(self.generator.sensor_configs.keys())
                
                for sensor_type in sensor_types:
                    # Generate raw sensor data
                    raw_data = self.generator.generate_raw_sensor_data(sensor_type)
                    
                    # Process directly through pipeline (no raw table needed)
                    success = self.pipeline.process_and_store(raw_data)
                    if success:
                        print(f"[OK] Processed {sensor_type}")
                    else:
                        print(f"[FAILED] Failed to process {sensor_type}")
                    
                    # Small delay between sensors
                    await asyncio.sleep(0.05)
                
                print(f"Generated and processed {len(sensor_types)} sensors")
                
                # Step 3: Show statistics
                stats = self.pipeline.get_pipeline_stats()
                print(f"Pipeline Stats: {stats['processed']} processed, {stats['rejected']} rejected")
                print(f"Success Rate: {stats['success_rate']:.1f}%")
                print(f"Database Count: {stats.get('database_count', 0)} total records in sensor_data table")
                if 'sensor_breakdown' in stats:
                    print(f"Sensor Breakdown: {stats['sensor_breakdown']}")
                
                # Wait before next cycle
                print("Waiting 15 seconds before next cycle...")
                await asyncio.sleep(15)
                
        except KeyboardInterrupt:
            print("\nStopping integrated sensor system...")
            self.running = False
        except Exception as e:
            print(f"System error: {e}")
            self.running = False
        finally:
            print("Integrated sensor system stopped")
            print(f"Data saved to: {self.db_file}")
            print("Check sensor_data table for clean, processed data")

    def get_system_status(self):
        """Get current system status"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Count raw data
            cursor.execute('SELECT COUNT(*) FROM raw_sensor_data')
            raw_count = cursor.fetchone()[0]
            
            # Count processed data
            cursor.execute('SELECT COUNT(*) FROM sensor_data')
            processed_count = cursor.fetchone()[0]
            
            # Count unprocessed raw data
            cursor.execute('SELECT COUNT(*) FROM raw_sensor_data WHERE processed = 0 OR processed IS NULL')
            unprocessed_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "raw_data_count": raw_count,
                "processed_data_count": processed_count,
                "unprocessed_count": unprocessed_count,
                "pipeline_stats": self.pipeline.get_pipeline_stats()
            }
            
        except Exception as e:
            print(f"❌ Status error: {e}")
            return {}

if __name__ == "__main__":
    # Initialize integrated system
    system = IntegratedSensorSystem()
    
    try:
        # Run the complete system
        asyncio.run(system.run_integrated_system())
    except KeyboardInterrupt:
        print("\n🛑 System stopped by user")
    finally:
        # Show final status
        status = system.get_system_status()
        print(f"\n📊 Final System Status:")
        print(f"   Raw data records: {status.get('raw_data_count', 0)}")
        print(f"   Processed records: {status.get('processed_data_count', 0)}")
        print(f"   Unprocessed records: {status.get('unprocessed_count', 0)}")
        print(f"   Pipeline success rate: {status.get('pipeline_stats', {}).get('success_rate', 0):.1f}%")
