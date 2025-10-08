import asyncio
import random
import math
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

class RawSensorDataGenerator:
    """Generates realistic RAW sensor data with noise, inconsistencies, and bad data"""
    
    def __init__(self, db_file="smart_dashboard.db"):
        self.db_file = db_file
        self.start_time = datetime.now()
        
        # Sensor configurations with realistic ranges - COMPREHENSIVE COVERAGE
        self.sensor_configs = {
            # Environmental Sensors
            "temperature": {"min": -10, "max": 50, "units": ["C", "F", "K"], "noise_level": 0.5},
            "humidity": {"min": 0, "max": 100, "units": ["%"], "noise_level": 2.0},
            "pressure": {"min": 900, "max": 1100, "units": ["hPa", "Pa", "bar"], "noise_level": 5.0},
            "light": {"min": 0, "max": 1000, "units": ["lux", "lumens"], "noise_level": 10.0},
            "co2_level": {"min": 300, "max": 1000, "units": ["ppm", "mg/m3"], "noise_level": 20.0},
            "co2": {"min": 300, "max": 1000, "units": ["ppm", "mg/m3"], "noise_level": 20.0},
            "wind_speed": {"min": 0, "max": 30, "units": ["m/s", "km/h", "mph"], "noise_level": 1.0},
            "rainfall": {"min": 0, "max": 50, "units": ["mm", "inches"], "noise_level": 0.5},
            
            # Soil Sensors
            "soil_moisture": {"min": 0, "max": 100, "units": ["%"], "noise_level": 3.0},
            "soil_ph": {"min": 4.0, "max": 9.0, "units": ["pH"], "noise_level": 0.2},
            "soil_temperature": {"min": 10, "max": 30, "units": ["C", "F"], "noise_level": 1.0},
            
            # Plant Growth Sensors
            "plant_height": {"min": 0, "max": 200, "units": ["cm", "inches", "m"], "noise_level": 2.0},
            "fruit_count": {"min": 0, "max": 50, "units": ["count"], "noise_level": 0.5},
            "fruit_size": {"min": 0, "max": 10, "units": ["cm", "inches"], "noise_level": 0.1},
            "leaf_count": {"min": 0, "max": 50, "units": ["count"], "noise_level": 1.0},
            "leaf_wetness": {"min": 0, "max": 100, "units": ["%"], "noise_level": 5.0},
            
            # Nutrient Sensors
            "nitrogen_level": {"min": 0, "max": 200, "units": ["ppm", "mg/kg"], "noise_level": 10.0},
            "phosphorus_level": {"min": 0, "max": 100, "units": ["ppm", "mg/kg"], "noise_level": 8.0},
            "potassium_level": {"min": 0, "max": 300, "units": ["ppm", "mg/kg"], "noise_level": 12.0},
            "nutrient_uptake": {"min": 0, "max": 100, "units": ["mg/L"], "noise_level": 5.0},
            
            # Pest & Disease Sensors
            "pest_count": {"min": 0, "max": 100, "units": ["count"], "noise_level": 1.0},
            "pest_detection": {"min": 0, "max": 1, "units": ["binary"], "noise_level": 0.1},
            "disease_risk": {"min": 0, "max": 100, "units": ["%"], "noise_level": 3.0},
            
            # Water Management
            "water_usage": {"min": 0, "max": 100, "units": ["L", "gallons"], "noise_level": 2.0},
            "water_efficiency": {"min": 0, "max": 100, "units": ["%"], "noise_level": 2.0},
            
            # Yield & Production
            "yield_prediction": {"min": 0, "max": 1000, "units": ["kg", "lbs"], "noise_level": 20.0},
            "yield_efficiency": {"min": 0, "max": 100, "units": ["%"], "noise_level": 3.0},
            
            # Market & Economics
            "tomato_price": {"min": 1.0, "max": 5.0, "units": ["$/kg"], "noise_level": 0.1},
            "lettuce_price": {"min": 0.5, "max": 3.0, "units": ["$/head"], "noise_level": 0.05},
            "pepper_price": {"min": 2.0, "max": 6.0, "units": ["$/kg"], "noise_level": 0.1},
            "cost_per_kg": {"min": 1.0, "max": 4.0, "units": ["$/kg"], "noise_level": 0.1},
            "demand_level": {"min": 0, "max": 100, "units": ["%"], "noise_level": 5.0},
            "supply_level": {"min": 0, "max": 100, "units": ["%"], "noise_level": 5.0},
            "profit_margin": {"min": 0, "max": 50, "units": ["%"], "noise_level": 2.0},
            
            # Additional Sensors
            "motion": {"min": 0, "max": 100, "units": ["count", "events"], "noise_level": 1.0},
            "fertilizer_usage": {"min": 0, "max": 10, "units": ["kg"], "noise_level": 0.5},
            "energy_usage": {"min": 0, "max": 500, "units": ["kWh", "W"], "noise_level": 5.0},
            "test_temperature": {"min": 15, "max": 35, "units": ["C", "F"], "noise_level": 0.5}
        }
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize database for raw sensor data"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create raw_sensor_data table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    raw_data TEXT NOT NULL,
                    quality_score REAL,
                    is_valid BOOLEAN,
                    processed BOOLEAN DEFAULT 0,
                    processed_at TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"[OK] Raw sensor database initialized: {self.db_file}")
        except Exception as e:
            print(f"[ERROR] Database initialization error: {e}")
    
    def _generate_timestamp_with_noise(self) -> str:
        """Generate timestamp with realistic sensor timing variations"""
        # Generate timestamp in the past with small variations
        base_time = datetime.now()
        
        # Add random timing variations (sensors don't read at exact intervals)
        time_offset = random.uniform(-2, 2)  # ±2 seconds variation
        
        # Always generate timestamp in the past (1-30 seconds ago)
        noisy_time = base_time - timedelta(seconds=random.uniform(1, 30)) + timedelta(seconds=time_offset)
        
        # Ensure it's still in the past
        if noisy_time > base_time:
            noisy_time = base_time - timedelta(seconds=random.uniform(1, 10))
        
        return noisy_time.isoformat()
    
    def _generate_noisy_value(self, sensor_type: str, base_value: float) -> float:
        """Add realistic sensor noise to values"""
        config = self.sensor_configs[sensor_type]
        noise_level = config["noise_level"]
        
        # Add Gaussian noise
        noise = random.gauss(0, noise_level)
        noisy_value = base_value + noise
        
        # Occasionally add extreme noise (sensor malfunction)
        if random.random() < 0.05:  # 5% chance of extreme noise
            extreme_noise = random.uniform(-50, 50)
            noisy_value += extreme_noise
        
        return round(noisy_value, 2)
    
    def _generate_bad_data(self, sensor_type: str) -> Dict[str, Any]:
        """Generate intentionally bad or inconsistent data"""
        bad_data_types = [
            "missing_value",
            "wrong_unit", 
            "out_of_range",
            "negative_value",
            "extreme_value",
            "wrong_type"
        ]
        
        bad_type = random.choice(bad_data_types)
        config = self.sensor_configs[sensor_type]
        
        if bad_type == "missing_value":
            return {
                "sensor": sensor_type,
                "value": None,
                "unit": random.choice(config["units"]),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "missing_value"
            }
        
        elif bad_type == "wrong_unit":
            wrong_units = ["Kelvin", "Fahrenheit", "Celsius", "Percent", "Unknown", "N/A"]
            return {
                "sensor": sensor_type,
                "value": random.uniform(config["min"], config["max"]),
                "unit": random.choice(wrong_units),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "wrong_unit"
            }
        
        elif bad_type == "out_of_range":
            # Generate values way outside normal range
            if random.random() < 0.5:
                value = random.uniform(config["max"] + 50, config["max"] + 200)
            else:
                value = random.uniform(config["min"] - 200, config["min"] - 50)
            
            return {
                "sensor": sensor_type,
                "value": value,
                "unit": random.choice(config["units"]),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "out_of_range"
            }
        
        elif bad_type == "negative_value":
            return {
                "sensor": sensor_type,
                "value": random.uniform(-100, -1),
                "unit": random.choice(config["units"]),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "negative_value"
            }
        
        elif bad_type == "extreme_value":
            extreme_values = [-999, 999, 9999, -9999, float('inf'), float('-inf')]
            return {
                "sensor": sensor_type,
                "value": random.choice(extreme_values),
                "unit": random.choice(config["units"]),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "extreme_value"
            }
        
        elif bad_type == "wrong_type":
            wrong_types = ["string", "boolean", "array", "object"]
            return {
                "sensor": sensor_type,
                "value": random.choice(wrong_types),
                "unit": random.choice(config["units"]),
                "timestamp": self._generate_timestamp_with_noise(),
                "quality": "bad",
                "error": "wrong_type"
            }
    
    def _generate_good_data(self, sensor_type: str) -> Dict[str, Any]:
        """Generate good quality sensor data with realistic patterns"""
        config = self.sensor_configs[sensor_type]
        
        # Generate base value with realistic patterns
        if sensor_type == "temperature":
            # Temperature follows daily cycle
            hour = datetime.now().hour
            base_temp = 20 + 10 * math.sin(math.pi * (hour - 6) / 12)
            value = self._generate_noisy_value(sensor_type, base_temp)
        
        elif sensor_type == "humidity":
            # Humidity inversely related to temperature
            hour = datetime.now().hour
            base_humidity = 60 - 20 * math.sin(math.pi * (hour - 6) / 12)
            value = self._generate_noisy_value(sensor_type, base_humidity)
        
        elif sensor_type == "soil_moisture":
            # Soil moisture decreases over time, occasional spikes
            if random.random() < 0.1:  # 10% chance of irrigation
                value = random.uniform(70, 90)
            else:
                value = random.uniform(20, 60)
            value = self._generate_noisy_value(sensor_type, value)
        
        elif sensor_type == "pest_count":
            # Pest count with occasional spikes
            if random.random() < 0.05:  # 5% chance of pest outbreak
                value = random.uniform(20, 50)
            else:
                value = random.uniform(0, 5)
            value = self._generate_noisy_value(sensor_type, value)
        
        else:
            # Default random value within range
            base_value = random.uniform(config["min"], config["max"])
            value = self._generate_noisy_value(sensor_type, base_value)
        
        # Ensure value is within reasonable bounds
        value = max(config["min"] - 10, min(config["max"] + 10, value))
        
        return {
            "sensor": sensor_type,
            "value": value,
            "unit": random.choice(config["units"]),
            "timestamp": self._generate_timestamp_with_noise(),
            "quality": "good",
            "noise_level": config["noise_level"]
        }
    
    def _calculate_quality_score(self, data: Dict[str, Any]) -> float:
        """Calculate quality score for sensor data"""
        if data["quality"] == "bad":
            return random.uniform(0.0, 0.3)  # Low quality for bad data
        
        # Good data gets high quality score with some variation
        return random.uniform(0.7, 1.0)
    
    def _is_valid_data(self, data: Dict[str, Any]) -> bool:
        """Determine if data is valid (not for cleaning, just for flagging)"""
        if data["quality"] == "bad":
            return False
        
        # Check for reasonable values
        sensor_type = data["sensor"]
        if sensor_type in self.sensor_configs:
            config = self.sensor_configs[sensor_type]
            value = data["value"]
            
            if value is None:
                return False
            
            # Check if value is within reasonable range (with some tolerance)
            if value < config["min"] - 20 or value > config["max"] + 20:
                return False
        
        return True
    
    def generate_raw_sensor_data(self, sensor_type: str) -> Dict[str, Any]:
        """Generate raw sensor data (good or bad)"""
        # 15% chance of generating bad data (simulating real sensor issues)
        if random.random() < 0.15:
            data = self._generate_bad_data(sensor_type)
        else:
            data = self._generate_good_data(sensor_type)
        
        # Add metadata
        data["quality_score"] = self._calculate_quality_score(data)
        data["is_valid"] = self._is_valid_data(data)
        data["sensor_id"] = f"{sensor_type}_{random.randint(1000, 9999)}"
        data["location"] = random.choice(["greenhouse_1", "greenhouse_2", "field_a", "field_b", "lab"])
        data["firmware_version"] = f"v{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        return data
    
    async def save_raw_data(self, data: Dict[str, Any]):
        """Save raw sensor data to database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO raw_sensor_data (timestamp, sensor_type, raw_data, quality_score, is_valid)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                data["timestamp"],
                data["sensor"],
                json.dumps(data),
                data["quality_score"],
                data["is_valid"]
            ))
            
            conn.commit()
            conn.close()
            
            # Print raw data for debugging
            status = "[OK]" if data["is_valid"] else "[BAD]"
            quality = data["quality"]
            print(f"{status} [{data['sensor']}] {data['value']} {data['unit']} (quality: {quality})")
            
            return True
        except Exception as e:
            print(f"[ERROR] Failed to save {data['sensor']}: {e}")
            return False
    
    async def run(self):
        """Run raw sensor data generation"""
        print("🚀 Starting RAW Sensor Data Generator")
        print("=" * 60)
        print("Generating REALISTIC raw sensor data with:")
        print("• Sensor noise and variations")
        print("• Bad data (15% chance)")
        print("• Wrong units and missing values")
        print("• Out-of-range and extreme values")
        print("• Realistic timing variations")
        print("• Quality scores and validation flags")
        print("=" * 60)
        
        sensor_types = list(self.sensor_configs.keys())
        cycle_count = 0
        
        while True:
            cycle_count += 1
            print(f"\n🔄 Cycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"Generating raw data for {len(sensor_types)} sensor types...")
            
            success_count = 0
            bad_data_count = 0
            
            for sensor_type in sensor_types:
                # Generate raw sensor data
                raw_data = self.generate_raw_sensor_data(sensor_type)
                
                # Save to database
                success = await self.save_raw_data(raw_data)
                if success:
                    success_count += 1
                    if not raw_data["is_valid"]:
                        bad_data_count += 1
                
                # Small delay between sensors
                await asyncio.sleep(0.1)
            
            print(f"Cycle {cycle_count} complete:")
            print(f"   [OK] {success_count}/{len(sensor_types)} sensors updated")
            print(f"   [BAD] {bad_data_count} bad data records generated")
            print(f"   Data quality: {((success_count - bad_data_count) / success_count * 100):.1f}%")
            
            # Wait before next cycle
            await asyncio.sleep(10)  # 10 seconds between cycles

if __name__ == "__main__":
    generator = RawSensorDataGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\n🛑 Raw sensor data generation stopped")
        print(f"💾 Raw data saved to: {generator.db_file}")
        print("📋 Check raw_sensor_data table for unprocessed sensor data")
