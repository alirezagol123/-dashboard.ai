import asyncio
import requests
import random
import math
from datetime import datetime

class PestDetectionGenerator:
    """Pest detection sensors data generator"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        self.sensors = [
            {"type": "pest_detection", "min": 0, "max": 1, "unit": "binary"},
            {"type": "disease_risk", "min": 0, "max": 100, "unit": "%"},
            {"type": "leaf_wetness", "min": 0, "max": 100, "unit": "%"},
            {"type": "pest_count", "min": 0, "max": 50, "unit": "count"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
    
    def generate_value(self, sensor):
        """Generate realistic pest detection values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        if sensor["type"] == "pest_detection":
            # Binary detection - mostly 0, occasional 1
            if random.random() < 0.01:  # 1% chance of pest detection
                value = 1
            else:
                value = 0
                
        elif sensor["type"] == "pest_count":
            # Event-based pest count
            if random.random() < 0.02:  # 2% chance of pest event
                value = random.uniform(5, max_val)
            else:
                value = random.uniform(0, 2)
                
        elif sensor["type"] == "disease_risk":
            # Slow change in disease risk
            change = random.uniform(-0.5, 0.5)
            value = current_value + change
            
        elif sensor["type"] == "leaf_wetness":
            # Daily cycle for leaf wetness
            hour = (datetime.now() - self.start_time).total_seconds() / 3600 % 24
            value = min_val + (max_val - min_val) * (0.5 * (1 + math.sin(math.pi * (hour - 6) / 12)))
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API"""
        data = {"sensor_type": sensor_type, "value": value}
        try:
            response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
            if response.status_code == 200:
                print(f"[PEST] {sensor_type}: {value}")
            return response.status_code == 200
        except:
            return False
    
    async def run(self):
        """Run pest detection data generation"""
        print("Starting Pest Detection Data Generation")
        print("Sensors: Pest Detection, Disease Risk, Leaf Wetness, Pest Count")
        
        while True:
            for sensor in self.sensors:
                value = self.generate_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.2)
            await asyncio.sleep(5)

if __name__ == "__main__":
    generator = PestDetectionGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\nPest detection data generation stopped")
