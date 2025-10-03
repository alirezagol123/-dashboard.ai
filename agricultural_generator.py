import asyncio
import requests
import random
import math
from datetime import datetime

class AgriculturalDataGenerator:
    """Agricultural sensors data generator"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        self.sensors = [
            {"type": "soil_moisture", "min": 20, "max": 80, "unit": "%"},
            {"type": "soil_ph", "min": 5.5, "max": 7.5, "unit": "pH"},
            {"type": "nitrogen_level", "min": 20, "max": 100, "unit": "ppm"},
            {"type": "phosphorus_level", "min": 10, "max": 50, "unit": "ppm"},
            {"type": "potassium_level", "min": 30, "max": 150, "unit": "ppm"},
            {"type": "water_usage", "min": 0, "max": 50, "unit": "L/hr"},
            {"type": "fertilizer_usage", "min": 0, "max": 5, "unit": "kg/hr"},
            {"type": "nutrient_uptake", "min": 0.1, "max": 2.0, "unit": "mg/L"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
    
    def generate_value(self, sensor):
        """Generate realistic agricultural values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        if sensor["type"] == "soil_moisture":
            # Irrigation cycle simulation
            if random.random() < 0.05:  # 5% chance of irrigation
                value = random.uniform(70, max_val)
            else:
                value = current_value - random.uniform(0.5, 2.0)
                
        elif sensor["type"] in ["nitrogen_level", "phosphorus_level", "potassium_level"]:
            # Fertilizer cycle simulation
            if random.random() < 0.02:  # 2% chance of fertilization
                value = random.uniform(80, max_val)
            else:
                value = current_value - random.uniform(0.1, 0.5)
                
        elif sensor["type"] == "soil_ph":
            # Slow change for pH
            change = random.uniform(-0.01, 0.01)
            value = current_value + change
            
        elif sensor["type"] in ["water_usage", "fertilizer_usage"]:
            # Event-based usage
            if random.random() < 0.1:  # 10% chance of usage event
                value = random.uniform(max_val * 0.5, max_val)
            else:
                value = random.uniform(0, min_val * 0.5)
                
        else:
            # Gradual change for nutrient uptake
            change = random.uniform(-0.01, 0.01)
            value = current_value + change
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API"""
        data = {"sensor_type": sensor_type, "value": value}
        try:
            response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
            if response.status_code == 200:
                print(f"[AGRI] {sensor_type}: {value}")
            return response.status_code == 200
        except:
            return False
    
    async def run(self):
        """Run agricultural data generation"""
        print("Starting Agricultural Data Generation")
        print("Sensors: Soil Moisture, pH, N-P-K Levels, Water/Fertilizer Usage, Nutrient Uptake")
        
        while True:
            for sensor in self.sensors:
                value = self.generate_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.2)
            await asyncio.sleep(4)

if __name__ == "__main__":
    generator = AgriculturalDataGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\nAgricultural data generation stopped")
