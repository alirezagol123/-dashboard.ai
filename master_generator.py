import asyncio
import subprocess
import sys
import time

class MasterDataGenerator:
    """Master script to run all individual feature generators"""
    
    def __init__(self):
        self.generators = [
            "environmental_generator.py",
            "agricultural_generator.py", 
            "pest_detection_generator.py",
            "harvest_generator.py",
            "marketplace_generator.py",
            "analytics_generator.py"
        ]
        self.processes = []
    
    def start_generator(self, script_name):
        """Start a single generator script"""
        try:
            print(f"Starting {script_name}...")
            process = subprocess.Popen([sys.executable, script_name])
            self.processes.append(process)
            print(f"✅ {script_name} started with PID {process.pid}")
            return process
        except Exception as e:
            print(f"❌ Failed to start {script_name}: {e}")
            return None
    
    def start_all_generators(self):
        """Start all feature generators"""
        print("🚀 Starting All Agriculture Feature Data Generators")
        print("=" * 60)
        
        for generator in self.generators:
            self.start_generator(generator)
            time.sleep(1)  # Small delay between starts
        
        print(f"\n✅ All {len(self.processes)} generators started!")
        print("\nGenerators running:")
        print("• Environmental: Temperature, Humidity, Pressure, Light, CO2, Wind, Rainfall, Soil Temp")
        print("• Agricultural: Soil Moisture, pH, N-P-K Levels, Water/Fertilizer Usage, Nutrient Uptake")
        print("• Pest Detection: Pest Detection, Disease Risk, Leaf Wetness, Pest Count")
        print("• Harvest: Plant Height, Leaf Count, Fruit Count, Fruit Size, Yield Prediction")
        print("• Marketplace: Tomato/Lettuce/Pepper Prices, Demand/Supply Levels")
        print("• Analytics: Energy Usage, Water/Yield Efficiency, Profit Margin, Cost per kg")
        print("\nPress Ctrl+C to stop all generators")
    
    def stop_all_generators(self):
        """Stop all running generators"""
        print("\n🛑 Stopping all generators...")
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ Generator {process.pid} stopped")
            except:
                try:
                    process.kill()
                    print(f"🔪 Generator {process.pid} force killed")
                except:
                    print(f"❌ Could not stop generator {process.pid}")
    
    def monitor_generators(self):
        """Monitor all generators and restart if needed"""
        while True:
            try:
                time.sleep(10)
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:  # Process has terminated
                        print(f"⚠️ Generator {self.generators[i]} stopped unexpectedly")
                        print(f"🔄 Restarting {self.generators[i]}...")
                        new_process = self.start_generator(self.generators[i])
                        if new_process:
                            self.processes[i] = new_process
            except KeyboardInterrupt:
                break
    
    def run(self):
        """Run the master generator"""
        try:
            self.start_all_generators()
            self.monitor_generators()
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
        finally:
            self.stop_all_generators()

if __name__ == "__main__":
    master = MasterDataGenerator()
    master.run()
