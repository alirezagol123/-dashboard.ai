import asyncio
import requests
import json
import random
import time
from datetime import datetime, timedelta
import math

class ComprehensiveDataSimulator:
    """Comprehensive simulator for generating data for all dashboard features"""
    
    def __init__(self, api_url="http://localhost:8000", interval=2):
        self.api_url = api_url
        self.interval = interval
        self.start_time = datetime.now()
        
        # Core environmental sensors
        self.environmental_sensors = [
            {"type": "temperature", "min": 15, "max": 35, "unit": "°C", "trend": "daily"},
            {"type": "humidity", "min": 30, "max": 80, "unit": "%", "trend": "daily"},
            {"type": "pressure", "min": 980, "max": 1020, "unit": "hPa", "trend": "stable"},
            {"type": "light", "min": 0, "max": 1000, "unit": "lux", "trend": "daily"},
            {"type": "motion", "min": 0, "max": 1, "unit": "binary", "trend": "random"},
            {"type": "co2", "min": 350, "max": 500, "unit": "ppm", "trend": "daily"},
            {"type": "wind_speed", "min": 0, "max": 15, "unit": "m/s", "trend": "random"},
            {"type": "rainfall", "min": 0, "max": 10, "unit": "mm", "trend": "random"}
        ]
        
        # Agricultural sensors
        self.agricultural_sensors = [
            {"type": "soil_moisture", "min": 20, "max": 80, "unit": "%", "trend": "irrigation"},
            {"type": "soil_ph", "min": 5.5, "max": 7.5, "unit": "pH", "trend": "slow"},
            {"type": "soil_temperature", "min": 10, "max": 30, "unit": "°C", "trend": "daily"},
            {"type": "nitrogen_level", "min": 20, "max": 80, "unit": "ppm", "trend": "fertilizer"},
            {"type": "phosphorus_level", "min": 15, "max": 50, "unit": "ppm", "trend": "fertilizer"},
            {"type": "potassium_level", "min": 100, "max": 300, "unit": "ppm", "trend": "fertilizer"},
            {"type": "water_usage", "min": 0, "max": 100, "unit": "L", "trend": "irrigation"},
            {"type": "fertilizer_usage", "min": 0, "max": 5, "unit": "kg", "trend": "fertilizer"}
        ]
        
        # Pest and disease detection
        self.pest_sensors = [
            {"type": "pest_detection", "min": 0, "max": 1, "unit": "binary", "trend": "random"},
            {"type": "disease_risk", "min": 0, "max": 100, "unit": "%", "trend": "environmental"},
            {"type": "leaf_wetness", "min": 0, "max": 100, "unit": "%", "trend": "daily"},
            {"type": "pest_count", "min": 0, "max": 50, "unit": "count", "trend": "random"}
        ]
        
        # Harvest and yield data
        self.harvest_sensors = [
            {"type": "plant_height", "min": 10, "max": 200, "unit": "cm", "trend": "growth"},
            {"type": "leaf_count", "min": 5, "max": 50, "unit": "count", "trend": "growth"},
            {"type": "fruit_count", "min": 0, "max": 20, "unit": "count", "trend": "growth"},
            {"type": "fruit_size", "min": 1, "max": 15, "unit": "cm", "trend": "growth"},
            {"type": "yield_prediction", "min": 0, "max": 100, "unit": "%", "trend": "growth"}
        ]
        
        # Marketplace data
        self.marketplace_data = [
            {"type": "tomato_price", "min": 2.5, "max": 4.5, "unit": "$/kg", "trend": "market"},
            {"type": "lettuce_price", "min": 1.5, "max": 3.0, "unit": "$/head", "trend": "market"},
            {"type": "pepper_price", "min": 3.0, "max": 5.5, "unit": "$/kg", "trend": "market"},
            {"type": "demand_level", "min": 0, "max": 100, "unit": "%", "trend": "market"},
            {"type": "supply_level", "min": 0, "max": 100, "unit": "%", "trend": "market"}
        ]
        
        # Analytics and performance metrics
        self.analytics_sensors = [
            {"type": "energy_usage", "min": 50, "max": 200, "unit": "kWh", "trend": "daily"},
            {"type": "water_efficiency", "min": 70, "max": 95, "unit": "%", "trend": "improvement"},
            {"type": "yield_efficiency", "min": 60, "max": 90, "unit": "%", "trend": "improvement"},
            {"type": "profit_margin", "min": 15, "max": 35, "unit": "%", "trend": "market"},
            {"type": "cost_per_kg", "min": 1.5, "max": 3.5, "unit": "$", "trend": "cost"}
        ]
        
        # Combine all sensors
        self.all_sensors = (
            self.environmental_sensors + 
            self.agricultural_sensors + 
            self.pest_sensors + 
            self.harvest_sensors + 
            self.marketplace_data + 
            self.analytics_sensors
        )
        
        # Historical data seeding
        self.historical_days = 30
        
    def get_time_factor(self, trend_type, sensor_type):
        """Calculate time-based factor for realistic data patterns"""
        elapsed_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        if trend_type == "daily":
            # Daily cycle (day/night)
            hour_of_day = datetime.now().hour
            if sensor_type in ["temperature", "light", "co2"]:
                # Higher during day
                return 0.7 + 0.3 * math.sin((hour_of_day - 6) * math.pi / 12)
            elif sensor_type in ["humidity"]:
                # Higher at night
                return 0.7 + 0.3 * math.sin((hour_of_day - 18) * math.pi / 12)
            else:
                return 1.0
                
        elif trend_type == "irrigation":
            # Irrigation cycles (every 6 hours)
            cycle_position = (elapsed_hours % 6) / 6
            if cycle_position < 0.1:  # Irrigation period
                return 1.5
            else:
                return 0.8
                
        elif trend_type == "fertilizer":
            # Fertilizer application cycles (weekly)
            week_position = (elapsed_hours % (24 * 7)) / (24 * 7)
            if week_position < 0.05:  # Fertilizer application
                return 2.0
            else:
                return 0.9
                
        elif trend_type == "growth":
            # Gradual growth over time
            return 1.0 + (elapsed_hours / (24 * 30)) * 0.5  # 50% growth over 30 days
            
        elif trend_type == "market":
            # Market fluctuations
            return 0.8 + 0.4 * math.sin(elapsed_hours * math.pi / 24)
            
        elif trend_type == "environmental":
            # Environmental factors affecting disease risk
            return 0.5 + 0.5 * math.sin(elapsed_hours * math.pi / 12)
            
        else:
            return 1.0
    
    def generate_realistic_value(self, sensor):
        """Generate realistic sensor values with patterns and correlations"""
        base_min = sensor["min"]
        base_max = sensor["max"]
        trend_type = sensor.get("trend", "random")
        sensor_type = sensor["type"]
        
        # Apply time-based factor
        time_factor = self.get_time_factor(trend_type, sensor_type)
        
        # Adjust range based on time factor
        adjusted_min = base_min + (base_max - base_min) * 0.1 * (1 - time_factor)
        adjusted_max = base_max - (base_max - base_min) * 0.1 * (1 - time_factor)
        
        # Add some randomness but keep it realistic
        if sensor_type == "motion" or sensor_type == "pest_detection":
            # Binary values
            return random.choice([0, 1])
        elif sensor_type in ["soil_ph"]:
            # More precise for pH
            return round(random.uniform(adjusted_min, adjusted_max), 1)
        elif sensor_type in ["nitrogen_level", "phosphorus_level", "potassium_level"]:
            # Nutrient levels with some correlation
            base_value = random.uniform(adjusted_min, adjusted_max)
            # Add correlation with soil moisture
            moisture_factor = random.uniform(0.9, 1.1)
            return round(base_value * moisture_factor, 1)
        else:
            # Regular sensors
            return round(random.uniform(adjusted_min, adjusted_max), 2)
    
    async def send_data(self, sensor_type, value):
        """Send sensor data to the API with retry logic"""
        data = {
            "sensor_type": sensor_type,
            "value": value
        }
        
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.api_url}/data",
                    json=data,
                    headers={"Content-Type": "application/json"},
                    timeout=5
                )
                
                if response.status_code == 200:
                    # Log occasionally to reduce noise
                    if random.random() < 0.05:  # Log 5% of successful sends
                        print(f"[DATA] {sensor_type}: {value} {self.get_sensor_unit(sensor_type)}")
                    return True
                else:
                    print(f"[ERROR] Failed to send {sensor_type}: {response.status_code}")
                    return False
                    
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    if attempt == 0:
                        print("[WAIT] Waiting for backend to be ready...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    print(f"[ERROR] Backend connection failed after {max_retries} attempts")
                    return False
            except Exception as e:
                print(f"[ERROR] Error sending data: {e}")
                return False
        
        return False
    
    def get_sensor_unit(self, sensor_type):
        """Get unit for sensor type"""
        for sensor in self.all_sensors:
            if sensor["type"] == sensor_type:
                return sensor["unit"]
        return ""
    
    async def seed_historical_data(self):
        """Seed historical data for better dashboard experience"""
        print("[SEED] Seeding historical data...")
        
        # First, check if backend is available
        backend_ready = False
        for attempt in range(30):  # Increased to 30 attempts (60 seconds)
            try:
                response = requests.get(f"{self.api_url}/", timeout=3)
                if response.status_code == 200:
                    backend_ready = True
                    break
            except:
                pass
            if attempt < 10:  # Only show first 10 attempts to avoid spam
                print(f"[WAIT] Waiting for backend... attempt {attempt + 1}/30")
            await asyncio.sleep(2)
        
        if not backend_ready:
            print("[SKIP] Backend not ready, skipping historical data seeding")
            return
        
        print("[READY] Backend is ready, starting historical data seeding...")
        
        seeded_count = 0
        for day in range(min(self.historical_days, 7)):  # Limit to 7 days to avoid timeout
            base_time = datetime.now() - timedelta(days=self.historical_days - day)
            
            # Generate data for every 4 hours to reduce load
            for hour in range(0, 24, 4):
                timestamp = base_time + timedelta(hours=hour)
                
                # Generate data for a subset of sensors to reduce load
                for sensor in self.all_sensors[:10]:  # Only first 10 sensors
                    # Adjust start time for historical data
                    original_start = self.start_time
                    self.start_time = timestamp - timedelta(days=self.historical_days)
                    
                    value = self.generate_realistic_value(sensor)
                    
                    # Send historical data
                    data = {
                        "sensor_type": sensor["type"],
                        "value": value,
                        "timestamp": timestamp.isoformat()
                    }
                    
                    try:
                        response = requests.post(
                            f"{self.api_url}/data",
                            json=data,
                            headers={"Content-Type": "application/json"},
                            timeout=3
                        )
                        if response.status_code == 200:
                            seeded_count += 1
                    except:
                        pass  # Skip failed historical data
                    
                    # Restore original start time
                    self.start_time = original_start
                    
                    # Small delay to avoid overwhelming the API
                    await asyncio.sleep(0.05)
        
        print(f"[DONE] Seeded {seeded_count} historical data points")
    
    async def simulate_sensor(self, sensor):
        """Simulate a single sensor"""
        sensor_name = sensor["type"]
        consecutive_failures = 0
        max_failures = 10
        
        while True:
            try:
                value = self.generate_realistic_value(sensor)
                success = await self.send_data(sensor_name, value)
                
                if success:
                    consecutive_failures = 0
                    await asyncio.sleep(self.interval)
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        print(f"[WARN] Sensor {sensor_name} failed {max_failures} times, pausing for 30 seconds...")
                        await asyncio.sleep(30)
                        consecutive_failures = 0
                    else:
                        await asyncio.sleep(self.interval * 2)
                        
            except Exception as e:
                print(f"[ERROR] Sensor {sensor_name} error: {e}")
                await asyncio.sleep(self.interval * 3)
    
    async def run_simulation(self):
        """Run the complete simulation"""
        print("Starting Comprehensive Agriculture Data Simulation")
        print(f"API URL: {self.api_url}")
        print(f"Interval: {self.interval} seconds")
        print(f"Total Sensors: {len(self.all_sensors)}")
        print(f"Environmental: {len(self.environmental_sensors)}")
        print(f"Agricultural: {len(self.agricultural_sensors)}")
        print(f"Pest Detection: {len(self.pest_sensors)}")
        print(f"Harvest: {len(self.harvest_sensors)}")
        print(f"Marketplace: {len(self.marketplace_data)}")
        print(f"Analytics: {len(self.analytics_sensors)}")
        print("-" * 60)
        
        # Try to seed historical data, but don't fail if it doesn't work
        try:
            await self.seed_historical_data()
        except Exception as e:
            print(f"[WARN] Historical data seeding failed: {e}")
            print("[INFO] Continuing with real-time data generation...")
        
        print("Starting real-time data generation...")
        
        # Create tasks for all sensors
        tasks = []
        for sensor in self.all_sensors:
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
            # Try to keep individual sensors running even if one fails
            for task in tasks:
                try:
                    await task
                except:
                    pass

def main():
    """Main function to run the simulator"""
    simulator = ComprehensiveDataSimulator()
    
    try:
        asyncio.run(simulator.run_simulation())
    except KeyboardInterrupt:
        print("\nGoodbye!")

if __name__ == "__main__":
    print("Smart Agriculture Data Simulator")
    print("=" * 50)
    main()
