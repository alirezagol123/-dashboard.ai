# 🔄 Dynamic AI-Powered Query System

## Overview

The Dynamic Query System is the intelligent query processing engine of the Smart Agriculture Dashboard, providing LLM-powered SQL generation, natural language understanding, and real-time data analysis. It enables users to ask complex questions in Persian or English and receive structured responses with generated SQL queries and comprehensive analytics.

## 🏗️ Architecture

### Core Components

1. **UnifiedSemanticQueryService** (`app/services/unified_semantic_service.py`)
   - Main orchestrator for dynamic query processing
   - Integrates LangChain SQLDatabaseChain for intelligent SQL generation
   - Handles Persian/English language detection and translation
   - Manages conversation history and session storage
   - Processes complex agricultural queries

2. **IntentRouterLayer** (`app/services/intent_router_layer.py`)
   - Smart intent detection and query routing
   - Routes queries to appropriate handlers (data_query, alert_management, mixed)
   - Manages conversation memory and context
   - Handles dangerous query detection and validation

3. **QueryBuilder** (`app/services/query_builder.py`)
   - Converts semantic JSON into optimized SQL templates
   - Handles time-aware queries and complex aggregations
   - Supports comparison queries across different time periods
   - Validates and optimizes SQL generation

4. **LLMTranslator** (within UnifiedSemanticQueryService)
   - Persian-to-English query translation using GPT-4o-mini
   - English-to-Persian response translation
   - Language detection and validation
   - Cultural adaptation for agricultural terminology

5. **SQLValidator** (within UnifiedSemanticQueryService)
   - Validates SQL queries for safety and security
   - Prevents dangerous operations (DROP, DELETE, UPDATE, etc.)
   - Ensures only SELECT queries are allowed
   - Validates against allowed tables and columns

## 🎯 Key Features

### ✅ **Advanced Query Processing**

1. **Natural Language Understanding**
   - Handles arbitrary questions in Persian and English
   - Context-aware query generation based on feature context
   - Intelligent intent detection and routing
   - Conversation history integration for context

2. **Dynamic SQL Generation**
   - Uses LangChain SQLDatabaseChain for intelligent SQL generation
   - Time-aware queries with proper date/time handling
   - Complex aggregation support (AVG, MIN, MAX, COUNT, SUM, STDDEV)
   - Comparison queries across different time periods
   - Chart data generation for visualizations

3. **Comprehensive Data Support**
   - **Environmental Data**: Temperature, humidity, pressure, light, CO2, wind, rainfall
   - **Agricultural Data**: Soil moisture, pH, N-P-K levels, water usage, fertilizer
   - **Pest Detection**: Pest count, disease risk, leaf wetness, detection confidence
   - **Harvest Data**: Plant height, fruit count, yield prediction, growth metrics
   - **Marketplace Data**: Crop prices, demand/supply levels, market trends
   - **Analytics Data**: Energy usage, efficiency metrics, profit margins

4. **Persian Language Support**
   - Complete Persian agricultural terminology
   - Cultural adaptation for Iranian farming practices
   - RTL text support and proper formatting
   - Persian response generation with structured bullet points

### ✅ **Smart Query Routing**

1. **Intent Detection**
   - `data_query`: Sensor data requests and analytics
   - `alert_management`: Alert creation, management, and monitoring
   - `mixed`: Combined data and reasoning queries

2. **Feature Context Awareness**
   - `irrigation`: Focuses on soil moisture, water usage, rainfall
   - `environment`: Focuses on temperature, humidity, CO2, light
   - `pest`: Focuses on pest count, disease risk, leaf wetness
   - `dashboard`: Uses any sensor type for comprehensive analysis

3. **Query Validation & Security**
   - SQL injection prevention
   - Dangerous operation blocking
   - Input validation and sanitization
   - Safe query execution with proper error handling

## 🔄 Query Processing Flow

### **Complete Processing Pipeline:**

```
User Query (Persian/English)
    ↓
1. Language Detection & Translation
    ↓
2. Intent Detection & Routing
    ↓
3. Feature Context Analysis
    ↓
4. Conversation History Integration
    ↓
5. Semantic JSON Generation
    ↓
6. SQL Generation (LangChain)
    ↓
7. Query Validation & Execution
    ↓
8. Data Processing & Analysis
    ↓
9. Metrics Extraction
    ↓
10. Chart Data Generation
    ↓
11. Response Generation
    ↓
12. Persian Translation (if needed)
    ↓
13. Structured Response Delivery
```

### **Example Processing:**

```
User: "دمای این هفته چطور بوده؟" (How has the temperature been this week?)
    ↓
Language: Persian → English: "How has the temperature been this week?"
    ↓
Intent: data_query
    ↓
Feature: environment
    ↓
Semantic JSON: {
  "entity": "temperature",
  "aggregation": "average",
  "time_range": "last_7_days",
  "grouping": "by_day"
}
    ↓
SQL: SELECT DATE(timestamp) as date, AVG(value) as avg_temp 
     FROM sensor_data 
     WHERE sensor_type='temperature' 
     AND timestamp >= datetime('now', '-7 days')
     GROUP BY DATE(timestamp)
    ↓
Result: [{"date": "2024-01-08", "avg_temp": 22.3}, ...]
    ↓
Response: "• میانگین دما این هفته: 23.1 درجه سانتیگراد\n• روند: افزایش 2.3 درجه نسبت به هفته قبل\n• توصیه: دمای مناسب برای رشد گیاهان"
```

## 🚀 API Endpoints

### **Core Query Processing**

#### `POST /ask`
Process natural language queries with full AI integration.

**Request:**
```json
{
  "query": "دمای این هفته چطور بوده؟",
  "feature_context": "environment",
  "session_id": "user_123"
}
```

**Response:**
```json
{
  "success": true,
  "response": "• میانگین دما این هفته: 23.1 درجه سانتیگراد\n• روند: افزایش 2.3 درجه نسبت به هفته قبل\n• توصیه: دمای مناسب برای رشد گیاهان",
  "data": [
    {
      "date": "2024-01-08",
      "avg_temp": 22.3,
      "sensor_type": "temperature"
    },
    {
      "date": "2024-01-09", 
      "avg_temp": 23.8,
      "sensor_type": "temperature"
    }
  ],
  "sql": "SELECT DATE(timestamp) as date, AVG(value) as avg_temp FROM sensor_data WHERE sensor_type='temperature' AND timestamp >= datetime('now', '-7 days') GROUP BY DATE(timestamp)",
  "metrics": {
    "weekly_average": 23.1,
    "trend": "increasing",
    "change_from_previous": 2.3
  },
  "chart": {
    "type": "line",
    "data": [...],
    "options": {...}
  },
  "detected_language": "fa",
  "detected_intent": "data_query"
}
```

#### `POST /ask/stream`
Streaming AI responses for real-time chat experience.

**Request:**
```json
{
  "query": "رطوبت خاک امروز چطوره؟",
  "feature_context": "irrigation"
}
```

**Response (Streaming):**
```
data: {"step": 1, "message": "Processing query...", "progress": 20}
data: {"step": 2, "message": "Generating SQL...", "progress": 40}
data: {"step": 3, "message": "Executing query...", "progress": 60}
data: {"step": 4, "message": "Analyzing results...", "progress": 80}
data: {"step": "complete", "result": {...}, "progress": 100}
data: [DONE]
```

### **Query Health & Status**

#### `GET /ai/health`
Check AI service health and configuration.

**Response:**
```json
{
  "status": "healthy",
  "llm_available": true,
  "model": "openai/gpt-4o-mini",
  "api_base": "https://ai.liara.ir/api/v1/your-endpoint",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🧪 Usage Examples

### **Environmental Queries**

#### Persian Examples:
- "دمای فعلی چقدر است؟" → Current temperature analysis
- "رطوبت این هفته چطور بوده؟" → Weekly humidity trend
- "فشار هوا امروز چطوره؟" → Today's air pressure status
- "نور گلخانه کافی است؟" → Greenhouse light adequacy

#### English Examples:
- "What is the current temperature?" → Real-time temperature data
- "Show me humidity trends" → Humidity analysis with charts
- "Is the CO2 level optimal?" → CO2 level assessment
- "How is the light intensity?" → Light intensity analysis

### **Agricultural Queries**

#### Persian Examples:
- "آبیاری امروز چطوره؟" → Irrigation status analysis
- "رطوبت خاک کافی است؟" → Soil moisture assessment
- "pH خاک چقدر است؟" → Soil pH measurement
- "مصرف آب این ماه چقدر بوده؟" → Monthly water usage

#### English Examples:
- "How is irrigation today?" → Irrigation status
- "What is the soil moisture level?" → Soil moisture data
- "Show me N-P-K levels" → Nutrient level analysis
- "Water usage this week?" → Weekly water consumption

### **Pest Detection Queries**

#### Persian Examples:
- "وضعیت آفات چطوره؟" → Pest status overview
- "آیا بیماری وجود دارد؟" → Disease risk assessment
- "رطوبت برگ چقدر است؟" → Leaf wetness measurement
- "توصیه درمانی چیست؟" → Treatment recommendations

#### English Examples:
- "Any pest detections today?" → Daily pest monitoring
- "What is the disease risk?" → Disease risk analysis
- "Leaf wetness status?" → Leaf wetness monitoring
- "Treatment recommendations?" → Pest treatment advice

### **Analytics Queries**

#### Persian Examples:
- "مصرف انرژی این هفته چقدر بوده؟" → Weekly energy consumption
- "بازدهی آبیاری چطوره؟" → Irrigation efficiency analysis
- "سود این ماه چقدر است؟" → Monthly profit calculation
- "هزینه هر کیلو چقدر است؟" → Cost per kg analysis

#### English Examples:
- "Energy usage this week?" → Energy consumption analysis
- "Irrigation efficiency?" → Efficiency metrics
- "Profit margin this month?" → Profit analysis
- "Cost per kilogram?" → Cost analysis

## 🔧 Configuration

### **Environment Variables**
```env
# AI Configuration
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://ai.liara.ir/api/v1/your-endpoint
OPENAI_MODEL_NAME=openai/gpt-4o-mini

# Database
DATABASE_URL=sqlite:///./smart_dashboard.db

# Query Processing
QUERY_TIMEOUT_SECONDS=30
MAX_QUERY_LENGTH=1000
CONVERSATION_MEMORY_SIZE=10

# Security
ENABLE_SQL_VALIDATION=true
ALLOWED_TABLES=sensor_data
BLOCKED_KEYWORDS=DROP,DELETE,UPDATE,INSERT,ALTER
```

### **Feature Context Configuration**
```python
FEATURE_CONTEXTS = {
    "irrigation": {
        "sensors": ["soil_moisture", "water_usage", "rainfall"],
        "focus": "water management and irrigation"
    },
    "environment": {
        "sensors": ["temperature", "humidity", "co2_level", "light"],
        "focus": "greenhouse climate control"
    },
    "pest": {
        "sensors": ["pest_count", "disease_risk", "leaf_wetness"],
        "focus": "pest monitoring and disease detection"
    },
    "dashboard": {
        "sensors": ["all"],
        "focus": "comprehensive agricultural overview"
    }
}
```

## 🛡️ Security Features

### **Query Validation**
1. **SQL Injection Prevention**
   - Only SELECT queries allowed
   - Dangerous keywords blocked
   - Parameterized query execution
   - Input sanitization

2. **Access Control**
   - Session-based user management
   - Feature-specific access control
   - Query rate limiting
   - Resource usage monitoring

3. **Data Protection**
   - Sensitive data filtering
   - Audit logging
   - Error message sanitization
   - Secure error handling

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

### **Response Optimization**
- Structured response formatting
- Chart data generation optimization
- Metrics extraction efficiency
- Persian translation caching

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
  -d '{"query": "دمای فعلی چقدر است؟", "feature_context": "environment"}'

# Test English query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the current humidity?", "feature_context": "environment"}'

# Test streaming query
curl -X POST http://localhost:8000/ask/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "رطوبت خاک امروز چطوره؟", "feature_context": "irrigation"}'
```

### **Health Checks**
```bash
# AI service health
curl http://localhost:8000/ai/health

# Query processing health
curl http://localhost:8000/ask/health
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

4. **SQL Generation Errors**
   - Check query complexity
   - Verify database schema
   - Review SQL validation rules
   - Test with simpler queries

### **Debug Mode**
Enable debug logging for detailed query processing:
```python
import logging
logging.getLogger('unified_semantic_service').setLevel(logging.DEBUG)
logging.getLogger('query_builder').setLevel(logging.DEBUG)
```

## 📈 Monitoring & Analytics

### **Key Metrics**
- Query processing time
- Language detection accuracy
- SQL generation success rate
- Response quality metrics
- User engagement analytics

### **Logging**
- Comprehensive query processing logs
- Error tracking and monitoring
- Performance metrics collection
- User behavior analytics

---

**🔄 The Dynamic Query System powers the intelligent query processing engine of the Smart Agriculture Dashboard, enabling natural language interaction with complex agricultural data through advanced AI and comprehensive SQL generation.**