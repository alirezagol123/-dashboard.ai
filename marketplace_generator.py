import asyncio
import requests
import random
import math
from datetime import datetime

class MarketplaceGenerator:
    """Marketplace data generator"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        self.sensors = [
            {"type": "tomato_price", "min": 1.5, "max": 4.0, "unit": "$/kg"},
            {"type": "lettuce_price", "min": 0.8, "max": 2.5, "unit": "$/head"},
            {"type": "pepper_price", "min": 2.0, "max": 5.0, "unit": "$/kg"},
            {"type": "demand_level", "min": 0, "max": 100, "unit": "index"},
            {"type": "supply_level", "min": 0, "max": 100, "unit": "index"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
    
    def generate_value(self, sensor):
        """Generate realistic marketplace values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        if sensor["type"] in ["tomato_price", "lettuce_price", "pepper_price"]:
            # Market fluctuation simulation
            change = random.uniform(-0.05 * (max_val - min_val), 0.05 * (max_val - min_val))
            value = current_value + change
            
        elif sensor["type"] == "demand_level":
            # Demand influenced by time of day and season
            hour = (datetime.now() - self.start_time).total_seconds() / 3600 % 24
            time_factor = 0.5 * (1 + math.sin(math.pi * (hour - 6) / 12))
            base_demand = min_val + (max_val - min_val) * time_factor
            noise = random.uniform(-10, 10)
            value = base_demand + noise
            
        elif sensor["type"] == "supply_level":
            # Supply inversely related to demand with some lag
            demand = self.last_values.get("demand_level", 50)
            inverse_supply = max_val - (demand * 0.8)  # Supply decreases as demand increases
            noise = random.uniform(-5, 5)
            value = inverse_supply + noise
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API"""
        data = {"sensor_type": sensor_type, "value": value}
        try:
            response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
            if response.status_code == 200:
                print(f"[MARKET] {sensor_type}: {value}")
            return response.status_code == 200
        except:
            return False
    
    async def run(self):
        """Run marketplace data generation"""
        print("Starting Marketplace Data Generation")
        print("Sensors: Tomato Price, Lettuce Price, Pepper Price, Demand Level, Supply Level")
        
        while True:
            for sensor in self.sensors:
                value = self.generate_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.2)
            await asyncio.sleep(10)

if __name__ == "__main__":
    generator = MarketplaceGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\nMarketplace data generation stopped")
