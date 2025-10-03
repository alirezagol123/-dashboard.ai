import asyncio
import requests
import random
import math
import sqlite3
import json
from datetime import datetime

class EnvironmentalDataGenerator:
    """Environmental sensors data generator"""
    
    def __init__(self, api_url="http://localhost:8000", use_database=True):
        self.api_url = api_url
        self.use_database = use_database
        self.start_time = datetime.now()
        self.db_file = "smart_dashboard.db"
        
        self.sensors = [
            # Environmental Sensors
            {"type": "temperature", "min": 15.02, "max": 34.99, "unit": "°C"},
            {"type": "humidity", "min": 22.50, "max": 89.99, "unit": "%"},
            {"type": "pressure", "min": 25.00, "max": 1030.00, "unit": "hPa"},
            {"type": "light", "min": 0.00, "max": 999.60, "unit": "lux"},
            {"type": "co2_level", "min": 300.00, "max": 600.00, "unit": "ppm"},
            {"type": "co2", "min": 300.00, "max": 600.00, "unit": "ppm"},
            {"type": "wind_speed", "min": 0.00, "max": 20.00, "unit": "m/s"},
            {"type": "rainfall", "min": 0.00, "max": 9.97, "unit": "mm"},
            
            # Soil Sensors
            {"type": "soil_moisture", "min": 20.00, "max": 79.86, "unit": "%"},
            {"type": "soil_ph", "min": 5.50, "max": 7.50, "unit": "pH"},
            {"type": "soil_temperature", "min": 15.00, "max": 28.00, "unit": "°C"},
            
            # Plant Growth Sensors
            {"type": "plant_height", "min": 10.00, "max": 188.54, "unit": "cm"},
            {"type": "fruit_count", "min": 0.00, "max": 19.90, "unit": "count"},
            {"type": "fruit_size", "min": 1.00, "max": 1.90, "unit": "cm"},
            {"type": "leaf_count", "min": 5.00, "max": 50.00, "unit": "count"},
            {"type": "leaf_wetness", "min": 0.00, "max": 100.00, "unit": "%"},
            
            # Nutrient Sensors
            {"type": "nitrogen_level", "min": 20.00, "max": 96.57, "unit": "ppm"},
            {"type": "phosphorus_level", "min": 10.00, "max": 50.00, "unit": "ppm"},
            {"type": "potassium_level", "min": 30.00, "max": 145.65, "unit": "ppm"},
            {"type": "nutrient_uptake", "min": 0.00, "max": 100.00, "unit": "mg/L"},
            
            # Pest & Disease Sensors
            {"type": "pest_count", "min": 0.00, "max": 48.32, "unit": "count"},
            {"type": "pest_detection", "min": 0.00, "max": 1.00, "unit": "binary"},
            {"type": "disease_risk", "min": 0.00, "max": 98.44, "unit": "%"},
            
            # Water Management
            {"type": "water_usage", "min": 0.00, "max": 49.74, "unit": "L"},
            {"type": "water_efficiency", "min": 61.52, "max": 94.86, "unit": "%"},
            
            # Yield & Production
            {"type": "yield_prediction", "min": 100.00, "max": 174.51, "unit": "kg"},
            {"type": "yield_efficiency", "min": 62.57, "max": 89.86, "unit": "%"},
            
            # Market & Economics
            {"type": "tomato_price", "min": 1.50, "max": 4.46, "unit": "$/kg"},
            {"type": "lettuce_price", "min": 0.80, "max": 2.98, "unit": "$/head"},
            {"type": "pepper_price", "min": 2.01, "max": 5.00, "unit": "$/kg"},
            {"type": "cost_per_kg", "min": 1.50, "max": 3.50, "unit": "$/kg"},
            {"type": "demand_level", "min": 0.00, "max": 100.00, "unit": "%"},
            {"type": "supply_level", "min": 0.00, "max": 100.00, "unit": "%"},
            {"type": "profit_margin", "min": 15.00, "max": 35.00, "unit": "%"},
            
            # Additional Sensors
            {"type": "motion", "min": 0.00, "max": 30.00, "unit": "count"},
            {"type": "fertilizer_usage", "min": 0.00, "max": 5.00, "unit": "kg"},
            {"type": "energy_usage", "min": 10.00, "max": 195.80, "unit": "kWh"},
            {"type": "test_temperature", "min": 15.00, "max": 35.00, "unit": "°C"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
        
        # Initialize database if using database mode
        if self.use_database:
            self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Create sensor_data table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_type TEXT NOT NULL,
                    value REAL NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            print(f"[OK] Database initialized: {self.db_file}")
        except Exception as e:
            print(f"[ERROR] Database initialization error: {e}")
            self.use_database = False
    
    def generate_value(self, sensor):
        """Generate realistic environmental values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        # Daily cycle simulation
        hour = (datetime.now() - self.start_time).total_seconds() / 3600 % 24
        
        # Environmental sensors with daily cycles
        if sensor["type"] in ["temperature", "co2_level", "co2", "test_temperature"]:
            value = min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 8) / 12)))
        elif sensor["type"] in ["humidity", "soil_moisture", "leaf_wetness"]:
            value = min_val + (max_val - min_val) * (0.5 * (1 - math.sin(math.pi * (hour - 8) / 12)))
        elif sensor["type"] in ["light"]:
            value = max(0, min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 6) / 12))))
        elif sensor["type"] in ["rainfall"]:
            if random.random() < 0.05:  # 5% chance of rain
                value = random.uniform(1, max_val)
            else:
                value = random.uniform(0, 0.5)
        elif sensor["type"] in ["soil_temperature"]:
            # Soil temperature follows air temperature with delay
            base_temp = min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 10) / 12)))
            value = base_temp + random.uniform(-2, 2)
        elif sensor["type"] in ["plant_height", "fruit_count", "fruit_size", "leaf_count"]:
            # Plant growth - slow increase over time
            growth_factor = (datetime.now() - self.start_time).total_seconds() / 86400  # Days
            base_value = min_val + (max_val - min_val) * min(growth_factor / 30, 1)  # 30 days to reach max
            value = base_value + random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
        elif sensor["type"] in ["pest_count", "disease_risk"]:
            # Pest/disease - occasional spikes
            if random.random() < 0.1:  # 10% chance of spike
                value = random.uniform(max_val * 0.7, max_val)
            else:
                value = random.uniform(min_val, max_val * 0.3)
        elif sensor["type"] in ["pest_detection"]:
            # Binary detection
            value = 1 if random.random() < 0.05 else 0  # 5% chance of detection
        elif sensor["type"] in ["water_usage", "fertilizer_usage", "energy_usage"]:
            # Usage patterns - higher during day
            day_factor = 0.5 * (1 + math.sin(math.pi * (hour - 6) / 12))
            value = min_val + (max_val - min_val) * day_factor + random.uniform(-0.1, 0.1)
        elif sensor["type"] in ["water_efficiency", "yield_efficiency", "profit_margin"]:
            # Efficiency metrics - generally stable with small variations
            base_efficiency = (min_val + max_val) / 2
            value = base_efficiency + random.uniform(-0.05 * (max_val - min_val), 0.05 * (max_val - min_val))
        elif sensor["type"] in ["yield_prediction"]:
            # Yield prediction - seasonal pattern
            seasonal_factor = 0.5 * (1 + math.sin(math.pi * hour / 12))
            value = min_val + (max_val - min_val) * seasonal_factor
        elif sensor["type"] in ["tomato_price", "lettuce_price", "pepper_price", "cost_per_kg"]:
            # Market prices - random walk with occasional spikes
            if random.random() < 0.05:  # 5% chance of price spike
                value = random.uniform(max_val * 0.8, max_val)
            else:
                change = random.uniform(-0.02 * (max_val - min_val), 0.02 * (max_val - min_val))
                value = current_value + change
        elif sensor["type"] in ["demand_level", "supply_level"]:
            # Market levels - correlated with time of day
            time_factor = 0.5 * (1 + math.sin(math.pi * (hour - 8) / 12))
            value = min_val + (max_val - min_val) * time_factor + random.uniform(-0.1, 0.1)
        elif sensor["type"] in ["nitrogen_level", "phosphorus_level", "potassium_level", "nutrient_uptake"]:
            # Nutrient levels - decrease over time, occasional replenishment
            depletion_factor = (datetime.now() - self.start_time).total_seconds() / 86400 / 7  # Weekly depletion
            base_value = max_val * (1 - min(depletion_factor, 0.5))  # Max 50% depletion
            if random.random() < 0.1:  # 10% chance of fertilizer application
                value = random.uniform(max_val * 0.8, max_val)
            else:
                value = base_value + random.uniform(-0.05 * (max_val - min_val), 0.05 * (max_val - min_val))
        elif sensor["type"] in ["soil_ph"]:
            # pH - very stable with small variations
            base_ph = (min_val + max_val) / 2
            value = base_ph + random.uniform(-0.1, 0.1)
        elif sensor["type"] in ["pressure", "wind_speed", "motion"]:
            # Weather and motion - random variations
            change = random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
            value = current_value + change
        else:
            # Default random walk for other sensors
            change = random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
            value = current_value + change
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API or database"""
        timestamp = datetime.now().isoformat()
        data = {"sensor_type": sensor_type, "value": value, "timestamp": timestamp}
        
        # Try API first if not using database mode
        if not self.use_database:
            try:
                response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
                if response.status_code == 200:
                    print(f"[ENV] {sensor_type}: {value}")
                    return True
            except Exception as e:
                print(f"[API ERROR] {sensor_type}: {e}")
        
        # Try database if API fails or database mode is enabled
        if self.use_database:
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO sensor_data (timestamp, sensor_type, value)
                    VALUES (?, ?, ?)
                ''', (timestamp, sensor_type, value))
                
                conn.commit()
                conn.close()
                print(f"[DB] {sensor_type}: {value}")
                return True
            except Exception as e:
                print(f"[DB ERROR] {sensor_type}: {e}")
        
            return False
    
    async def run(self):
        """Run environmental data generation"""
        print("Starting Comprehensive Environmental Data Generation")
        print("Generating data for ALL 38 sensor types:")
        print("   Environmental: Temperature, Humidity, Pressure, Light, CO2, Wind, Rainfall")
        print("   Soil: Moisture, pH, Temperature")
        print("   Plant Growth: Height, Fruit Count/Size, Leaf Count/Wetness")
        print("   Nutrients: Nitrogen, Phosphorus, Potassium, Uptake")
        print("   Pest/Disease: Count, Detection, Risk")
        print("   Water: Usage, Efficiency")
        print("   Yield: Prediction, Efficiency")
        print("   Market: Prices, Demand/Supply, Profit")
        print("   Additional: Motion, Fertilizer, Energy, Test Temperature")
        
        if self.use_database:
            print(f"Mode: Database ({self.db_file})")
        else:
            print(f"Mode: API ({self.api_url})")
        
        print("Press Ctrl+C to stop")
        print("-" * 60)
        
        cycle_count = 0
        
        while True:
            cycle_count += 1
            print(f"\nCycle {cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"Generating data for {len(self.sensors)} sensors...")
            
            success_count = 0
            for i, sensor in enumerate(self.sensors):
                value = self.generate_value(sensor)
                success = await self.send_data(sensor["type"], value)
                if success:
                    success_count += 1
                else:
                    print(f"Failed to send {sensor['type']}")
                
                # Show progress every 10 sensors
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i + 1}/{len(self.sensors)} sensors processed")
                
                await asyncio.sleep(0.1)  # Reduced delay for faster processing
            
            print(f"Cycle {cycle_count} complete: {success_count}/{len(self.sensors)} sensors updated")
            await asyncio.sleep(5)  # Wait 5 seconds between cycles

if __name__ == "__main__":
    # Use database mode by default (more reliable)
    generator = EnvironmentalDataGenerator(use_database=True)
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\n[STOPPED] Environmental data generation stopped")
        print(f"[SAVED] Data saved to: {generator.db_file}")
