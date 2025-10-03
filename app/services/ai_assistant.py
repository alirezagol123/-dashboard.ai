import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)

class MockLLM:
    """Mock LLM for testing without OpenAI API"""
    def invoke(self, messages, **kwargs):
        return type('MockResponse', (), {'content': 'Mock response for testing'})()
    
    def predict(self, text, **kwargs):
        return "Mock response for testing"

class AIAssistant:
    """AI Assistant for feature-aware agriculture queries"""
    
    def __init__(self):
        # Initialize LLM
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        
        if self.api_key and self.api_key != "your-openai-api-key-here" and len(self.api_key) > 10:
            self.llm = ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model_name=self.model_name,
                temperature=0.1
            )
            logger.info(f"Using custom AI API: {self.base_url} with model {self.model_name}")
        else:
            self.llm = MockLLM()
            logger.warning("Using MockLLM - set OPENAI_API_KEY for real AI responses")
        
        # Initialize memory
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")
        
        # Store conversation history for better context (last 10 messages)
        self.conversation_history = []
        
        # Feature contexts
        self.feature_contexts = {
            "irrigation": {
                "name": "Smart Irrigation Management",
                "description": "Water management, soil moisture, and irrigation scheduling",
                "entities": ["sensor_data"],
                "key_fields": ["soil_moisture", "water_usage", "water_efficiency", "rainfall"],
                "apis": ["start_irrigation", "stop_irrigation", "get_schedule"],
                "services": ["auto_irrigation", "weather_integration"],
                "logs": ["irrigation_logs", "water_usage_logs"]
            },
            "environment": {
                "name": "Greenhouse Environment Control",
                "description": "Temperature, humidity, CO2, light, and climate management",
                "entities": ["sensor_data"],
                "key_fields": ["temperature", "humidity", "co2_level", "light", "pressure"],
                "apis": ["set_temperature", "set_humidity", "control_fans"],
                "services": ["climate_control", "energy_optimization"],
                "logs": ["climate_logs", "control_logs"]
            },
            "pest": {
                "name": "Pest & Disease Detection",
                "description": "Pest monitoring, disease detection, and treatment recommendations",
                "entities": ["sensor_data"],
                "key_fields": ["pest_count", "pest_detection", "disease_risk", "leaf_wetness"],
                "apis": ["detect_pests", "apply_treatment", "get_recommendations"],
                "services": ["pest_monitoring", "disease_prediction"],
                "logs": ["detection_logs", "treatment_logs"]
            },
            "dashboard": {
                "name": "Dashboard Overview",
                "description": "General dashboard queries and cross-feature analysis",
                "entities": ["sensor_data"],
                "key_fields": ["temperature", "humidity", "soil_moisture", "co2_level", "light", "pest_count", "water_usage", "energy_usage", "yield_prediction"],
                "apis": ["sensor_data", "data_stats", "websocket"],
                "services": ["data_processing", "alert_system", "reporting"],
                "logs": ["system_logs", "error_logs", "performance_logs"]
            }
        }
    
    def _get_live_sensor_data(self, feature: str) -> List[Dict[str, Any]]:
        """Get live sensor data for the specified feature"""
        try:
            # Connect to SQLite database
            conn = sqlite3.connect('smart_dashboard.db')
            cursor = conn.cursor()
            
            # Map feature to relevant sensor types
            sensor_mapping = {
                "irrigation": ["soil_moisture", "water_usage", "water_efficiency", "rainfall"],
                "environment": ["temperature", "humidity", "co2_level", "light", "pressure"],
                "pest": ["pest_count", "pest_detection", "disease_risk", "leaf_wetness"],
                "dashboard": ["temperature", "humidity", "soil_moisture", "co2_level", "light", "pest_count", "water_usage", "energy_usage", "yield_prediction"]
            }
            
            relevant_sensors = sensor_mapping.get(feature, [])
            if not relevant_sensors:
                return []
            
            # Get latest data for each relevant sensor type
            live_data = []
            for sensor_type in relevant_sensors:
                cursor.execute("""
                    SELECT timestamp, sensor_type, value 
                    FROM sensor_data 
                    WHERE sensor_type = ? 
                    ORDER BY timestamp DESC 
                    LIMIT 5
                """, (sensor_type,))
                
                results = cursor.fetchall()
                for row in results:
                    live_data.append({
                        "timestamp": row[0],
                        "sensor_type": row[1],
                        "value": row[2]
                    })
            
            conn.close()
            return live_data
            
        except Exception as e:
            logger.error(f"Error fetching live sensor data: {str(e)}")
            return []
    
    def _process_feature_query(self, feature: str, query: str) -> Dict[str, Any]:
        """Process feature-specific query"""
        try:
            # Get feature context
            context = self.feature_contexts.get(feature, self.feature_contexts["dashboard"])
            
            # Get live sensor data
            live_data = self._get_live_sensor_data(feature)
            
            # Build intelligent response
            response = self._build_intelligent_response(feature, query, context, live_data)
            
            # Add to conversation history
            ai_response = response["summary"]
            self._add_to_conversation_history(query, ai_response)
            
            return {
                "success": True,
                "answer": response["summary"],
                "feature": feature,
                "entity": context["name"],
                "chart": response.get("chart"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing feature query: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "feature": feature
            }
    
    def _add_to_conversation_history(self, user_query: str, ai_response: str):
        """Add message to conversation history (keep last 10 messages)"""
        self.conversation_history.append({
            "user": user_query,
            "ai": ai_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 messages (5 exchanges)
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
    
    def _get_conversation_context(self) -> str:
        """Get formatted conversation history for context"""
        if not self.conversation_history:
            return "No previous conversation history."
        
        context_lines = ["Previous conversation:"]
        for i, msg in enumerate(self.conversation_history[-5:], 1):  # Last 5 exchanges
            context_lines.append(f"{i}. User: {msg['user']}")
            context_lines.append(f"   AI: {msg['ai']}")
        
        return "\n".join(context_lines)

    def _build_intelligent_response(self, feature: str, query: str, context: Dict[str, Any], live_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build intelligent response using LLM"""
        try:
            import json
            
            # Prepare context for LLM
            context_str = f"""
            Feature: {context['name']}
            Description: {context['description']}
            Available Entities: {', '.join(context['entities'])}
            Key Fields: {', '.join(context['key_fields'])}
            Available APIs: {', '.join(context['apis'])}
            Available Services: {', '.join(context['services'])}
            Available Logs: {', '.join(context['logs'])}
            """
            
            # Prepare live data summary
            live_data_summary = ""
            if live_data:
                live_data_summary = f"Live Sensor Data (last 5 readings): {json.dumps(live_data, indent=2)}"
            else:
                live_data_summary = "No live sensor data available"
            
            # Get conversation history for context
            conversation_context = self._get_conversation_context()
            
            # Create prompt
            prompt = f"""You are a knowledgeable and friendly AI Assistant for agriculture. You are having a natural conversation with a farmer.

CONTEXT:
{context_str}

CONVERSATION HISTORY:
{conversation_context}

LIVE DATA (for reference only):
{live_data_summary}

USER QUERY: {query}

INSTRUCTIONS:
1. Respond ONLY in Persian (Farsi)
2. Be friendly, conversational, and natural - like talking to a friend
3. Use conversation history to provide better context and follow-up responses
4. Adapt your response style based on the user's query:
   - For greetings ("خوبی", "سلام", "چطوری") -> Warm, welcoming response
   - For casual questions -> Conversational and helpful
   - For technical questions -> Detailed but easy to understand
   - For emotional queries -> Empathetic and supportive
   - For urgent problems -> Direct and solution-focused
   - For follow-up questions -> Reference previous conversation naturally
5. Only mention specific sensor data if the user explicitly asks about metrics or data
6. Keep responses conversational, not like formal reports
7. Be encouraging and positive
8. Ask follow-up questions when appropriate to help the user
9. If you don't know something, admit it and offer to help find the answer
10. Format response as JSON with this structure:
{{
    "summary": "پاسخ طبیعی و مناسب با نوع سوال (1-3 جمله)",
    "metrics": null,
    "recommendations": [
        "توصیه مفید و عملی",
        "نکته کاربردی دیگر"
    ],
    "chart": null
}}

10. Make recommendations practical and actionable
11. Use a warm, supportive tone
12. Be flexible in your responses - adapt to the conversation flow

RESPONSE (JSON only):"""

            # Get LLM response
            if hasattr(self.llm, 'openai_api_key') and self.llm.openai_api_key:
                response = self.llm.invoke(prompt)
                response_text = response.content.strip()
            else:
                # Mock response
                response_text = json.dumps({
                    "summary": f"وضعیت {context['name']} بر اساس داده‌های زنده",
                    "metrics": {"sensor_count": len(live_data)},
                    "recommendations": ["بررسی داده‌های سنسور", "نظارت مداوم", "به‌روزرسانی تنظیمات"],
                    "chart": None
                }, ensure_ascii=False)
            
            # Parse JSON response
            try:
                parsed_response = json.loads(response_text)
                return parsed_response
            except json.JSONDecodeError:
                # Fallback if JSON parsing fails
                return {
                    "summary": response_text,
                    "metrics": {},
                    "recommendations": [],
                    "chart": None
                }
                
        except Exception as e:
            logger.error(f"Error building intelligent response: {str(e)}")
            return {
                "summary": f"خطا در پردازش درخواست: {str(e)}",
                "metrics": {},
                "recommendations": [],
                "chart": None
            }
    
    def process_query(self, feature: str, query: str) -> Dict[str, Any]:
        """Main processing function"""
        try:
            logger.info(f"🔍 AI Assistant: Processing {feature} query: '{query}'")
            
            # Validate feature
            if feature not in self.feature_contexts:
                return {
                    "success": False,
                    "error": f"Invalid feature. Available features: {list(self.feature_contexts.keys())}"
                }
            
            # Process the query
            result = self._process_feature_query(feature, query)
            
            logger.info(f"✅ AI Assistant: Query processed successfully")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI Assistant Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "feature": feature
            }
    
    def get_available_features(self) -> List[str]:
        """Get list of available features"""
        return list(self.feature_contexts.keys())
    
    def get_feature_info(self, feature: str) -> Dict[str, Any]:
        """Get information about a specific feature"""
        return self.feature_contexts.get(feature, {})
    
    def get_sample_queries(self, feature: str) -> List[str]:
        """Get sample queries for a feature"""
        samples = {
            "irrigation": [
                "وضعیت آبیاری فعلی چیست؟",
                "آخرین آبیاری کی انجام شد؟",
                "مصرف آب امروز چقدر است؟"
            ],
            "environment": [
                "دمای فعلی گلخانه چقدر است؟",
                "رطوبت هوا چگونه است؟",
                "وضعیت تهویه چگونه است؟"
            ],
            "pest": [
                "آفات امروز چه هستند؟",
                "خطر بیماری چقدر است؟",
                "توصیه‌های آفت‌کشی چیست؟"
            ],
            "dashboard": [
                "وضعیت کلی مزرعه چیست؟",
                "آمار کلی سنسورها را نشان دهید",
                "آخرین قرائت‌ها چه هستند؟"
            ]
        }
        return samples.get(feature, [])
