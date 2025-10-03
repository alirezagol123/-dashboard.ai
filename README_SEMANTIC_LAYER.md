# 🧠 Unified Semantic Layer & AI Query Processing

## Overview

The Unified Semantic Layer is the core intelligence system of the Smart Agriculture Dashboard, providing comprehensive natural language query processing, intent detection, and AI-powered responses in both Persian and English. It integrates LangChain, OpenAI GPT-4o-mini, and a sophisticated ontology to deliver context-aware agricultural insights.

## 🏗️ Architecture

### Core Components

1. **UnifiedSemanticQueryService** (`app/services/unified_semantic_service.py`)
   - Main orchestrator for all query processing
   - Integrates LangChain SQLDatabaseChain for dynamic SQL generation
   - Handles Persian/English language detection and translation
   - Manages conversation history and session storage
   - Processes alert management queries

2. **IntentRouterLayer** (`app/services/intent_router_layer.py`)
   - Smart intent detection and routing system
   - Routes queries to appropriate handlers (data_query, alert_management, mixed)
   - Manages conversation memory and context
   - Handles dangerous query detection and validation

3. **LLMTranslator** (within UnifiedSemanticQueryService)
   - Persian-to-English query translation
   - English-to-Persian response translation
   - Language detection and validation
   - Cultural adaptation for agricultural terminology

4. **QueryBuilder** (`app/services/query_builder.py`)
   - Converts semantic JSON into SQL templates
   - Handles time-aware queries and aggregations
   - Supports comparison queries and complex analytics
   - Validates and optimizes SQL generation

5. **SQLValidator** (within UnifiedSemanticQueryService)
   - Validates SQL queries for safety and security
   - Prevents dangerous operations (DROP, DELETE, etc.)
   - Ensures only SELECT queries are allowed
   - Validates against allowed tables and columns

## 🎯 Key Features

### ✅ **Advanced Query Processing**

1. **Natural Language Understanding**
   - Handles arbitrary questions in Persian and English
   - Context-aware query generation based on feature context
   - Intelligent intent detection and routing
   - Conversation history integration

2. **Dynamic SQL Generation**
   - Uses LangChain SQLDatabaseChain for intelligent SQL generation
   - Time-aware queries with proper date/time handling
   - Aggregation support (AVG, MIN, MAX, COUNT, SUM)
   - Complex comparison queries across time periods

3. **Comprehensive Ontology**
   - **Environmental Sensors**: Temperature, humidity, pressure, light, CO2, wind, rainfall
   - **Agricultural Sensors**: Soil moisture, pH, N-P-K levels, water usage, fertilizer
   - **Pest Detection**: Pest count, disease risk, leaf wetness, detection confidence
   - **Harvest Management**: Plant height, fruit count, yield prediction
   - **Marketplace Data**: Crop prices, demand/supply levels
   - **Analytics**: Energy usage, efficiency metrics, profit margins

4. **Persian Language Support**
   - Complete Persian agricultural terminology
   - Cultural adaptation for Iranian farming practices
   - RTL text support and proper formatting
   - Persian response generation with structured bullet points

### ✅ **Smart Intent Detection**

1. **Query Classification**
   - `data_query`: Sensor data requests and analytics
   - `alert_management`: Alert creation, management, and monitoring
   - `mixed`: Combined data and reasoning queries

2. **Dangerous Query Prevention**
   - SQL injection protection
   - Dangerous operation blocking
   - Input validation and sanitization
   - Safe query execution

3. **Context-Aware Processing**
   - Feature-specific query handling (irrigation, environment, pest, dashboard)
   - Session-based conversation memory
   - User-specific alert management
   - Real-time data integration

## 🔄 Query Processing Flow

### **Step-by-Step Process:**

```
User Query (Persian/English)
    ↓
1. Language Detection
    ↓
2. Persian Translation (if needed)
    ↓
3. Intent Detection & Routing
    ↓
4. Feature Context Analysis
    ↓
5. SQL Generation (LangChain)
    ↓
6. Query Validation & Execution
    ↓
7. Data Processing & Analysis
    ↓
8. Response Generation
    ↓
9. Persian Translation (if needed)
    ↓
10. Structured Response Delivery
```

### **Example Flow:**
```
User: "دمای فعلی چقدر است؟" (What is the current temperature?)
    ↓
Language: Persian → English: "What is the current temperature?"
    ↓
Intent: data_query
    ↓
Feature: dashboard
    ↓
SQL: SELECT value FROM sensor_data WHERE sensor_type='temperature' ORDER BY timestamp DESC LIMIT 1
    ↓
Result: 23.7°C
    ↓
Response: "• دمای فعلی: 23.7 درجه سانتیگراد\n• وضعیت: مناسب\n• توصیه: دمای فعلی در محدوده مطلوب است"
```

## 🚀 API Endpoints

### **Core Query Processing**

#### `POST /ask`
Process natural language queries with full AI integration.

**Request:**
```json
{
  "query": "دمای فعلی چقدر است؟",
  "feature_context": "dashboard",
  "session_id": "user_123"
}
```

**Response:**
```json
{
  "success": true,
  "response": "• دمای فعلی: 23.7 درجه سانتیگراد\n• وضعیت: مناسب\n• توصیه: دمای فعلی در محدوده مطلوب است",
  "data": [
    {
      "sensor_type": "temperature",
      "value": 23.7,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  ],
  "sql": "SELECT value FROM sensor_data WHERE sensor_type='temperature' ORDER BY timestamp DESC LIMIT 1",
  "metrics": {
    "current_temperature": 23.7,
    "status": "optimal"
  },
  "detected_language": "fa",
  "detected_intent": "data_query"
}
```

#### `POST /ask/stream`
Streaming AI responses for real-time chat experience.

### **Alert Management Integration**

The semantic layer seamlessly integrates with the smart alerting system:

#### Alert Creation
```json
{
  "query": "وقتی دما بیشتر از 25 شد هشدار بده",
  "intent": "alert_management"
}
```

#### Alert Processing
- Natural language alert parsing
- Sensor type detection using ontology
- Threshold extraction and validation
- Persian response generation

## 🧪 Usage Examples

### **Environmental Queries**
- Persian: "دمای فعلی چقدر است؟" → "Current temperature: 23.7°C"
- English: "What is the humidity trend?" → "Humidity trend analysis with charts"

### **Agricultural Queries**
- Persian: "آبیاری امروز چطوره؟" → "Irrigation status: 45% soil moisture"
- English: "Show me soil pH levels" → "Soil pH analysis: 6.8 (optimal)"

### **Pest Detection Queries**
- Persian: "وضعیت آفات چطوره؟" → "Pest status: No active threats detected"
- English: "Any disease risks today?" → "Disease risk assessment: Low risk"

### **Analytics Queries**
- Persian: "مصرف آب این هفته چقدر است؟" → "Weekly water usage: 1,250 liters"
- English: "Show me yield predictions" → "Yield prediction: 2.3 tons expected"

## 🔧 Configuration

### **Environment Variables**
```env
# AI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
OPENAI_MODEL_NAME=openai/gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./smart_dashboard.db

# Session Management
SESSION_TIMEOUT_MINUTES=30
CONVERSATION_MEMORY_SIZE=10
```

### **Feature Context Mapping**
- `irrigation`: Soil moisture, water usage, rainfall sensors
- `environment`: Temperature, humidity, CO2, light sensors
- `pest`: Pest count, disease risk, leaf wetness sensors
- `dashboard`: Any sensor type (comprehensive view)

## 🛡️ Security Features

### **Query Validation**
1. **SQL Injection Prevention**
   - Only SELECT queries allowed
   - Dangerous keywords blocked
   - Parameterized query execution

2. **Input Sanitization**
   - Comprehensive input validation
   - XSS protection
   - SQL injection prevention

3. **Access Control**
   - Session-based user management
   - Feature-specific access control
   - Alert ownership validation

## 📊 Performance Optimization

### **Query Processing**
- Efficient SQL generation with LangChain
- Query result caching for repeated requests
- Optimized database queries with proper indexing
- Streaming responses for better UX

### **Memory Management**
- Conversation memory with configurable window size
- Session cleanup and garbage collection
- Efficient ontology storage and retrieval
- Minimal memory footprint for scalability

## 🔄 Integration Points

### **Backend Integration**
- Integrated into main FastAPI application
- Shared database connection with sensor data
- WebSocket integration for real-time updates
- Consistent error handling and logging

### **Frontend Integration**
- Available through LangChainChat component
- Real-time streaming responses
- Persian UI with RTL support
- Interactive query examples and suggestions

### **Alert System Integration**
- Seamless alert creation through natural language
- Real-time alert monitoring and processing
- Persian alert responses and recommendations
- Priority-based alert management

## 🧪 Testing

### **Query Testing**
```bash
# Test Persian query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "دمای فعلی چقدر است؟", "feature_context": "dashboard"}'

# Test English query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current humidity?", "feature_context": "environment"}'

# Test alert creation
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "وقتی دما بیشتر از 25 شد هشدار بده", "feature_context": "dashboard"}'
```

### **Health Checks**
```bash
# Semantic layer health
curl http://localhost:8000/semantic/health

# AI service health
curl http://localhost:8000/ai/health
```

## 🚀 Future Enhancements

### **Advanced Features**
1. **Machine Learning Integration**
   - Query pattern learning
   - User behavior analysis
   - Predictive query suggestions
   - Automated insight generation

2. **Extended Language Support**
   - Additional language support
   - Regional dialect handling
   - Context-aware translation
   - Multi-language ontology

3. **Advanced Analytics**
   - Query usage analytics
   - Performance metrics
   - User engagement tracking
   - Automated reporting

4. **API Expansion**
   - GraphQL support
   - RESTful API enhancements
   - Real-time query streaming
   - Webhook integrations

## 🛠️ Troubleshooting

### **Common Issues**

1. **Query Not Recognized**
   - Check query format and keywords
   - Use sample queries as reference
   - Verify language detection
   - Check feature context

2. **Translation Issues**
   - Check Persian character encoding
   - Verify translation mappings
   - Test with simple queries first
   - Ensure proper UTF-8 encoding

3. **Performance Issues**
   - Monitor query processing time
   - Check database connectivity
   - Review pattern matching efficiency
   - Optimize conversation memory

4. **Alert Integration Issues**
   - Verify alert manager initialization
   - Check alert database connectivity
   - Test alert creation flow
   - Monitor alert processing logs

### **Debug Mode**
Enable debug logging for detailed query processing:
```python
import logging
logging.getLogger('unified_semantic_service').setLevel(logging.DEBUG)
logging.getLogger('intent_router_layer').setLevel(logging.DEBUG)
```

## 📈 Monitoring & Analytics

### **Key Metrics**
- Query processing time
- Language detection accuracy
- SQL generation success rate
- Alert creation success rate
- User engagement metrics

### **Logging**
- Comprehensive query processing logs
- Error tracking and monitoring
- Performance metrics collection
- User behavior analytics

---

**🧠 The Unified Semantic Layer powers the intelligent core of the Smart Agriculture Dashboard, enabling natural language interaction with complex agricultural data through advanced AI and comprehensive ontology mapping.**