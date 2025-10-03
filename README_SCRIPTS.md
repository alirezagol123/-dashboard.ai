# 🌱 Smart Agriculture Dashboard - Data Generation Scripts

## Overview

This directory contains comprehensive data generation scripts for the Smart Agriculture Dashboard, providing realistic sensor data simulation for all agricultural monitoring features. Each script generates specific types of sensor data with realistic patterns, cycles, and agricultural behaviors.

## 🏗️ Architecture

### **Data Generation System**

```
┌─────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Individual         │───▶│   FastAPI       │───▶│   SQLite DB     │
│  Generators         │    │   Backend       │    │   (Sensor Data) │
│  (Environmental,    │    │   + WebSocket   │    │                 │
│   Agricultural,     │    │   + Real-time   │    │                 │
│   Pest Detection)   │    │   Streaming     │    │                 │
└─────────────────────┘    └─────────────────┘    └─────────────────┘
                                      │                       │
                                      ▼                       ▼
                           ┌─────────────────┐    ┌─────────────────┐
                           │   React         │◀───│   WebSocket     │
                           │   Frontend      │    │   Real-time     │
                           │   (Dashboard)   │    │   Updates       │
                           └─────────────────┘    └─────────────────┘
```

## 📁 Available Scripts

### 🏗️ **Core Scripts**

#### `start_server.py` - **Main Server Starter**
- **Purpose**: Primary startup script for the entire application
- **Features**: 
  - Sets environment variables for AI integration
  - Starts FastAPI backend with WebSocket support
  - Configures logging and error handling
  - Runs on port 8000 with auto-reload

#### `master_generator.py` - **Master Data Generator**
- **Purpose**: Runs all individual generators simultaneously
- **Features**:
  - Coordinates all data generation scripts
  - Manages generator lifecycle
  - Provides centralized control
  - Error handling and recovery

#### `feature_data_generator.py` - **Comprehensive Generator**
- **Purpose**: Single script for all agricultural features
- **Features**:
  - All sensor types in one generator
  - Coordinated data generation
  - Realistic agricultural patterns
  - Efficient resource usage

### 🌍 **Environmental Monitoring**

#### `environmental_generator.py`
- **Sensors**: 8 environmental sensors
- **Interval**: 3 seconds
- **Features**: Realistic daily cycles, weather patterns

**Generated Data:**
- **Temperature**: Daily cycle (15°C-35°C) with seasonal variation
- **Humidity**: Inverse correlation with temperature (30%-80%)
- **Pressure**: Atmospheric pressure with weather patterns
- **Light**: Daylight cycle with cloud cover simulation
- **CO2 Level**: Plant respiration patterns (300-800 ppm)
- **Wind Speed**: Variable wind patterns (0-25 km/h)
- **Rainfall**: Precipitation events and accumulation
- **Soil Temperature**: Ground temperature with thermal lag

**Patterns:**
- Daily temperature cycles (cooler at night, warmer during day)
- Humidity inversely correlated with temperature
- Light intensity follows sun position
- CO2 levels affected by plant activity
- Weather events (rain, wind) with realistic timing

### 🌾 **Agricultural Sensors**

#### `agricultural_generator.py`
- **Sensors**: 8 agricultural sensors
- **Interval**: 4 seconds
- **Features**: Irrigation cycles, fertilizer applications, soil health

**Generated Data:**
- **Soil Moisture**: Irrigation events and natural drying (20%-80%)
- **Soil pH**: Gradual changes with fertilizer applications (5.5-7.5)
- **Nitrogen Level**: Plant uptake and fertilizer replenishment
- **Phosphorus Level**: Nutrient cycling and plant consumption
- **Potassium Level**: Soil nutrient dynamics
- **Water Usage**: Irrigation system consumption
- **Fertilizer Usage**: Application events and consumption
- **Nutrient Uptake**: Plant absorption rates

**Patterns:**
- Irrigation events cause moisture spikes
- Fertilizer applications affect nutrient levels
- Plant growth affects nutrient uptake
- Seasonal variations in water usage
- Soil health indicators

### 🐛 **Pest Detection**

#### `pest_detection_generator.py`
- **Sensors**: 4 pest detection sensors
- **Interval**: 5 seconds
- **Features**: Pest outbreaks, disease risk, treatment events

**Generated Data:**
- **Pest Count**: Pest population dynamics (0-50 pests)
- **Pest Detection**: Detection confidence and accuracy
- **Disease Risk**: Risk assessment based on conditions (0-100%)
- **Leaf Wetness**: Moisture on plant surfaces (0-100%)

**Patterns:**
- Pest outbreaks with seasonal patterns
- Disease risk correlated with humidity and temperature
- Leaf wetness affects disease development
- Treatment events reduce pest counts
- Environmental factors influence pest activity

### 🌿 **Harvest Management**

#### `harvest_generator.py`
- **Sensors**: 5 harvest sensors
- **Interval**: 6 seconds
- **Features**: Plant growth cycles, yield predictions, harvest timing

**Generated Data:**
- **Plant Height**: Growth progression (10-200 cm)
- **Leaf Count**: Foliage development (5-50 leaves)
- **Fruit Count**: Fruit development and maturation (0-100 fruits)
- **Fruit Size**: Size progression and maturity (1-15 cm)
- **Yield Prediction**: Expected harvest based on current data

**Patterns:**
- Exponential growth curves for plant height
- Leaf count increases with plant maturity
- Fruit development follows growth stages
- Yield predictions based on current metrics
- Harvest timing optimization

### 🛒 **Marketplace Data**

#### `marketplace_generator.py`
- **Sensors**: 5 marketplace sensors
- **Interval**: 10 seconds
- **Features**: Price fluctuations, demand/supply dynamics

**Generated Data:**
- **Tomato Price**: Market price per kilogram (15-45 Toman/kg)
- **Lettuce Price**: Leafy green pricing (8-25 Toman/kg)
- **Pepper Price**: Vegetable pricing (20-60 Toman/kg)
- **Demand Level**: Market demand (0-100%)
- **Supply Level**: Available supply (0-100%)

**Patterns:**
- Price fluctuations based on demand/supply
- Seasonal price variations
- Market trends and cycles
- Supply chain effects
- Economic indicators

### 📊 **Analytics**

#### `analytics_generator.py`
- **Sensors**: 5 analytics sensors
- **Interval**: 8 seconds
- **Features**: Performance metrics, efficiency tracking, cost analysis

**Generated Data:**
- **Energy Usage**: Power consumption (50-500 kWh)
- **Water Efficiency**: Irrigation efficiency (60-95%)
- **Yield Efficiency**: Production efficiency (70-95%)
- **Profit Margin**: Financial performance (10-40%)
- **Cost per kg**: Production cost analysis (5-25 Toman/kg)

**Patterns:**
- Efficiency improvements over time
- Cost optimization trends
- Performance metrics correlation
- Resource utilization analysis
- Profitability indicators

## 🚀 **Quick Start**

### **Option 1: Start Everything (Recommended)**
```bash
# Start the complete system
python start_server.py

# In another terminal, start frontend
cd frontend
npm run dev
```

### **Option 2: Start Individual Generators**
```bash
# Start specific generators
python environmental_generator.py
python agricultural_generator.py
python pest_detection_generator.py
python harvest_generator.py
python marketplace_generator.py
python analytics_generator.py
```

### **Option 3: Start All Generators Together**
```bash
python master_generator.py
```

## 🌐 **Access Points**

- **Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health
- **Latest Data**: http://localhost:8000/data/latest?limit=20
- **Data Statistics**: http://localhost:8000/data/stats
- **WebSocket**: ws://localhost:8000/ws

## 📊 **Dashboard Features**

### 🎯 **Main Dashboard**
- Real-time sensor data visualization
- WebSocket connection status
- Statistics cards for all sensor types
- Interactive charts and graphs
- Persian language support

### 🌍 **Environmental Tab**
- Temperature, humidity, pressure monitoring
- Light levels and CO2 tracking
- Weather conditions (wind, rainfall)
- Soil temperature monitoring
- Real-time environmental alerts

### 💧 **Irrigation Tab**
- Soil moisture levels
- Water usage tracking
- Irrigation scheduling
- Efficiency monitoring
- Water conservation analytics

### 🐛 **Pest Detection Tab**
- Pest detection alerts
- Disease risk assessment
- Leaf wetness monitoring
- Treatment recommendations
- Prevention strategies

### 🌾 **Fertilization Tab**
- Soil pH analysis
- N-P-K nutrient levels
- Fertilizer usage tracking
- AI recommendations
- Nutrient balance monitoring

### 📅 **Harvest Tab**
- Plant growth tracking
- Fruit development monitoring
- Yield predictions
- Harvest scheduling
- Growth analytics

### 🛒 **Marketplace Tab**
- Crop price tracking
- Demand/supply analysis
- Market trends
- Profit calculations
- Economic forecasting

### 📈 **Analytics Tab**
- Performance metrics
- Efficiency analysis
- Cost-benefit analysis
- Report generation
- KPI monitoring

### 🤖 **AI Assist Tab**
- LangChain-powered chat
- Natural language queries
- Data analysis
- Insights and recommendations
- Persian language support

### 🚨 **Alerts Tab**
- Smart alerting system
- Natural language alert creation
- Real-time monitoring
- Recommended actions with Act/Pass options
- Persian interface

## 🔧 **Technical Details**

### **Data Generation Patterns**

#### **Daily Cycles**
- **Temperature**: Cooler at night (15°C), warmer during day (35°C)
- **Humidity**: Inverse correlation with temperature
- **Light**: Follows sun position with cloud cover simulation
- **CO2**: Plant respiration patterns

#### **Event-Based**
- **Pest Detection**: Random outbreaks with seasonal patterns
- **Irrigation**: Scheduled events with soil moisture triggers
- **Fertilization**: Periodic applications based on nutrient levels
- **Harvest**: Growth stage-based timing

#### **Growth Cycles**
- **Plant Height**: Exponential growth curves
- **Fruit Development**: Maturation stages
- **Yield Prediction**: Based on current metrics
- **Harvest Timing**: Optimization algorithms

#### **Market Fluctuation**
- **Price Changes**: Based on demand/supply dynamics
- **Seasonal Variations**: Crop-specific patterns
- **Market Trends**: Long-term price movements
- **Supply Chain**: Distribution effects

#### **Efficiency Tracking**
- **Performance Metrics**: Continuous improvement
- **Cost Optimization**: Resource utilization
- **Efficiency Gains**: Learning algorithms
- **Profitability**: Financial indicators

### **API Endpoints**

#### **Data Management**
- `POST /data` - Send sensor data
- `GET /data/latest` - Get recent data
- `GET /data/stats` - Get statistics
- `GET /data/types` - Get sensor types
- `GET /data/range` - Get data in time range

#### **Real-time Communication**
- `WebSocket /ws` - Real-time data stream
- `WebSocket /ws/data` - Sensor data updates
- `WebSocket /ws/alerts` - Alert notifications

#### **AI Integration**
- `POST /ask` - AI chat queries
- `POST /ask/stream` - Streaming AI responses
- `GET /ai/health` - AI service health

#### **Alert Management**
- `GET /api/alerts` - Get all alerts
- `POST /api/alerts` - Create new alert
- `DELETE /api/alerts/{id}` - Delete alert
- `GET /api/alerts/monitor` - Monitor triggered alerts

### **WebSocket Integration**
- Real-time data streaming
- Automatic reconnection
- Connection status monitoring
- Fallback to polling if WebSocket fails
- Persian language support

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **WebSocket Connection Failed**
   - Check if backend is running on port 8000
   - Verify WebSocket endpoint accessibility
   - Check firewall settings

2. **No Data Showing**
   - Verify data generators are running
   - Check database connectivity
   - Monitor generator logs

3. **Frontend Not Loading**
   - Check if React dev server is running on port 3000
   - Verify frontend dependencies
   - Check for JavaScript errors

4. **API Errors**
   - Check backend logs for errors
   - Verify database connection
   - Check environment variables

5. **AI Chat Not Working**
   - Verify OpenAI API key configuration
   - Check API endpoint accessibility
   - Monitor AI service logs

### **Debug Commands**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check recent data
curl http://localhost:8000/data/latest?limit=5

# Check WebSocket connection
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Key: test" -H "Sec-WebSocket-Version: 13" http://localhost:8000/ws

# Check running processes
netstat -an | findstr :8000
netstat -an | findstr :3000
```

### **Log Monitoring**
```bash
# Monitor backend logs
tail -f logs/backend.log

# Monitor generator logs
tail -f logs/generators.log

# Monitor AI service logs
tail -f logs/ai_service.log
```

## 🎯 **Next Steps**

1. **Open Dashboard**: Go to http://localhost:3000
2. **Explore Features**: Click through different tabs
3. **Test AI Chat**: Try asking questions in the AI Assist tab
4. **Create Alerts**: Use natural language to create alerts
5. **Monitor Data**: Watch real-time data updates
6. **Customize**: Modify generators for your specific needs

## 🔧 **Customization**

### **Modifying Generators**
- Edit sensor ranges and patterns
- Adjust generation intervals
- Add new sensor types
- Modify agricultural behaviors

### **Adding New Sensors**
1. Update generator script
2. Add sensor type to database schema
3. Update frontend components
4. Test data flow

### **Configuring Patterns**
- Modify daily cycles
- Adjust seasonal variations
- Change event frequencies
- Update growth curves

---

**🎉 The Smart Agriculture Dashboard Data Generation System provides comprehensive, realistic sensor data simulation for all agricultural monitoring features, enabling thorough testing and demonstration of the platform's capabilities!**