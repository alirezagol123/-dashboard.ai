import asyncio
import requests
import random
import math
from datetime import datetime

class AnalyticsGenerator:
    """Analytics sensors data generator"""
    
    def __init__(self, api_url="http://localhost:8000"):
        self.api_url = api_url
        self.start_time = datetime.now()
        
        self.sensors = [
            {"type": "energy_usage", "min": 10, "max": 200, "unit": "kWh"},
            {"type": "water_efficiency", "min": 50, "max": 95, "unit": "%"},
            {"type": "yield_efficiency", "min": 60, "max": 99, "unit": "%"},
            {"type": "profit_margin", "min": 5, "max": 40, "unit": "%"},
            {"type": "cost_per_kg", "min": 0.5, "max": 3.0, "unit": "$/kg"}
        ]
        
        self.last_values = {sensor["type"]: random.uniform(sensor["min"], sensor["max"]) for sensor in self.sensors}
    
    def generate_value(self, sensor):
        """Generate realistic analytics values"""
        current_value = self.last_values.get(sensor["type"])
        min_val, max_val = sensor["min"], sensor["max"]
        
        if sensor["type"] == "energy_usage":
            # Daily cycle for energy usage
            hour = (datetime.now() - self.start_time).total_seconds() / 3600 % 24
            time_factor = 0.5 * (1 + math.sin(math.pi * (hour - 8) / 12))
            base_usage = min_val + (max_val - min_val) * time_factor
            noise = random.uniform(-5, 5)
            value = base_usage + noise
            
        elif sensor["type"] in ["water_efficiency", "yield_efficiency"]:
            # Slow improvement over time with small fluctuations
            days_since_start = (datetime.now() - self.start_time).days
            improvement_factor = min(0.1 * days_since_start, 0.2)  # Max 20% improvement
            base_efficiency = min_val + (max_val - min_val) * 0.7 + improvement_factor * (max_val - min_val)
            noise = random.uniform(-1, 1)
            value = base_efficiency + noise
            
        elif sensor["type"] == "profit_margin":
            # Market-dependent profit margin
            market_factor = random.uniform(0.8, 1.2)
            base_margin = min_val + (max_val - min_val) * 0.6
            value = base_margin * market_factor
            
        elif sensor["type"] == "cost_per_kg":
            # Cost inversely related to efficiency
            efficiency = self.last_values.get("yield_efficiency", 80)
            efficiency_factor = 1 - (efficiency - min_val) / (max_val - min_val) * 0.3
            base_cost = min_val + (max_val - min_val) * 0.5
            value = base_cost * efficiency_factor
        
        value = max(min_val, min(max_val, value))
        self.last_values[sensor["type"]] = value
        return round(value, 2)
    
    async def send_data(self, sensor_type, value):
        """Send data to API"""
        data = {"sensor_type": sensor_type, "value": value}
        try:
            response = requests.post(f"{self.api_url}/data", json=data, timeout=5)
            if response.status_code == 200:
                print(f"[ANALYTICS] {sensor_type}: {value}")
            return response.status_code == 200
        except:
            return False
    
    async def run(self):
        """Run analytics data generation"""
        print("Starting Analytics Data Generation")
        print("Sensors: Energy Usage, Water Efficiency, Yield Efficiency, Profit Margin, Cost per kg")
        
        while True:
            for sensor in self.sensors:
                value = self.generate_value(sensor)
                await self.send_data(sensor["type"], value)
                await asyncio.sleep(0.2)
            await asyncio.sleep(8)

if __name__ == "__main__":
    generator = AnalyticsGenerator()
    try:
        asyncio.run(generator.run())
    except KeyboardInterrupt:
        print("\nAnalytics data generation stopped")
