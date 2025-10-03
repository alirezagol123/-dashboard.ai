import asyncio
import requests
import json
import random
import time
from datetime import datetime, timedelta
import math

class SimpleDataSimulator:
    """Simple simulator that starts immediately without historical data seeding"""
    
    def __init__(self, api_url="http://localhost:8000", interval=3):
        self.api_url = api_url
        self.interval = interval
        self.start_time = datetime.now()
        
        # Core sensors for immediate data generation
        self.sensors = [
            {"type": "temperature", "min": 15, "max": 35, "unit": "°C"},
            {"type": "humidity", "min": 30, "max": 80, "unit": "%"},
            {"type": "pressure", "min": 980, "max": 1020, "unit": "hPa"},
            {"type": "light", "min": 0, "max": 1000, "unit": "lux"},
            {"type": "soil_moisture", "min": 20, "max": 80, "unit": "%"},
            {"type": "soil_ph", "min": 5.5, "max": 7.5, "unit": "pH"},
            {"type": "nitrogen_level", "min": 20, "max": 80, "unit": "ppm"},
            {"type": "phosphorus_level", "min": 15, "max": 50, "unit": "ppm"},
            {"type": "pest_detection", "min": 0, "max": 1, "unit": "binary"},
            {"type": "disease_risk", "min": 0, "max": 100, "unit": "%"},
            {"type": "plant_height", "min": 10, "max": 200, "unit": "cm"},
            {"type": "fruit_count", "min": 0, "max": 20, "unit": "count"},
            {"type": "tomato_price", "min": 2.5, "max": 4.5, "unit": "$/kg"},
            {"type": "lettuce_price", "min": 1.5, "max": 3.0, "unit": "$/head"},
            {"type": "energy_usage", "min": 50, "max": 200, "unit": "kWh"},
            {"type": "water_efficiency", "min": 70, "max": 95, "unit": "%"},
            {"type": "yield_efficiency", "min": 60, "max": 90, "unit": "%"},
            {"type": "profit_margin", "min": 15, "max": 35, "unit": "%"}
        ]
    
    def generate_value(self, sensor):
        """Generate realistic sensor values"""
        if sensor["type"] == "pest_detection":
            return random.choice([0, 1])
        elif sensor["type"] == "soil_ph":
            return round(random.uniform(sensor["min"], sensor["max"]), 1)
        else:
            return round(random.uniform(sensor["min"], sensor["max"]), 2)
    
    async def send_data(self, sensor_type, value):
        """Send sensor data to the API"""
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
    
    async def simulate_sensor(self, sensor):
        """Simulate a single sensor"""
        sensor_name = sensor["type"]
        consecutive_failures = 0
        max_failures = 5
        
        while True:
            try:
                value = self.generate_value(sensor)
                success = await self.send_data(sensor_name, value)
                
                if success:
                    consecutive_failures = 0
                    await asyncio.sleep(self.interval)
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print(f"[WARN] Sensor {sensor_name} failed {max_failures} times, pausing...")
                        await asyncio.sleep(30)
                        consecutive_failures = 0
                    else:
                        await asyncio.sleep(self.interval * 2)
                        
            except Exception as e:
                print(f"[ERROR] Sensor {sensor_name} error: {e}")
                await asyncio.sleep(self.interval * 3)
    
    async def run_simulation(self):
        """Run the simulation"""
        print("Starting Simple Agriculture Data Simulator")
        print(f"API URL: {self.api_url}")
        print(f"Interval: {self.interval} seconds")
        print(f"Total Sensors: {len(self.sensors)}")
        print("-" * 50)
        print("Starting real-time data generation...")
        
        # Create tasks for all sensors
        tasks = []
        for sensor in self.sensors:
            task = asyncio.create_task(self.simulate_sensor(sensor))
            tasks.append(task)
        
        # Run all tasks concurrently
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
            for task in tasks:
                task.cancel()
        except Exception as e:
            print(f"\nSimulation error: {e}")
            print("Continuing with individual sensor tasks...")

def main():
    """Main function to run the simulator"""
    simulator = SimpleDataSimulator()
    
    try:
        asyncio.run(simulator.run_simulation())
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    print("Simple Agriculture Data Simulator")
    print("=" * 50)
    main()
