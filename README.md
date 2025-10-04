# 🌱 Smart Agriculture Dashboard

A comprehensive, AI-powered agriculture monitoring and management platform with real-time sensor data, intelligent analytics, and Persian language support.

## 🎯 Project Overview

The Smart Agriculture Dashboard is a full-stack application that provides:

- **Real-time Sensor Monitoring**: Live data from environmental, agricultural, and pest detection sensors
- **AI-Powered Analytics**: LangChain-based natural language query processing in Persian and English
- **Smart Alerting System**: Intelligent alerts with recommended actions and Act/Pass options
- **Comprehensive Dashboard**: Multi-tab interface for different agricultural aspects
- **Persian Language Support**: Complete UI and AI responses in Persian

## 🏗️ Architecture

```
┌─────────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Data Generators    │───▶│   FastAPI       │───▶│   SQLite DB     │
│  (Environmental,    │    │   Backend       │    │   (Sensor Data) │
│   Agricultural,     │    │   + LangChain   │    │                 │
│   Pest Detection)   │    │   + AI Assistant│    │                 │
└─────────────────────┘    └─────────────────┘    └─────────────────┘
                                      │                       │
                                      ▼                       ▼
                           ┌─────────────────┐    ┌─────────────────┐
                           │   React         │◀───│   WebSocket     │
                           │   Frontend      │    │   Real-time     │
                           │   (Dashboard)   │    │   Streaming     │
                           └─────────────────┘    └─────────────────┘
```

## ✨ Key Features

### 🤖 **AI Assistant with Persian Support**
- **Natural Language Queries**: Ask questions in Persian or English
- **Smart Intent Detection**: Automatically routes queries to appropriate handlers
- **Real-time Data Integration**: Uses live sensor data for responses
- **Structured Responses**: Persian responses with bullet points and metrics

### 🚨 **Smart Alerting System**
- **AI-Powered Alerts**: Create alerts using natural language
- **Persian Interface**: Complete UI in Persian
- **Recommended Actions**: Context-specific recommendations with Act/Pass options
- **Real-time Monitoring**: Continuous monitoring with sound alerts
- **Priority Management**: Horizontal alert cards with inline actions

### 📊 **Comprehensive Dashboard**
- **Environmental Monitoring**: Temperature, humidity, pressure, light, CO2
- **Agricultural Sensors**: Soil moisture, pH, N-P-K levels, water usage
- **Pest Detection**: Pest count, disease risk, leaf wetness
- **Harvest Management**: Plant height, fruit count, yield prediction
- **Marketplace Data**: Crop prices, demand/supply analysis
- **Analytics**: Energy usage, efficiency metrics, profit margins

### 🌐 **Multi-language Support**
- **Persian UI**: Complete interface in Persian
- **Bilingual AI**: Responds in user's language
- **RTL Support**: Right-to-left text layout
- **Cultural Adaptation**: Persian agricultural terminology

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: SQLite (with PostgreSQL support)
- **AI/ML**: LangChain + OpenAI GPT-4o-mini
- **ORM**: SQLAlchemy
- **Real-time**: WebSocket
- **Language**: Python 3.8+

### Frontend
- **Framework**: React.js (Vite)
- **Styling**: TailwindCSS
- **Charts**: Chart.js, Recharts
- **Icons**: Lucide React
- **State Management**: React Hooks
- **Language**: JavaScript/JSX

### AI & Analytics
- **LLM**: OpenAI GPT-4o-mini (custom API endpoint)
- **Orchestration**: LangChain
- **Translation**: Built-in Persian/English translator
- **Query Processing**: Dynamic SQL generation
- **Intent Detection**: Smart routing system

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smart-agriculture-dashboard
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   cd frontend
   npm install
   cd ..
   ```

4. **Set up environment variables**
   ```bash
   # Copy the example file
   cp env.example .env
   
   # Edit .env with your configuration
   # OPENAI_API_KEY=your-api-key
   # OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
   # OPENAI_MODEL_NAME=openai/gpt-4o-mini
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   python start_server.py
   ```

2. **Start the frontend (in a new terminal)**
   ```bash
   cd frontend
   npm run dev
   ```

3. **Access the application**
   - 🌐 **Frontend**: http://localhost:3000
   - 🔌 **Backend API**: http://localhost:8000
   - 📚 **API Docs**: http://localhost:8000/docs

## 📁 Project Structure

```
smart-agriculture-dashboard/
├── app/                          # FastAPI Backend
│   ├── db/                      # Database configuration
│   │   └── database.py
│   ├── models/                  # SQLAlchemy models
│   │   ├── schemas.py
│   │   └── sensor_data.py
│   ├── services/                # Business logic
│   │   ├── ai_assistant.py
│   │   ├── alert_manager.py     # Smart alerting system
│   │   ├── alert_monitor.py     # Alert monitoring
│   │   ├── data_service.py
│   │   ├── intent_router_layer.py
│   │   ├── langchain_service.py
│   │   ├── query_builder.py
│   │   ├── session_storage.py
│   │   ├── unified_semantic_service.py
│   │   └── websocket_manager.py
│   ├── ai_assistant_api.py
│   ├── graphql_schema.py
│   └── main.py                  # FastAPI application
├── frontend/                    # React Frontend
│   ├── src/
│   │   ├── components/          # React components
│   │   │   ├── AlertsManager.jsx    # Smart alerts UI
│   │   │   ├── Chart.jsx
│   │   │   ├── DataVisualizer.jsx
│   │   │   ├── LangChainChat.jsx    # AI chat interface
│   │   │   ├── QueryAssistant.jsx
│   │   │   └── StatsCard.jsx
│   │   ├── pages/
│   │   │   └── Dashboard.jsx    # Main dashboard
│   │   ├── services/            # API services
│   │   │   ├── api.js
│   │   │   └── ws.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── data-simulator/              # Data generation
│   ├── simulator.py
│   └── simple_simulator.py
├── database/                    # Database schema
│   └── schema.sql
├── generators/                  # Individual data generators
│   ├── environmental_generator.py
│   ├── agricultural_generator.py
│   ├── pest_detection_generator.py
│   ├── harvest_generator.py
│   ├── marketplace_generator.py
│   └── analytics_generator.py
├── start_server.py              # Main startup script
├── requirements.txt
├── package.json
└── README.md
```

## 🎯 Core Features

### 1. **AI Assistant (LangChain Integration)**
- **Natural Language Processing**: Ask questions in Persian or English
- **Smart Intent Detection**: Automatically routes queries to appropriate handlers
- **Real-time Data Integration**: Uses live sensor data for context-aware responses
- **Structured Responses**: Persian responses with bullet points and metrics

**Example Queries:**
- Persian: "دمای فعلی چقدر است؟" (What is the current temperature?)
- English: "Show me the humidity trend for today"
- Persian: "آبیاری امروز چطوره؟" (How is irrigation today?)

### 2. **Smart Alerting System**
- **Natural Language Alert Creation**: Create alerts using simple commands
- **Persian Interface**: Complete UI in Persian
- **Recommended Actions**: Context-specific recommendations with Act/Pass options
- **Real-time Monitoring**: Continuous monitoring with sound alerts
- **Priority Management**: Horizontal alert cards with inline actions

**Alert Examples:**
- Persian: "وقتی دما بیشتر از 25 شد هشدار بده" (Alert when temperature > 25°C)
- English: "Alert me when soil moisture drops below 40%"

### 3. **Comprehensive Dashboard Tabs**

#### 🌍 **Environmental Monitoring**
- Temperature, humidity, pressure monitoring
- Light levels and CO2 tracking
- Weather conditions (wind, rainfall)
- Soil temperature monitoring

#### 💧 **Irrigation Management**
- Soil moisture levels
- Water usage tracking
- Irrigation scheduling
- Efficiency monitoring

#### 🐛 **Pest Detection**
- Pest detection alerts
- Disease risk assessment
- Leaf wetness monitoring
- Treatment recommendations

#### 🌾 **Fertilization**
- Soil pH analysis
- N-P-K nutrient levels
- Fertilizer usage tracking
- AI recommendations

#### 📅 **Harvest Management**
- Plant growth tracking
- Fruit development monitoring
- Yield predictions
- Harvest scheduling

#### 🛒 **Marketplace**
- Crop price tracking
- Demand/supply analysis
- Market trends
- Profit calculations

#### 📈 **Analytics**
- Performance metrics
- Efficiency analysis
- Cost-benefit analysis
- Report generation

## 🔧 Configuration

### Environment Variables
```env
# AI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
OPENAI_MODEL_NAME=openai/gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./smart_dashboard.db

# Server
HOST=0.0.0.0
PORT=8000
```

### Data Generation
The system includes multiple data generators for realistic simulation:
- **Environmental**: Temperature, humidity, pressure, light, CO2
- **Agricultural**: Soil moisture, pH, N-P-K levels, water usage
- **Pest Detection**: Pest count, disease risk, leaf wetness
- **Harvest**: Plant height, fruit count, yield prediction
- **Marketplace**: Crop prices, demand/supply levels
- **Analytics**: Energy usage, efficiency metrics

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `GET /data/latest` - Get latest sensor data
- `GET /data/stats` - Get data statistics
- `POST /data` - Submit sensor data
- `WebSocket /ws` - Real-time data streaming

### AI Assistant
- `POST /ask` - Process natural language queries
- `POST /ask/stream` - Streaming AI responses
- `GET /ai/health` - AI service health check

### Smart Alerts
- `GET /api/alerts` - Get all alerts
- `POST /api/alerts` - Create new alert
- `DELETE /api/alerts/{id}` - Delete alert
- `GET /api/alerts/monitor` - Monitor triggered alerts

## 🧪 Testing

### Backend Tests
```bash
# Health check
curl http://localhost:8000/health

# AI query test
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "دمای فعلی چقدر است؟"}'

# Alert creation test
curl -X POST http://localhost:8000/api/alerts \
  -H "Content-Type: application/json" \
  -d '{"query": "وقتی دما بیشتر از 25 شد هشدار بده"}'
```

### Frontend Tests
1. Navigate to http://localhost:3000
2. Test AI chat in Persian and English
3. Create alerts using natural language
4. Verify real-time data updates
5. Test alert monitoring and actions

## 🚀 Deployment

### Development
```bash
# Start backend
python start_server.py

# Start frontend
cd frontend && npm run dev
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Start backend (serves both API and frontend)
python start_server.py
```

## 📈 Performance

- **Real-time Updates**: WebSocket for live data streaming
- **Efficient Queries**: Optimized SQL with proper indexing
- **Caching**: Smart caching for frequently accessed data
- **Responsive UI**: Mobile-friendly interface with TailwindCSS
- **AI Optimization**: Efficient LLM integration with context management

## 🔒 Security

- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Safe query execution
- **CORS**: Proper cross-origin resource sharing
- **Error Handling**: Graceful error responses without sensitive data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See individual README files for specific features
- **Issues**: [GitHub Issues](https://github.com/your-org/smart-agriculture-dashboard/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/smart-agriculture-dashboard/discussions)

## 🗺️ Roadmap

### Current Version (v1.0)
- ✅ Real-time sensor monitoring
- ✅ AI-powered natural language queries
- ✅ Smart alerting system with Persian support
- ✅ Comprehensive dashboard with multiple tabs
- ✅ WebSocket real-time updates

### Future Versions
- [ ] Mobile application
- [ ] Advanced ML models for prediction
- [ ] Multi-tenant support
- [ ] Advanced analytics and reporting
- [ ] Integration with IoT devices

---

**Built with ❤️ by the Smart Agriculture Dashboard Team**

*Empowering farmers with AI-driven insights and real-time monitoring*#   W e b h o o k   T e s t   -   1 0 / 0 4 / 2 0 2 5   0 9 : 3 1 : 5 1  
 