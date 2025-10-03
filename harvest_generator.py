import asyncio
import requests
import random
import math
from datetime import datetime

class HarvestGenerator:
    """Harvest sensors data generator"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        self.sensors = [
            {"type": "plant_height", "min": 10, "max": 200, "unit": "cm"},
            {"type": "leaf_count", "min": 5, "max": 100, "unit": "count"},
            {"type": "fruit_count", "min": 0, "max": 50, "unit": "count"},
            {"type": "fruit_size", "min": 1, "max": 10, "unit": "cm"},
            {"type": "yield_prediction", "min": 100, "max": 1000, "unit": "kg/ha"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
    
    def generate_value(self, sensor):
        """Generate realistic harvest values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        # Growth cycle simulation
        days_since_start = (datetime.now() - self.start_time).days
        growth_factor = 1 - math.exp(-0.05 * days_since_start)
        
        if sensor["type"] in ["plant_height", "leaf_count", "fruit_count", "fruit_size"]:
            # Gradual growth with some noise
            base_value = min_val + (max_val - min_val) * growth_factor
            noise = random.uniform(-0.1 * (max_val - min_val), 0.1 * (max_val - min_val))
            value = base_value + noise
            
        elif sensor["type"] == "yield_prediction":
            # Yield prediction based on other factors
            base_yield = min_val + (max_val - min_val) * growth_factor
            # Add some market/weather influence
            market_factor = random.uniform(0.8, 1.2)
            value = base_yield * market_factor
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API"""
        data = {"sensor_type": sensor_type, "value": value}
        try:
            response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
            if response.status_code == 200:
                print(f"[HARVEST] {sensor_type}: {value}")
            return response.status_code == 200
        except:
            return False
    
    async def run(self):
        """Run harvest data generation"""
        print("Starting Harvest Data Generation")
        print("Sensors: Plant Height, Leaf Count, Fruit Count, Fruit Size, Yield Prediction")
        
        while True:
            for sensor in self.sensors:
                value = self.generate_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.2)
            await asyncio.sleep(6)

if __name__ == "__main__":
    generator = HarvestGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\nHarvest data generation stopped")
