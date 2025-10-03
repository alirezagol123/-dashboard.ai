import asyncio
import requests
import json
import random
import time
from datetime import datetime, timedelta
import math

class FeatureDataGenerator:
    """Individual data generators for each dashboard feature"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        # Environmental sensors
        self.environmental_sensors = [
            {"type": "temperature", "min": 18, "max": 30, "unit": "°C", "trend": "daily_cycle"},
            {"type": "humidity", "min": 40, "max": 90, "unit": "%", "trend": "daily_cycle"},
            {"type": "pressure", "min": 990, "max": 1030, "unit": "hPa", "trend": "random_walk"},
            {"type": "light", "min": 0, "max": 1000, "unit": "lux", "trend": "daily_cycle"},
            {"type": "co2_level", "min": 300, "max": 600, "unit": "ppm", "trend": "daily_cycle"},
            {"type": "wind_speed", "min": 0, "max": 20, "unit": "km/h", "trend": "random_walk"},
            {"type": "rainfall", "min": 0, "max": 10, "unit": "mm", "trend": "event_based"},
            {"type": "soil_temperature", "min": 15, "max": 28, "unit": "°C", "trend": "daily_cycle"}
        ]
        
        # Agricultural sensors
        self.agricultural_sensors = [
            {"type": "soil_moisture", "min": 20, "max": 80, "unit": "%", "trend": "irrigation_cycle"},
            {"type": "soil_ph", "min": 5.5, "max": 7.5, "unit": "pH", "trend": "slow_change"},
            {"type": "nitrogen_level", "min": 20, "max": 100, "unit": "ppm", "trend": "fertilizer_cycle"},
            {"type": "phosphorus_level", "min": 10, "max": 50, "unit": "ppm", "trend": "fertilizer_cycle"},
            {"type": "potassium_level", "min": 30, "max": 150, "unit": "ppm", "trend": "fertilizer_cycle"},
            {"type": "water_usage", "min": 0, "max": 50, "unit": "L/hr", "trend": "irrigation_event"},
            {"type": "fertilizer_usage", "min": 0, "max": 5, "unit": "kg/hr", "trend": "fertilizer_event"},
            {"type": "nutrient_uptake", "min": 0.1, "max": 2.0, "unit": "mg/L", "trend": "growth_cycle"}
        ]
        
        # Pest detection sensors
        self.pest_sensors = [
            {"type": "pest_detection", "min": 0, "max": 1, "unit": "binary", "trend": "event_based"},
            {"type": "disease_risk", "min": 0, "max": 100, "unit": "%", "trend": "slow_change"},
            {"type": "leaf_wetness", "min": 0, "max": 100, "unit": "%", "trend": "daily_cycle"},
            {"type": "pest_count", "min": 0, "max": 50, "unit": "count", "trend": "event_based"}
        ]
        
        # Harvest sensors
        self.harvest_sensors = [
            {"type": "plant_height", "min": 10, "max": 200, "unit": "cm", "trend": "growth_cycle"},
            {"type": "leaf_count", "min": 5, "max": 100, "unit": "count", "trend": "growth_cycle"},
            {"type": "fruit_count", "min": 0, "max": 50, "unit": "count", "trend": "growth_cycle"},
            {"type": "fruit_size", "min": 1, "max": 10, "unit": "cm", "trend": "growth_cycle"},
            {"type": "yield_prediction", "min": 100, "max": 1000, "unit": "kg/ha", "trend": "growth_cycle"}
        ]
        
        # Marketplace data
        self.marketplace_data = [
            {"type": "tomato_price", "min": 1.5, "max": 4.0, "unit": "$/kg", "trend": "market_fluctuation"},
            {"type": "lettuce_price", "min": 0.8, "max": 2.5, "unit": "$/head", "trend": "market_fluctuation"},
            {"type": "pepper_price", "min": 2.0, "max": 5.0, "unit": "$/kg", "trend": "market_fluctuation"},
            {"type": "demand_level", "min": 0, "max": 100, "unit": "index", "trend": "market_fluctuation"},
            {"type": "supply_level", "min": 0, "max": 100, "unit": "index", "trend": "market_fluctuation"}
        ]
        
        # Analytics sensors
        self.analytics_sensors = [
            {"type": "energy_usage", "min": 10, "max": 200, "unit": "kWh", "trend": "daily_cycle"},
            {"type": "water_efficiency", "min": 50, "max": 95, "unit": "%", "trend": "slow_change"},
            {"type": "yield_efficiency", "min": 60, "max": 99, "unit": "%", "trend": "slow_change"},
            {"type": "profit_margin", "min": 5, "max": 40, "unit": "%", "trend": "market_fluctuation"},
            {"type": "cost_per_kg", "min": 0.5, "max": 3.0, "unit": "$/kg", "trend": "market_fluctuation"}
        ]
        
        # Store last values for trends
        self.last_values = {}
        for sensor_group in [self.environmental_sensors, self.agricultural_sensors, 
                           self.pest_sensors, self.harvest_sensors, 
                           self.marketplace_data, self.analytics_sensors]:
            for sensor in sensor_group:
                self.last_values[sensor["type"]] = random.uniform(sensor["min"], sensor["max"])
    
    def generate_realistic_value(self, sensor):
        """Generate realistic values based on trend patterns"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        if sensor["trend"] == "daily_cycle":
            # Simulate daily cycles
            hour = (datetime.now() - self.start_time).total_seconds() / 3600 % 24
            if sensor["type"] == "temperature":
                value = min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 8) / 12)))
            elif sensor["type"] == "humidity":
                value = min_val + (max_val - min_val) * (0.5 * (1 - math.sin(math.pi * (hour - 8) / 12)))
            elif sensor["type"] == "light":
                value = max(0, min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 6) / 12))))
            else:
                value = min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 8) / 12)))
            value += random.uniform(-0.5, 0.5)
            
        elif sensor["trend"] == "random_walk":
            change = random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
            value = current_value + change
            
        elif sensor["trend"] == "irrigation_cycle":
            if random.random() < 0.05:  # 5% chance of irrigation
                value = random.uniform(70, max_val)
            else:
                value = current_value - random.uniform(0.5, 2.0)
                
        elif sensor["trend"] == "fertilizer_cycle":
            if random.random() < 0.02:  # 2% chance of fertilization
                value = random.uniform(80, max_val)
            else:
                value = current_value - random.uniform(0.1, 0.5)
                
        elif sensor["trend"] == "event_based":
            if random.random() < 0.01:  # 1% chance of event
                value = random.uniform(max_val * 0.5, max_val)
            else:
                value = random.uniform(min_val, min_val * 1.1)
                
        elif sensor["trend"] == "slow_change":
            change = random.uniform(-0.01 * (max_val - min_val), 0.01 * (max_val - min_val))
            value = current_value + change
            
        elif sensor["trend"] == "growth_cycle":
            days_since_start = (datetime.now() - self.start_time).days
            growth_factor = 1 - math.exp(-0.05 * days_since_start)
            value = min_val + (max_val - min_val) * growth_factor
            value += random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
            
        elif sensor["trend"] == "market_fluctuation":
            change = random.uniform(-0.05 * (max_val - min_val), 0.05 * (max_val - min_val))
            value = current_value + change
            
        else:
            value = random.uniform(min_val, max_val)
        
        # Ensure value stays within bounds
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to the API"""
        data = {
            "sensor_type": sensor_type,
            "value": value
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/data",
                json=data,
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code == 200:
                if random.random() < 0.1:  # Log 10% of sends
                    print(f"[DATA] {sensor_type}: {value}")
                return True
            else:
                print(f"[ERROR] Failed to send {sensor_type}: {response.status_code}")
                return False
                
        except Exception as e:
            if random.random() < 0.05:  # Log 5% of errors
                print(f"[ERROR] {sensor_type}: {e}")
            return False
    
    async def simulate_feature(self, sensors, feature_name, interval=2):
        """Simulate a specific feature"""
        print(f"[{feature_name.upper()}] Starting {feature_name} simulation with {len(sensors)} sensors")
        
        while True:
            for sensor in sensors:
                value = self.generate_realistic_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.1)  # Small delay between sensors
            
            await asyncio.sleep(interval)
    
    async def run_all_features(self):
        """Run all feature simulations concurrently"""
        print("Starting Comprehensive Agriculture Data Generation")
        print("=" * 60)
        
        # Create tasks for each feature
        tasks = [
            asyncio.create_task(self.simulate_feature(self.environmental_sensors, "environmental", 3)),
            asyncio.create_task(self.simulate_feature(self.agricultural_sensors, "agricultural", 4)),
            asyncio.create_task(self.simulate_feature(self.pest_sensors, "pest_detection", 5)),
            asyncio.create_task(self.simulate_feature(self.harvest_sensors, "harvest", 6)),
            asyncio.create_task(self.simulate_feature(self.marketplace_data, "marketplace", 10)),
            asyncio.create_task(self.simulate_feature(self.analytics_sensors, "analytics", 8))
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
            for task in tasks:
                task.cancel()

def main():
    """Main function"""
    generator = FeatureDataGenerator()
    
    try:
        asyncio.run(generator.run_all_features())
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    print("Feature-Based Agriculture Data Generator")
    print("=" * 50)
    main()
