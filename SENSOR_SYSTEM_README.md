# 🚀 Smart Agriculture Sensor System

## Overview
A realistic IoT sensor data pipeline that simulates real-world sensor behavior with data validation and normalization.

## 🔄 Data Flow
```
Raw Sensors → Validation → Normalization → Clean Database → AI Analysis
```

## 📁 Files

### Core Components:
- **`raw_sensor_generator.py`** - Generates realistic raw sensor data with noise and bad data
- **`data_pipeline.py`** - Validates and normalizes raw data
- **`integrated_sensor_system.py`** - Complete integrated system
- **`run_sensor_system.py`** - Main script to run everything

### Test Scripts:
- **`test_pipeline.py`** - Test the data pipeline

## 🚀 How to Run

### Option 1: Complete Integrated System
```bash
python run_sensor_system.py
```
This runs the complete system:
- Generates raw sensor data
- Processes through validation pipeline
- Stores clean data in database

### Option 2: Test Pipeline Only
```bash
python test_pipeline.py
```
This tests the data pipeline with sample data.

### Option 3: Raw Data Generator Only
```bash
python raw_sensor_generator.py
```
This generates only raw sensor data (no processing).

## 📊 Database Tables

### `raw_sensor_data` (Raw, Unprocessed)
- All raw sensor data with noise and bad values
- Quality scores and validation flags
- Original units and formats

### `sensor_data` (Clean, Processed)
- Only validated and normalized data
- Standard units and formats
- Ready for AI analysis

## 🎯 What Happens

### 1. Raw Data Generation (15% bad data)
- ✅ **Good data**: Realistic values with sensor noise
- ❌ **Bad data**: Wrong units, extreme values, missing fields

### 2. Data Validation
- ✅ **Temperature**: -50°C to 70°C
- ✅ **Humidity**: 0% to 100%
- ✅ **Soil moisture**: 0% to 100%
- ✅ **Pest count**: ≥ 0
- ❌ **Rejects**: Out-of-range values, future timestamps

### 3. Data Normalization
- ✅ **Unit conversion**: F→C, km/h→m/s, inches→cm
- ✅ **Standard units**: C, %, ppm, hPa, kg
- ✅ **Decimal rounding**: 2 decimal places

### 4. Clean Database Storage
- ✅ **Only valid data** stored in `sensor_data` table
- ✅ **Quality tracking** and processing metadata
- ✅ **Ready for AI analysis**

## 🔧 Configuration

### Sensor Types (38 total):
- **Environmental**: temperature, humidity, pressure, light, co2_level, wind_speed, rainfall
- **Soil**: soil_moisture, soil_ph, soil_temperature
- **Plant Growth**: plant_height, fruit_count, fruit_size, leaf_count, leaf_wetness
- **Nutrients**: nitrogen_level, phosphorus_level, potassium_level, nutrient_uptake
- **Pest & Disease**: pest_count, pest_detection, disease_risk
- **Water**: water_usage, water_efficiency
- **Yield**: yield_prediction, yield_efficiency
- **Market**: tomato_price, lettuce_price, pepper_price, cost_per_kg, demand_level, supply_level, profit_margin
- **Additional**: motion, fertilizer_usage, energy_usage, test_temperature

## 📈 Statistics

The system tracks:
- **Raw data generated**
- **Validation success/failure**
- **Normalization results**
- **Processing statistics**
- **Data quality metrics**

## 🎯 Integration with AI

Your AI assistant will analyze the **clean data** from the `sensor_data` table, while the `raw_sensor_data` table shows realistic sensor behavior with noise and inconsistencies.

## 🚀 Next Steps

1. **Run the system**: `python run_sensor_system.py`
2. **Start your backend**: The AI will analyze clean data
3. **Open frontend**: See real-time sensor data
4. **Test AI chat**: Ask questions about sensor data

Your MVP now behaves like a real IoT system! 🎯
