"""
Intent Router Layer for AI Assistant
Smart intent detection and routing system for agriculture queries
"""

import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import sqlite3
from dotenv import load_dotenv
from .session_storage import SessionStorage

# Load environment variables
load_dotenv()

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

# MockLLM removed - using real LLM only

class IntentRouterLayer:
    """Complete Intent Router Layer with smart intent detection and routing"""
    
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
            logger.info(f" Intent Router: Real LLM initialized: {self.model_name}")
            logger.info(f" Intent Router: API Base URL: {self.base_url}")
        else:
            logger.error(f" Intent Router: Invalid API key - length: {len(self.api_key) if self.api_key else 0}")
            logger.error(f" Intent Router: API key value: {self.api_key}")
            raise ValueError(" Intent Router: OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        # Initialize conversation memory (k=10 window)
        self.conversation_memories = {}  # session_id -> ConversationBufferWindowMemory
        
        # Initialize session storage (database storage)
        self.session_storage = SessionStorage()
        
        # Initialize services
        self._initialize_services()
        
        logger.info(" Intent Router Layer initialized successfully")
        
        # Start session cleanup task
        self._start_session_cleanup()
    
    def _initialize_services(self):
        """Initialize required services"""
        try:
            # Import services
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            
            # Initialize services
            self.unified_semantic_service = UnifiedSemanticQueryService()
            
            logger.info(" Services initialized successfully")
        except Exception as e:
            logger.error(f" Error initializing services: {str(e)}")
            raise
    
    def _get_or_create_memory(self, session_id: str) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for a session (k=10)"""
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = ConversationBufferWindowMemory(
                k=10,  # Keep last 10 messages
                memory_key="chat_history",
                return_messages=True,
                output_key="output"
            )
            logger.info(f" Created new conversation memory for session: {session_id}")
        return self.conversation_memories[session_id]
    
    def _detect_language(self, text: str) -> str:
        """Detect if text is Persian or English"""
        persian_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        total_chars = len([c for c in text if c.isalpha()])
        
        if total_chars == 0:
            return 'en'
        
        persian_ratio = persian_chars / total_chars
        return 'fa' if persian_ratio > 0.3 else 'en'
    
    def _detect_comparison_intent(self, query: str) -> bool:
        """Detect comparison intent in query (language-independent)"""
        query_lower = query.lower()
        
        # Persian comparison keywords
        persian_comparison_words = [
            "مقایسه", "مقایسه", "تفاوت", "نسبت", "در مقابل", "با", "بین",
            "امروز", "دیروز", "هفته", "ماه", "سال", "پیش", "گذشته", "اخیر"
        ]
        
        # English comparison keywords  
        english_comparison_words = [
            "compare", "comparison", "difference", "versus", "vs", "against",
            "today", "yesterday", "week", "month", "year", "ago", "past", "recent"
        ]
        
        # Check for comparison patterns
        comparison_patterns = [
            r'\d+\s*روز\s*پیش',  # "X days ago" in Persian
            r'\d+\s*days?\s*ago',  # "X days ago" in English
            r'امروز.*دیروز',  # "today ... yesterday" in Persian
            r'today.*yesterday',  # "today ... yesterday" in English
            r'هفته.*هفته',  # "week ... week" in Persian
            r'week.*week',  # "week ... week" in English
        ]
        
        # Check for comparison keywords
        for word in persian_comparison_words + english_comparison_words:
            if word in query_lower:
                return True
        
        # Check for comparison patterns
        import re
        for pattern in comparison_patterns:
            if re.search(pattern, query_lower):
                return True
        
        return False
    
    def _translate_query(self, persian_query: str) -> str:
        """Translate Persian query to English using Unified Semantic Service's translator"""
        try:
            # Use the sophisticated translator from Unified Semantic Service
            translated_query = self.unified_semantic_service.translator.translate_query_to_english(persian_query)
            
            logger.info(f" Intent Router Translation: '{persian_query}' -> '{translated_query}'")
            return translated_query
            
        except Exception as e:
            logger.error(f" Translation Error: {str(e)}")
            # Fallback to basic translation
            return self._fallback_translation(persian_query)
    
    def _fallback_translation(self, persian_text: str) -> str:
        """Fallback word-by-word translation if LLM fails"""
        translations = {
            "آبیاری": "irrigation", "ابیاری": "irrigation", "آب": "water",
            "دما": "temperature", "دمای": "temperature", "رطوبت": "humidity",
            "امروز": "today", "وضعیت": "status", "چطوره": "how is",
            "گلخانه": "greenhouse", "گلخونه": "greenhouse", "آفات": "pests",
            "دمای": "temperature", "ابیاری": "irrigation"
        }
        
        words = persian_text.split()
        translated_words = []
        
        for word in words:
            if word in translations:
                translated_words.append(translations[word])
            else:
                translated_words.append(word)
        
        return " ".join(translated_words)
    
    def _detect_intent(self, english_query: str, conversation_context: str = "", original_query: str = None) -> str:
        """Detect user intent using LLM"""
        try:
            context_info = f"\nPrevious conversation:\n{conversation_context}" if conversation_context else ""
            
            # First check for dangerous queries (more specific to avoid false positives)
            dangerous_keywords = ['drop table', 'delete from', 'update set', 'insert into', 'alter table', 'create table', 'truncate table', 'remove table', 'clear table']
            query_lower = english_query.lower()
            
            for keyword in dangerous_keywords:
                if keyword in query_lower:
                    logger.warning(f"  Dangerous query detected: {keyword}")
                    return 'data_query'  # Route to data_query to trigger SQL validation
            
            # NEW: Check for alert management commands (BEFORE agricultural terms)
            alert_keywords = [
                # English keywords
                'alert', 'notify', 'warning', 'threshold', 'monitor', 'create alert', 'alert me', 'set alert',
                'send me a message', 'message when', 'notify when', 'alert when', 'warn when',
                # Persian keywords
                'هشدار', 'اعلان', 'اطلاع', 'بهم هشدار بده', 'به من هشدار بده', 'هشدار بده', 'اعلان بده', 'اطلاع بده',
                'زمانی که', 'وقتی که', 'قتی', 'اگر', 'هنگامی که', 'پیامک', 'اس ام اس', 'sms', 'بیشتر از', 'کمتر از',
                'پیام بده', 'بهم پیام بده', 'به من پیام بده'
            ]
            for keyword in alert_keywords:
                # Check both original query and English query for Persian/English keywords
                if keyword in query_lower or (original_query and keyword in original_query):
                    logger.info(f" Alert keyword '{keyword}' detected, classifying as alert_management")
                    return 'alert_management'
            
            # FALLBACK: Check for agricultural sensor terms first (before LLM)
            agricultural_terms = [
                'irrigation', 'watering', 'soil', 'soil moisture', 'temperature', 'humidity', 
                'pests', 'pest', 'pesticide', 'greenhouse', 'environment', 'environmental',
                'leaf wetness', 'fruit count', 'fruit size', 'plant height', 'co2', 'co2 level',
                'light', 'wind speed', 'rainfall', 'disease risk', 'yield prediction', 
                'energy usage', 'water usage', 'fertilizer', 'nutrient', 'ph', 'pressure',
                'motion', 'detection', 'efficiency', 'prediction', 'moisture', 'wetness'
            ]
            
            # If query contains agricultural terms, classify as data_query
            for term in agricultural_terms:
                if term in query_lower:
                    logger.info(f" Agricultural term '{term}' detected, classifying as data_query")
                    return 'data_query'
            
            # Check for question words that suggest data queries
            data_question_words = ['what is', 'how much', 'how many', 'show me', 'current', 'latest', 'status']
            for word in data_question_words:
                if word in query_lower:
                    logger.info(f" Data question word '{word}' detected, classifying as data_query")
                    return 'data_query'
            
            prompt = f"""You are an expert intent classifier for agriculture AI assistant queries.

Classify the following query into ONE of these categories:
- data_query: Questions asking for specific data, measurements, statistics, or database information (temperature, humidity, pest counts, irrigation status, soil conditions, sensor readings, leaf wetness, fruit size, plant height, etc.)
- mixed: Questions that combine data requests with explanations or reasoning

Query: {english_query}{context_info}

Examples:
- "What is the current temperature?" -> data_query
- "What is the leaf wetness?" -> data_query (sensor measurement)
- "What is the fruit size?" -> data_query (sensor measurement)
- "Should I spray pesticides today?" -> data_query (asks for recommendation based on data)
- "How many pests are there?" -> data_query
- "What is the irrigation status?" -> data_query
- "Why is the temperature high today?" -> mixed
- "Show me irrigation data" -> data_query
- "What caused the temperature spike and how can I fix it?" -> mixed
- "Is it safe to spray today?" -> data_query (needs pest/weather data)
- "When should I harvest?" -> data_query (needs crop data)
- "Delete all data" -> data_query (dangerous operation)
- "Remove table" -> data_query (dangerous operation)
- "DROP TABLE users" -> data_query (dangerous operation)

IMPORTANT: Agricultural sensor terms should ALWAYS be data_query:
- "irrigation" -> data_query (needs soil moisture, water usage data)
- "pesticide" -> data_query (needs pest count, weather data)
- "soil" -> data_query (needs soil moisture, pH data)
- "greenhouse" -> data_query (needs environmental sensor data)
- "environment" -> data_query (needs temperature, humidity, CO2 data)
- "pests" -> data_query (needs pest count, detection data)
- "temperature" -> data_query (needs temperature sensor data)
- "humidity" -> data_query (needs humidity sensor data)
- "soil moisture" -> data_query (needs soil moisture sensor data)
- "water usage" -> data_query (needs water usage sensor data)
- "leaf wetness" -> data_query (needs leaf wetness sensor data)
- "fruit count" -> data_query (needs fruit count sensor data)
- "plant height" -> data_query (needs plant height sensor data)
- "CO2 level" -> data_query (needs CO2 sensor data)
- "light intensity" -> data_query (needs light sensor data)
- "wind speed" -> data_query (needs wind speed sensor data)
- "rainfall" -> data_query (needs rainfall sensor data)
- "disease risk" -> data_query (needs disease risk sensor data)
- "yield prediction" -> data_query (needs yield prediction sensor data)
- "energy usage" -> data_query (needs energy usage sensor data)

Intent:"""
            
            response = self.llm.invoke(prompt)
            intent = response.content.strip().lower()
            
            # Validate intent
            if intent not in ['data_query', 'mixed']:
                logger.warning(f" Invalid intent detected: {intent}, defaulting to data_query")
                intent = 'data_query'
            
            logger.info(f" Intent detected: {intent}")
            return intent
            
        except Exception as e:
            logger.error(f" Intent Detection Error: {str(e)}")
            return 'data_query'  # Default to data_query for safety
    
    def _translate_response_to_persian(self, english_response: str) -> str:
        """Translate English response back to Persian using LLM"""
        try:
            prompt = f"""You are an expert translator. Translate this English response about agriculture/greenhouse management into natural Persian while preserving the markdown formatting:

English: {english_response}

Important: Keep the markdown structure intact (# headers, ## subheaders, - bullet points, 1. numbered lists). Only translate the text content, not the formatting.

Persian:"""
            
            response = self.llm.invoke(prompt)
            persian_response = response.content.strip()
            
            # Fix encoding issues by ensuring UTF-8 encoding
            if isinstance(persian_response, str):
                # Ensure the string is properly encoded
                persian_response = persian_response.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Safe logging with encoding handling
            try:
                logger.info(f" Response Translation: '{english_response[:50]}...' -> '{persian_response[:50]}...'")
            except UnicodeEncodeError:
                logger.info(f" Response Translation: English -> Persian (encoding safe)")
            return persian_response
            
        except Exception as e:
            logger.error(f" Response Translation Error: {str(e)}")
            # Return original response with proper encoding
            try:
                return english_response.encode('utf-8', errors='ignore').decode('utf-8')
            except:
                return "Translation error occurred"
    
    def _process_data_query(self, english_query: str, session_id: str, feature_context: str, is_comparison: bool = False) -> Dict[str, Any]:
        """Process data query using Unified Semantic Service"""
        try:
            logger.info(f" Processing data query: '{english_query}' (comparison: {is_comparison})")
            
            result = self.unified_semantic_service.process_query(
                query=english_query,
                feature_context=feature_context,
                session_id=session_id,
                intent="data_query",
                is_comparison=is_comparison
            )
            
            # Check if the semantic service returned an error
            if not result.get("success", False) and result.get("error"):
                logger.error(f" Semantic Service Error: {result.get('error')}")
                return {
                    "type": "data_query",
                    "success": False,
                    "response": result.get("error", "Query execution failed"),
                    "data": [],
                    "sql": result.get("sql", ""),
                    "metrics": {},
                    "validation": result.get("validation", {"query_valid": False, "execution_success": False}),
                    "error": result.get("error")
                }
            
            return {
                "type": "data_query",
                "success": result.get("success", False),
                "response": result.get("summary", "No data available"),
                "data": result.get("raw_data", []),
                "sql": result.get("sql", ""),
                "metrics": result.get("metrics", {}),
                "validation": result.get("validation", {}),
                "chart": result.get("chart", None),  # Add chart data
                "chart_type": result.get("chart_type", None)  # Add chart type
            }
            
        except Exception as e:
            logger.error(f" Data Query Processing Error: {str(e)}")
            return {
                "type": "data_query",
                "success": False,
                "response": f"Error processing data query: {str(e)}",
                "data": [],
                "sql": "",
                "metrics": {},
                "validation": {"query_valid": False, "execution_success": False}
            }
    
    
    def _process_mixed_query(self, english_query: str, session_id: str, feature_context: str, is_comparison: bool = False) -> Dict[str, Any]:
        """Process mixed query by splitting and merging results"""
        try:
            print(f" DEBUG: Starting mixed query processing for: {len(english_query)} characters (comparison: {is_comparison})")
            logger.info(f" Processing mixed query: '{english_query}' (comparison: {is_comparison})")
            
            # Extract data parts and reasoning parts
            print(f" DEBUG: Extracting data parts...")
            data_parts = self._extract_data_parts(english_query)
            print(f" DEBUG: Extracting reasoning parts...")
            reasoning_parts = self._extract_reasoning_parts(english_query)
            
            print(f" DEBUG: Extracted data parts: '{data_parts}'")
            print(f" DEBUG: Extracted reasoning parts: '{reasoning_parts}'")
            logger.info(f" DEBUG: Extracted data parts: '{data_parts}'")
            logger.info(f" DEBUG: Extracted reasoning parts: '{reasoning_parts}'")
            
            # Process data parts
            data_result = None
            if data_parts:
                print(f" DEBUG: Processing data parts with unified_semantic_service...")
                logger.info(f" DEBUG: Processing data parts with unified_semantic_service...")
                data_result = self.unified_semantic_service.process_query(
                    query=data_parts,
                    feature_context=feature_context,
                    session_id=session_id,
                    intent="mixed",
                    is_comparison=is_comparison
                )
                print(f" DEBUG: Data result success: {data_result.get('success', False)}")
                print(f" DEBUG: Data result data points: {len(data_result.get('data', []))}")
                print(f" DEBUG: Data result SQL: {data_result.get('sql', 'No SQL')}")
                logger.info(f" DEBUG: Data result success: {data_result.get('success', False)}")
                logger.info(f" DEBUG: Data result data points: {len(data_result.get('data', []))}")
                logger.info(f" DEBUG: Data result SQL: {data_result.get('sql', 'No SQL')}")
            else:
                print(f" DEBUG: No data parts extracted, skipping data processing")
                logger.warning(f" DEBUG: No data parts extracted, skipping data processing")
            
            # For mixed queries, we only process data parts
            # Reasoning parts are handled by the LLM in the streaming endpoint
            merged_response = self._merge_results(data_result, None, english_query)
            
            return {
                "type": "mixed",
                "success": True,
                "response": merged_response,
                "data": data_result.get("raw_data", []) if data_result else [],
                "sql": data_result.get("sql", "") if data_result else "",
                "metrics": data_result.get("metrics", {}) if data_result else {},
                "validation": data_result.get("validation", {}) if data_result else {"query_valid": True, "execution_success": True}
            }
            
        except Exception as e:
            logger.error(f" Mixed Query Processing Error: {str(e)}")
            return {
                "type": "mixed",
                "success": False,
                "response": f"Error processing mixed query: {str(e)}",
                "data": [],
                "sql": "",
                "metrics": {},
                "validation": {"query_valid": False, "execution_success": False}
            }
    
    def _process_alert_query(self, query: str, session_id: str, feature_context: str) -> Dict[str, Any]:
        """Process alert management queries"""
        try:
            print(f" DEBUG: Processing alert query: {len(query)} characters")
            logger.info(f" Processing alert query: {query}")
            
            # Use the unified semantic service to process alert queries
            from app.services.unified_semantic_service import UnifiedSemanticQueryService
            service = UnifiedSemanticQueryService()
            
            # Process the alert query - the query is already translated to English
            # from the main processing flow, so we can process it directly
            result = service._process_alert_query(query, session_id, "en")
            
            print(f" DEBUG: Alert processing result: {result.get('success', False)}")
            logger.info(f" Alert processing result: {result.get('success', False)}")
            
            return {
                "type": "alert_management",
                "success": result.get("success", False),
                "response": result.get("response", ""),
                "data": result.get("data", []),
                "sql": result.get("sql", ""),
                "metrics": result.get("metrics", {}),
                "validation": result.get("validation", {"query_valid": True, "execution_success": True}),
                "original_query": query,
                "english_query": query,
                "detected_language": "en",
                "detected_intent": "alert_management",
                "session_id": session_id,
                "feature_context": feature_context,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_context_length": 0
            }
            
        except Exception as e:
            logger.error(f" Alert Query Processing Error: {str(e)}")
            return {
                "type": "alert_management",
                "success": False,
                "response": f"Error processing alert query: {str(e)}",
                "data": [],
                "sql": "",
                "metrics": {},
                "validation": {"query_valid": False, "execution_success": False},
                "original_query": query,
                "english_query": query,
                "detected_language": "en",
                "detected_intent": "alert_management",
                "session_id": session_id,
                "feature_context": feature_context,
                "timestamp": datetime.utcnow().isoformat(),
                "conversation_context_length": 0
            }
    
    def _extract_data_parts(self, query: str) -> str:
        """Extract data-related parts from mixed query"""
        try:
            print(f" DEBUG: Extracting data parts from: {len(query)} characters")
            prompt = f"""Extract only the data-related parts from this query. Focus on questions about specific measurements, values, statistics, or sensor data that can be answered from the sensor_data table.

Available sensor types: temperature, humidity, pressure, light, co2_level, wind_speed, soil_moisture, soil_ph, soil_temperature, plant_height, fruit_count, fruit_size, nitrogen_level, phosphorus_level, potassium_level, pest_count, pest_detection, disease_risk, water_usage, water_efficiency, yield_prediction, yield_efficiency, tomato_price, lettuce_price, pepper_price, motion, fertilizer_usage, energy_usage, rainfall

Examples:
- "How is the soil today? Should we apply fertilizer?" -> "What is the current soil moisture and soil pH?"
- "What's the temperature? Is it too hot?" -> "What is the current temperature?"
- "Show me humidity data and tell me if it's good" -> "What is the current humidity?"
- "خاک چطوره امروز کود بدیم" -> "What is the current soil moisture and soil pH?"

Original query: {query}

Extract only the data question (about sensor measurements/values):"""
            
            response = self.llm.invoke(prompt)
            extracted = response.content.strip()
            print(f" DEBUG: LLM extracted data parts: '{extracted}'")
            logger.info(f" DEBUG: LLM extracted data parts: '{extracted}'")
            return extracted
            
        except Exception as e:
            print(f" DEBUG: Data Parts Extraction Error: {str(e)}")
            logger.error(f" Data Parts Extraction Error: {str(e)}")
            return query  # Return original if extraction fails
    
    def _extract_reasoning_parts(self, query: str) -> str:
        """Extract reasoning/advice parts from mixed query"""
        try:
            print(f" DEBUG: Extracting reasoning parts from: {len(query)} characters")
            prompt = f"""Extract only the reasoning, advice, or recommendation parts from this query. Focus on questions about what to do, how to act, or what decisions to make.

Examples:
- "How is the soil today? Should we apply fertilizer?" -> "Should we apply fertilizer?"
- "What's the temperature? Is it too hot?" -> "Is it too hot?"
- "Show me humidity data and tell me if it's good" -> "Is the humidity good?"
- "خاک چطوره امروز کود بدیم" -> "Should we apply fertilizer today?"

Original query: {query}

Extract only the reasoning question (about actions/decisions):"""
            
            response = self.llm.invoke(prompt)
            extracted = response.content.strip()
            print(f" DEBUG: LLM extracted reasoning parts: '{extracted}'")
            logger.info(f" DEBUG: LLM extracted reasoning parts: '{extracted}'")
            return extracted
            
        except Exception as e:
            print(f" DEBUG: Reasoning Parts Extraction Error: {str(e)}")
            logger.error(f" Reasoning Parts Extraction Error: {str(e)}")
            return query  # Return original if extraction fails
    
    def _process_chit_chat(self, reasoning_parts: str, session_id: str) -> Dict[str, Any]:
        """Process reasoning parts using LLM"""
        try:
            # Get conversation context
            conversation_context = self._get_conversation_context(session_id)
            
            # Create prompt for reasoning
            prompt = f"""
            You are an agricultural AI assistant. Based on the user's question and context, provide helpful advice.
            
            User Question: {reasoning_parts}
            Context: {conversation_context}
            
            Provide a helpful response in the same language as the question.
            """
            
            # Get LLM response
            response = self.llm.invoke([HumanMessage(content=prompt)])
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                "success": True,
                "response": response_text,
                "type": "reasoning"
            }
            
        except Exception as e:
            logger.error(f" Error processing reasoning: {str(e)}")
            return {
                "success": False,
                "response": f"Error processing reasoning: {str(e)}",
                "type": "reasoning"
            }
    
    def _merge_results(self, data_result: Optional[Dict], reasoning_result: Optional[Dict], original_query: str) -> str:
        """Merge data and reasoning results into a single response"""
        try:
            data_info = data_result.get("response", "") if data_result else ""
            reasoning_info = reasoning_result.get("response", "") if reasoning_result else ""
            raw_data = data_result.get("raw_data", []) if data_result else []
            
            # Format the actual sensor data for the LLM
            sensor_data_text = ""
            if raw_data:
                sensor_data_text = "\n\n## Actual Sensor Data:\n"
                for data_point in raw_data:
                    sensor_type = data_point.get('sensor_type', 'unknown')
                    value = data_point.get('value', 'N/A')
                    timestamp = data_point.get('timestamp', 'N/A')
                    sensor_data_text += f"- {sensor_type}: {value} (at {timestamp})\n"
            
            prompt = f"""You are an AI assistant for a smart agriculture platform. 
Always respond in this structured format with proper markdown formatting:

# Summary
Brief one-sentence summary combining data and reasoning

## Key Metrics
- Metric 1: value
- Metric 2: value  
- Metric 3: value

## Analysis
Brief analysis combining data insights and reasoning (max 2 sentences)

## Recommendations
1. First recommendation
2. Second recommendation

Use proper markdown formatting with headers (#, ##), bullet points (-), and numbered lists (1., 2.). 
Keep responses concise and clear. If user speaks Persian, reply in Persian.

Original query: {original_query}

Data response: {data_info}

Reasoning response: {reasoning_info}
{sensor_data_text}

IMPORTANT: Use the actual sensor data values above in your response. Make specific recommendations based on the real sensor readings. Don't give generic advice - base your recommendations on the actual data values provided.

Merge these responses into a single structured response following the markdown format above:"""
            
            response = self.llm.invoke(prompt)
            merged_response = response.content.strip()
            
            # Add intent information at the end
            intent_text = " Mixed Query - Combined data analysis and conversation"
            return f"{merged_response}\n\n---\n{intent_text}"
            
        except Exception as e:
            logger.error(f" Results Merging Error: {str(e)}")
            # Fallback: combine responses manually
            data_part = data_info if data_result else ""
            reasoning_part = reasoning_info if reasoning_result else ""
            fallback_response = f"{data_part}\n\n{reasoning_part}".strip()
            intent_text = " Mixed Query - Combined data analysis and conversation"
            return f"{fallback_response}\n\n---\n{intent_text}"
    
    def _save_conversation_history(self, session_id: str, user_query: str, assistant_response: str, 
                                 sql_query: str = None, semantic_json: Dict = None, 
                                 metrics: Dict = None, chart_data: Dict = None):
        """Save conversation history to both memory and database"""
        try:
            # Save to in-memory conversation memory
            memory = self._get_or_create_memory(session_id)
            memory.chat_memory.add_user_message(user_query)
            memory.chat_memory.add_ai_message(assistant_response)
            
            # Save to database session storage
            self.session_storage.save_session_data(
                session_id=session_id,
                query=user_query,
                response=assistant_response,
                sql_query=sql_query,
                semantic_json=semantic_json,
                metrics=metrics,
                chart_data=chart_data
            )
            
            logger.info(f" Saved conversation history for session: {session_id}")
            
        except Exception as e:
            logger.error(f" Error saving conversation history: {str(e)}")
    
    def _get_conversation_context(self, session_id: str) -> str:
        """Get conversation history as context string from database"""
        try:
            # Get context from database storage
            context_data = self.session_storage.get_session_context(session_id, limit=5)
            
            if not context_data:
                return ""
            
            # Format conversation history
            context_lines = []
            for item in context_data:
                query = item['query'][:200] + "..." if len(item['query']) > 200 else item['query']
                response = item['response'][:200] + "..." if len(item['response']) > 200 else item['response']
                context_lines.append(f"User: {query}")
                context_lines.append(f"Assistant: {response}")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            logger.error(f" Error getting conversation context: {str(e)}")
            return ""
    
    def _start_session_cleanup(self):
        """Start session cleanup task"""
        try:
            # Expire sessions after 30 minutes
            expired_count = self.session_storage.expire_sessions(timeout_minutes=30)
            if expired_count > 0:
                logger.info(f" Expired {expired_count} sessions due to timeout")
            
            # Clean up old session data (keep 7 days)
            cleaned_count = self.session_storage.cleanup_expired_sessions(days_to_keep=7)
            if cleaned_count > 0:
                logger.info(f" Cleaned up {cleaned_count} old session records")
                
        except Exception as e:
            logger.error(f" Error in session cleanup: {e}")
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get session summary with key metrics"""
        return self.session_storage.get_session_summary(session_id)
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get list of active sessions"""
        return self.session_storage.get_active_sessions()
    
    def process_query(self, query: str, session_id: str = "default", feature_context: str = "dashboard") -> Dict[str, Any]:
        """Main processing function following the complete intent routing flow"""
        try:
            print(f"\n{'='*80}")
            print(f" INTENT ROUTER LAYER - NEW QUERY RECEIVED")
            print(f"{'='*80}")
            print(f" Original Query: {len(query)} characters")
            print(f"Session ID: {session_id}")
            print(f" Feature Context: {feature_context}")
            print(f"Timestamp: {datetime.utcnow().isoformat()}")
            print(f"{'='*80}")
            
            logger.info(f" Intent Router Layer: Processing query: '{query}' for session: {session_id}")
            
            # Step 1: Detect language
            print(f"\n STEP 1: LANGUAGE DETECTION")
            print(f"   Input: {len(query)} characters")
            detected_lang = self._detect_language(query)
            print(f"    Detected Language: {detected_lang}")
            logger.info(f" Language detected: {detected_lang}")
            
            # Step 1.5: Detect comparison intent BEFORE translation
            print(f"\n STEP 1.5: COMPARISON DETECTION")
            is_comparison = self._detect_comparison_intent(query)
            print(f"    Comparison detected: {is_comparison}")
            if is_comparison:
                print(f"    This is a comparison query - will use comparison logic")
            
            # Step 2: Translate if Persian
            print(f"\n STEP 2: TRANSLATION")
            english_query = query
            if detected_lang == 'fa':
                print(f"    Persian detected, translating...")
                english_query = self._translate_query(query)
                print(f"    Translated: {len(query)} -> {len(english_query)} characters")
                logger.info(f" Translated to English: '{english_query}'")
            else:
                print(f"    English detected, no translation needed")
            
            # Step 3: Get conversation context
            print(f"\n STEP 3: CONVERSATION CONTEXT")
            conversation_context = self._get_conversation_context(session_id)
            print(f"    Context Length: {len(conversation_context)} characters")
            if conversation_context:
                try:
                    print(f"    Context Preview: {conversation_context[:100]}...")
                except UnicodeEncodeError:
                    print(f"    Context Preview: [Text with special characters - encoding safe]")
            else:
                print(f"    No previous conversation")
            
            # Step 4: Detect intent
            print(f"\n STEP 4: INTENT DETECTION")
            print(f"    Analyzing: {len(english_query)} characters")
            intent = self._detect_intent(english_query, conversation_context, query)
            print(f"    Detected Intent: {intent}")
            logger.info(f" Intent detected: {intent}")
            
            # Step 5: Route based on intent
            print(f"\n STEP 5: INTENT ROUTING")
            print(f"    Routing to: {intent}")
            if intent == 'data_query':
                print(f"    Processing as DATA QUERY")
                result = self._process_data_query(english_query, session_id, feature_context, is_comparison)
            elif intent == 'mixed':
                print(f"    Processing as MIXED QUERY")
                result = self._process_mixed_query(english_query, session_id, feature_context, is_comparison)
            elif intent == 'alert_management':
                print(f"    Processing as ALERT MANAGEMENT")
                result = self._process_alert_query(english_query, session_id, feature_context)
            else:
                print(f"    Unknown intent, defaulting to DATA QUERY")
                result = self._process_data_query(english_query, session_id, feature_context, is_comparison)
            
            print(f"    Processing Result:")
            print(f"      - Success: {result.get('success', False)}")
            print(f"      - Response Length: {len(result.get('response', ''))}")
            print(f"      - Data Points: {len(result.get('data', []))}")
            print(f"      - SQL Generated: {'Yes' if result.get('sql') else 'No'}")
            
            # Step 6: Translate back to Persian if needed
            print(f"\n STEP 6: RESPONSE TRANSLATION")
            if detected_lang == 'fa':
                print(f"    Translating response back to Persian...")
                original_response = result['response']
                result['response'] = self._translate_response_to_persian(result['response'])
                print(f"    Response translated")
                # Safe printing with encoding handling
                try:
                    print(f"    Original: {original_response[:100]}...")
                except UnicodeEncodeError:
                    print(f"    Original: [Persian text - encoding safe]")
                try:
                    print(f"    Translated: {result['response'][:100]}...")
                except UnicodeEncodeError:
                    print(f"    Translated: [Persian text - encoding safe]")
                logger.info(f" Response translated back to Persian")
            else:
                print(f"    English response, no translation needed")
            
            # Step 7: Save conversation history
            print(f"\n STEP 7: SAVE CONVERSATION")
            self._save_conversation_history(
                session_id=session_id, 
                user_query=query, 
                assistant_response=result['response'],
                sql_query=result.get('sql', ''),
                semantic_json=result.get('validation', {}).get('semantic_json', {}),
                metrics=result.get('metrics', {}),
                chart_data=result.get('chart', {})
            )
            print(f"    Conversation saved for session: {session_id}")
            
            # Step 8: Convert to frontend-compatible format
            print(f"\n STEP 8: FRONTEND FORMATTING")
            formatted_result = self._format_for_frontend(result, detected_lang)
            print(f"    Formatted for frontend")
            
            # Step 9: Add metadata
            print(f"\n STEP 9: ADD METADATA")
            formatted_result.update({
                'original_query': query,
                'english_query': english_query,
                'detected_language': detected_lang,
                'detected_intent': intent,
                'session_id': session_id,
                'feature_context': feature_context,
                'timestamp': datetime.utcnow().isoformat(),
                'conversation_context_length': len(conversation_context)
            })
            print(f"    Metadata added")
            
            print(f"\n FINAL RESULT:")
            print(f"    Success: {formatted_result.get('success', False)}")
            print(f"    Response: {formatted_result.get('response', '')[:200]}...")
            print(f"    Language: {formatted_result.get('detected_language', 'unknown')}")
            print(f"    Intent: {formatted_result.get('detected_intent', 'unknown')}")
            print(f"    Data Points: {len(formatted_result.get('data', []))}")
            print(f"{'='*80}")
            print(f" QUERY PROCESSING COMPLETED SUCCESSFULLY")
            print(f"{'='*80}\n")
            
            logger.info(f" Intent Router Layer: Query processed successfully")
            return formatted_result
            
        except Exception as e:
            print(f"\n ERROR IN INTENT ROUTER LAYER:")
            print(f"   Error: {str(e)}")
            print(f"   Query: {len(query)} characters")
            print(f"   Session: {session_id}")
            print(f"{'='*80}\n")
            
            logger.error(f" Intent Router Layer Error: {str(e)}")
            return {
                "type": "error",
                "success": False,
                "response": f"Error processing query: {str(e)}",
                "data": [],
                "sql": "",
                "metrics": {},
                "validation": {"query_valid": False, "execution_success": False},
                "original_query": query,
                "session_id": session_id,
                "feature_context": feature_context,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _format_for_frontend(self, result: Dict[str, Any], language: str) -> Dict[str, Any]:
        """Format backend response to match frontend expectations"""
        try:
            # Extract the main response text
            main_response = result.get('response', 'No response generated')
            
            # Return the response as a simple string for the frontend
            return {
                "response": main_response,
                "success": result.get('success', False),
                "data": result.get('data', []),
                "sql": result.get('sql', ''),
                "metrics": result.get('metrics', {}),
                "validation": result.get('validation', {}),
                "chart": result.get('chart', None),  # Add chart data
                "chart_type": result.get('chart_type', None)  # Add chart type
            }
            
        except Exception as e:
            logger.error(f" Error formatting for frontend: {str(e)}")
            return {
                "response": f"Error formatting response: {str(e)}",
                "success": False,
                "data": [],
                "sql": "",
                "metrics": {},
                "validation": {"query_valid": False, "execution_success": False}
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the intent router layer"""
        try:
            # Test basic functionality
            test_result = self.process_query("test query", "health_test")
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "llm_available": hasattr(self.llm, 'openai_api_key'),
                "services_available": {
                    "unified_semantic_service": hasattr(self, 'unified_semantic_service')
                },
                "test_query_success": test_result.get("success", False),
                "active_sessions": len(self.conversation_memories)
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
