import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import sqlite3
from dotenv import load_dotenv
from .time_parser import parse_time_context

# Load environment variables
load_dotenv()

# LangChain imports
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents import AgentType
from langchain.tools import BaseTool
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.manager import CallbackManagerForToolRun

# Import the new QueryBuilder
from app.services.query_builder import QueryBuilder

logger = logging.getLogger(__name__)

# MockLLM removed - using real LLM only

class LLMTranslator:
    """LLM-based semantic translation for Persian to English queries"""
    
    def __init__(self, llm):
        self.llm = llm
        self.few_shot_examples = [
            {
                "persian": "آخرین آبیاری کی انجام شده؟",
                "english": "When was the last irrigation performed?"
            },
            {
                "persian": "پیش‌بینی برداشت محصول گوجه چند کیلوگرم است؟",
                "english": "What is the predicted tomato yield in kilograms?"
            },
            {
                "persian": "وضعیت آفات در گلخانه شماره ۲ چطوره؟",
                "english": "What is the pest situation in greenhouse 2?"
            },
            {
                "persian": "وضعیت دمای امروز چطوره؟",
                "english": "How is today's temperature status?"
            },
            {
                "persian": "ابیاری امروز چطوره؟",
                "english": "How is today's irrigation status?"
            },
            {
                "persian": "امروز سم پاشی کنم؟",
                "english": "Should I spray pesticides today?"
            },
            {
                "persian": "لان ما تو چه بخشی از گلخونه هستیم؟",
                "english": "What section of the greenhouse are we currently in?"
            }
        ]
    
    def detect_language(self, text: str) -> str:
        """Detect if text is Persian or English with hybrid detection for mixed content"""
        if not text or not text.strip():
            return 'en'
        
        # Count Persian characters (Arabic script range)
        persian_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF')
        # Count Arabic characters (extended range)
        arabic_chars = sum(1 for char in text if '\u0600' <= char <= '\u06FF' or '\u0750' <= char <= '\u077F')
        # Count English characters
        english_chars = sum(1 for char in text if char.isalpha() and ord(char) < 128)
        # Count all alphabetic characters
        total_alpha = sum(1 for char in text if char.isalpha())
        
        if total_alpha == 0:
            return 'en'
        
        # Calculate ratios
        persian_ratio = (persian_chars + arabic_chars) / total_alpha
        english_ratio = english_chars / total_alpha
        
        # Hybrid detection logic
        if persian_ratio > 0.4:
            return 'fa'  # Primarily Persian
        elif english_ratio > 0.6:
            return 'en'  # Primarily English
        elif persian_ratio > 0.2 and english_ratio > 0.2:
            # Mixed content - check for Persian keywords
            persian_keywords = ['آب', 'دما', 'رطوبت', 'خاک', 'گیاه', 'آفات', 'مصرف', 'امروز', 'دیروز', 'هفته', 'ماه']
            if any(keyword in text for keyword in persian_keywords):
                return 'fa'
            else:
                return 'en'
        else:
            return 'en'  # Default to English
    
    def translate_query_to_english(self, persian_query: str) -> str:
        """Translate Persian query to natural English using LLM"""
        try:
            # Build few-shot examples string
            examples_str = "\n".join([
                f"Persian: {ex['persian']}\nEnglish: {ex['english']}\n"
                for ex in self.few_shot_examples
            ])
            
            prompt = f"""You are an expert translator specializing in agriculture and greenhouse management queries.

Your task is to translate Persian queries into natural, fluent English that captures the full semantic meaning and context.

Few-shot examples:
{examples_str}

Now translate this Persian query:
Persian: {persian_query}

English:"""

            # Log LLM call with truncated prompt
            truncated_prompt = prompt[:200] + "..." if len(prompt) > 200 else prompt
            logger.info(f"🤖 LLM Call - Translation (Prompt): {truncated_prompt}")

            response = self.llm.invoke(prompt)
            # Safe accessor for response content (LangChain sometimes returns .text instead of .content)
            translated_query = getattr(response, 'content', None) or getattr(response, 'text', '')
            if not translated_query:
                raise ValueError("Empty response from LLM")
            translated_query = translated_query.strip()
            
            # Log LLM response (truncated)
            truncated_response = translated_query[:100] + "..." if len(translated_query) > 100 else translated_query
            logger.info(f"🤖 LLM Call - Translation (Response): {truncated_response}")
            
            logger.info(f" LLM Translation: '{persian_query}' -> '{translated_query}'")
            return translated_query
            
        except Exception as e:
            logger.error(f" Translation Error: {str(e)}")
            # Fallback to basic translation
            return self._fallback_translation(persian_query)
    
    def translate_response_to_persian(self, english_response: str) -> str:
        """Translate English response back to Persian using LLM"""
        try:
            prompt = f"""You are an expert translator. Translate this English response about agriculture/greenhouse management into natural Persian:

English: {english_response}

Persian:"""

            # Log LLM call with truncated prompt
            truncated_prompt = prompt[:200] + "..." if len(prompt) > 200 else prompt
            logger.info(f"🤖 LLM Call - Response Translation (Prompt): {truncated_prompt}")

            response = self.llm.invoke(prompt)
            # Safe accessor for response content (LangChain sometimes returns .text instead of .content)
            persian_response = getattr(response, 'content', None) or getattr(response, 'text', '')
            if not persian_response:
                raise ValueError("Empty response from LLM")
            persian_response = persian_response.strip()
            
            # Fix encoding issues by ensuring UTF-8 encoding
            if isinstance(persian_response, str):
                # Ensure the string is properly encoded
                persian_response = persian_response.encode('utf-8', errors='ignore').decode('utf-8')
            
            # Log LLM response (truncated) with safe encoding
            try:
                truncated_response = persian_response[:100] + "..." if len(persian_response) > 100 else persian_response
                logger.info(f"🤖 LLM Call - Response Translation (Response): {truncated_response}")
            except UnicodeEncodeError:
                logger.info(f"🤖 LLM Call - Response Translation (Response): [Persian text - encoding safe]")
            
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
    
    def _fallback_translation(self, persian_text: str) -> str:
        """Fallback word-by-word translation if LLM fails with expanded ontology mappings"""
        translations = {
            # Basic terms
            "آبیاری": "irrigation", "ابیاری": "irrigation", "آب": "water", "مصرف آب": "water usage",
            "دما": "temperature", "دمای": "temperature", "رطوبت": "humidity", "فشار": "pressure",
            "امروز": "today", "دیروز": "yesterday", "وضعیت": "status", "چطوره": "how is",
            "گلخانه": "greenhouse", "گلخونه": "greenhouse", "آفات": "pests", "آفت": "pest",
            
            # Time expressions
            "هفته": "week", "ماه": "month", "سال": "year", "روز": "day", "ساعت": "hour",
            "گذشته": "past", "اخیر": "recent", "پیش": "ago", "قبل": "before",
            "این": "this", "آن": "that", "آخرین": "last", "اولین": "first",
            
            # Sensor types
            "خاک": "soil", "گیاه": "plant", "برگ": "leaf", "میوه": "fruit",
            "نور": "light", "باد": "wind", "باران": "rain", "برف": "snow",
            "کود": "fertilizer", "سم": "pesticide", "بیماری": "disease",
            
            # Actions and comparisons
            "مقایسه": "compare", "تفاوت": "difference", "نسبت": "ratio", "در مقابل": "versus",
            "بیشتر": "more", "کمتر": "less", "بالا": "high", "پایین": "low",
            "افزایش": "increase", "کاهش": "decrease", "تغییر": "change",
            
            # Agricultural terms
            "محصول": "crop", "برداشت": "harvest", "کاشت": "planting", "آبیاری": "irrigation",
            "کوددهی": "fertilization", "سمپاشی": "spraying", "هرس": "pruning",
            "بذر": "seed", "نهال": "sapling", "درخت": "tree", "بوته": "bush",
            
            # Technical terms
            "سنسور": "sensor", "داده": "data", "اطلاعات": "information", "گزارش": "report",
            "تحلیل": "analysis", "نتیجه": "result", "مقدار": "value", "عدد": "number"
        }
        
        # Handle long structured JSON responses
        if len(persian_text) > 1000 or ('{' in persian_text and '}' in persian_text):
            # For long or JSON responses, try to translate key phrases only
            key_phrases = []
            for persian_term, english_term in translations.items():
                if persian_term in persian_text:
                    key_phrases.append(f"{persian_term} -> {english_term}")
            
            if key_phrases:
                return f"[Translation failed - key terms: {', '.join(key_phrases[:5])}]"
            else:
                return "[Translation failed - no known terms found]"
        
        # Regular word-by-word translation for short texts
        words = persian_text.split()
        translated_words = []
        
        for word in words:
            if word in translations:
                translated_words.append(translations[word])
            else:
                translated_words.append(word)
        
        return " ".join(translated_words)

    async def stream_response(self, prompt: str):
        """Stream LLM response token by token"""
        try:
            logger.info(f"🚀 Starting streaming response...")
            token_count = 0
            async for chunk in self.llm.astream(prompt):
                if hasattr(chunk, 'content') and chunk.content:
                    token_count += 1
                    # Fix encoding issues by ensuring UTF-8 encoding
                    content = chunk.content
                    if isinstance(content, str):
                        content = content.encode('utf-8', errors='ignore').decode('utf-8')
                    yield content
                else:
                    logger.warning(f" Chunk without content: {chunk}")
            
            logger.info(f"✅ Streaming completed. Total tokens: {token_count}")
        except Exception as e:
            logger.error(f"❌ Streaming Error: {str(e)}")
            yield f"Error: {str(e)}"

class SQLValidator:
    """Validates and sanitizes SQL queries"""
    
    def __init__(self, sql_db):
        self.sql_db = sql_db
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """Validate SQL query for safety and correctness with column whitelist"""
        try:
            # Check for dangerous operations
            dangerous_keywords = ['DROP TABLE', 'DELETE FROM', 'UPDATE SET', 'INSERT INTO', 'ALTER TABLE', 'CREATE TABLE', 'TRUNCATE TABLE']
            query_upper = query.upper()
            
            for keyword in dangerous_keywords:
                if keyword in query_upper:
                    return {
                        "valid": False,
                        "message": f"Dangerous operation detected: {keyword}",
                        "suggestions": ["Use SELECT queries only"]
                    }
            
            # Check if query uses allowed tables (allow SELECT * for exploration)
            if 'sensor_data' not in query_upper and 'SELECT *' not in query_upper:
                return {
                    "valid": False,
                    "message": "Query must use sensor_data table only",
                    "suggestions": ["Use SELECT * FROM sensor_data WHERE ..."]
                }
            
            # Basic syntax check
            if not query_upper.strip().startswith('SELECT'):
                return {
                    "valid": False,
                    "message": "Only SELECT queries are allowed",
                    "suggestions": ["Start your query with SELECT"]
                }
            
            # Column whitelist validation (skip for SELECT * queries)
            allowed_columns = [
                'timestamp', 'sensor_type', 'value', 'location', 'unit',
                'time_period', 'avg_value', 'min_value', 'max_value', 'data_points'
            ]
            
            # Extract column names from SELECT clause
            import re
            select_match = re.search(r'SELECT\s+(.*?)\s+FROM', query_upper, re.IGNORECASE)
            if select_match:
                select_clause = select_match.group(1)
                # Handle * and specific columns
                if select_clause.strip() != '*':
                    # Extract column names (handle aliases)
                    columns = re.findall(r'(\w+)(?:\s+AS\s+\w+)?', select_clause)
                    for column in columns:
                        if column.upper() not in [col.upper() for col in allowed_columns]:
                            return {
                                "valid": False,
                                "message": f"Column '{column}' is not allowed",
                                "suggestions": [f"Use only allowed columns: {', '.join(allowed_columns)}"]
                }
            
            return {
                "valid": True,
                "message": "Query is valid",
                "suggestions": []
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation error: {str(e)}",
                "suggestions": ["Check query syntax"]
            }

class UnifiedSemanticQueryService:
    """Unified service combining semantic layer and dynamic query generation"""
    
    def __init__(self):
        # Initialize LLM
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        self.model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        
        # Log configuration for debugging
        logger.info(f" LLM Configuration:")
        logger.info(f"   API Key: {'SET' if self.api_key and len(self.api_key) > 10 else 'NOT SET'}")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   Model: {self.model_name}")
        
        if self.api_key and self.api_key != "your-openai-api-key-here" and len(self.api_key) > 10:
            self.llm = ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model_name=self.model_name,
                temperature=0.1,
                streaming=True  # Enable streaming
            )
            logger.info(f" Unified Service: Real LLM initialized: {self.model_name}")
            logger.info(f" Unified Service: API Base URL: {self.base_url}")
        else:
            logger.error(f" Unified Service: Invalid API key - length: {len(self.api_key) if self.api_key else 0}")
            logger.error(f" Unified Service: API key value: {self.api_key}")
            raise ValueError(" Unified Service: OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        # Initialize components
        self.translator = LLMTranslator(self.llm)
        
        # Initialize SQL Database connection for dynamic query generation
        self.db_engine = self._initialize_db_engine()
        self.sql_db = SQLDatabase(self.db_engine)
        self.sql_toolkit = SQLDatabaseToolkit(db=self.sql_db, llm=self.llm)
        
        # Create SQL agent for dynamic query generation
        self.sql_agent = create_sql_agent(
            llm=self.llm,
            toolkit=self.sql_toolkit,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=15,
            agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            system_message=self._get_sql_system_message()
        )
        
        self.validator = SQLValidator(self.sql_db)
        
        # Build comprehensive ontology
        self.ontology = self._build_comprehensive_ontology()
        
        # Initialize QueryBuilder for semantic JSON to SQL conversion
        self.query_builder = QueryBuilder(self.ontology)
        
        # Initialize conversation memory (session-based)
        self.conversation_memories = {}  # session_id -> ConversationBufferMemory
        
        logger.info(" UnifiedSemanticQueryService initialized successfully with conversation history and QueryBuilder")
    
    def _get_or_create_memory(self, session_id: str) -> ConversationBufferMemory:
        """Get or create conversation memory for a session"""
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True,
                output_key="output",
                k=10  # Keep last 10 messages
            )
            logger.info(f" Created new conversation memory for session: {session_id}")
        return self.conversation_memories[session_id]
    
    def _get_conversation_context(self, session_id: str) -> str:
        """Get conversation history as context string"""
        memory = self._get_or_create_memory(session_id)
        chat_history = memory.chat_memory.messages
        
        if not chat_history:
            return "No previous conversation history."
        
        # Format conversation history
        context_lines = []
        for i, message in enumerate(chat_history[-10:]):  # Last 10 messages
            role = "User" if message.type == "human" else "Assistant"
            content = message.content[:200] + "..." if len(message.content) > 200 else message.content
            context_lines.append(f"{role}: {content}")
        
        return "\n".join(context_lines)
    
    def _save_conversation_history(self, session_id: str, user_query: str, assistant_response: str):
        """Save conversation history for a session"""
        try:
            memory = self._get_or_create_memory(session_id)
            
            # Add user message
            memory.chat_memory.add_user_message(user_query)
            
            # Add assistant response
            memory.chat_memory.add_ai_message(assistant_response)
            
            logger.info(f" Saved conversation history for session: {session_id}")
            
        except Exception as e:
            logger.error(f" Error saving conversation history: {str(e)}")
    
    def _initialize_db_engine(self):
        """Initialize database engine for SQLite"""
        try:
            from sqlalchemy import create_engine
            # For SQLite, create a proper SQLAlchemy engine with Liara path
            if os.getenv("LIARA_APP_ID"):
                db_dir = "/var/lib/data"
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, "smart_dashboard.db")
                engine = create_engine(f"sqlite:///{db_path}")
            else:
                engine = create_engine("sqlite:///smart_dashboard.db")
            return engine
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            return None
    
    def _get_sql_system_message(self):
        """Get system message for SQL agent"""
        return """You are an AI assistant specialized in generating SQL queries for an agriculture sensor database.

DATABASE SCHEMA:
- Table: sensor_data
  - Columns: id (INTEGER), timestamp (TEXT), sensor_type (TEXT), value (REAL)
  - Sensor types: temperature, humidity, pressure, light, co2_level, wind_speed, rainfall, soil_temperature, soil_moisture, water_usage, pest_count, disease_risk

RULES:
1. Only use SELECT queries
2. Always use the sensor_data table
3. Be specific with WHERE clauses
4. Use appropriate date/time functions for filtering
5. Return structured results

EXAMPLES:
- "last irrigation" -> SELECT * FROM sensor_data WHERE sensor_type = 'water_usage' ORDER BY timestamp DESC LIMIT 1;
- "temperature today" -> SELECT * FROM sensor_data WHERE sensor_type = 'temperature' AND DATE(timestamp) = DATE('now') ORDER BY timestamp DESC;
- "pest trend last 7 days" -> SELECT sensor_type, COUNT(*) as count, AVG(value) as avg_value FROM sensor_data WHERE sensor_type = 'pest_count' AND timestamp >= datetime('now', '-7 days') GROUP BY sensor_type;
"""
    
    def _build_comprehensive_ontology(self) -> Dict[str, Any]:
        """Build comprehensive ontology for agriculture management"""
        return {
            "sensor_mappings": {
                # Environmental Sensors
                "temperature": {
                    "persian_terms": ["دما", "گرما", "حرارت", "درجه حرارت", "دمای هوا", "درجه", "گرمای هوا", "حرارت هوا", "دمای محیط", "گرمای محیط", "حرارت محیط", "دمای گلخانه", "گرمای گلخانه", "حرارت گلخانه"],
                    "english_terms": ["temperature", "temp", "heat", "thermal", "air temperature", "degree", "air heat", "air thermal", "ambient temperature", "ambient heat", "ambient thermal", "greenhouse temperature", "greenhouse heat", "greenhouse thermal"],
                    "unit": "°C",
                    "range": {"min": 15.02, "max": 34.99, "avg": 21.51},
                    "description": "Air temperature readings"
                },
                "humidity": {
                    "persian_terms": ["رطوبت", "نم", "شرجی", "رطوبت هوا", "رطوبت محیط", "نم هوا", "شرجی هوا", "رطوبت گلخانه", "نم گلخانه", "شرجی گلخانه", "رطوبت نسبی", "نم نسبی"],
                    "english_terms": ["humidity", "moisture", "dampness", "air humidity", "ambient humidity", "air moisture", "air dampness", "greenhouse humidity", "greenhouse moisture", "greenhouse dampness", "relative humidity", "relative moisture"],
                    "unit": "%",
                    "range": {"min": 22.50, "max": 89.99, "avg": 72.68},
                    "description": "Air humidity percentage"
                },
                "pressure": {
                    "persian_terms": ["فشار", "هوا", "بارومتر", "فشار هوا"],
                    "english_terms": ["pressure", "atmospheric", "barometric"],
                    "unit": "hPa",
                    "range": {"min": 25.00, "max": 1030.00, "avg": 1004.81},
                    "description": "Atmospheric pressure readings"
                },
                "light": {
                    "persian_terms": ["نور", "روشنایی", "لامپ", "نور خورشید"],
                    "english_terms": ["light", "brightness", "illumination", "lux"],
                    "unit": "lux",
                    "range": {"min": 0.00, "max": 999.60, "avg": 277.57},
                    "description": "Light intensity measurements"
                },
                "co2_level": {
                    "persian_terms": ["دی اکسید کربن", "co2", "کربن دی اکسید"],
                    "english_terms": ["co2", "carbon dioxide", "co2 level"],
                    "unit": "ppm",
                    "range": {"min": 300.00, "max": 600.00, "avg": 425.54},
                    "description": "Carbon dioxide concentration"
                },
                "wind_speed": {
                    "persian_terms": ["سرعت باد", "باد", "سرعت وزش باد"],
                    "english_terms": ["wind", "wind speed", "air velocity"],
                    "unit": "m/s",
                    "range": {"min": 0.00, "max": 20.00, "avg": 10.26},
                    "description": "Wind speed measurements"
                },
                "rainfall": {
                    "persian_terms": ["باران", "بارندگی", "میزان باران"],
                    "english_terms": ["rain", "rainfall", "precipitation"],
                    "unit": "mm",
                    "range": {"min": 0.00, "max": 9.97, "avg": 0.55},
                    "description": "Rainfall measurements"
                },
                
                # Soil Sensors
                "soil_moisture": {
                    "persian_terms": ["رطوبت خاک", "نم خاک", "آب خاک", "خاک", "زمین", "بستر", "رطوبت زمین", "آب زمین", "نم زمین", "خاک مرطوب", "زمین مرطوب", "رطوبت بستر", "آب بستر", "نم بستر"],
                    "english_terms": ["soil moisture", "soil water", "ground moisture", "soil", "ground", "substrate", "ground water", "soil wetness", "ground wetness", "substrate moisture", "substrate water", "substrate wetness"],
                    "unit": "%",
                    "range": {"min": 20.00, "max": 79.86, "avg": 51.18},
                    "description": "Soil moisture percentage"
                },
                "soil_ph": {
                    "persian_terms": ["پی اچ خاک", "اسیدیته خاک", "ph خاک"],
                    "english_terms": ["soil ph", "soil acidity", "ph level"],
                    "unit": "pH",
                    "range": {"min": 5.50, "max": 7.50, "avg": 6.67},
                    "description": "Soil pH level"
                },
                "soil_temperature": {
                    "persian_terms": ["دمای خاک", "حرارت خاک", "گرمای خاک"],
                    "english_terms": ["soil temperature", "ground temperature"],
                    "unit": "°C",
                    "range": {"min": 15.00, "max": 28.00, "avg": 22.30},
                    "description": "Soil temperature readings"
                },
                
                # Plant Growth Sensors
                "plant_height": {
                    "persian_terms": ["قد گیاه", "ارتفاع گیاه", "بلندی گیاه"],
                    "english_terms": ["plant height", "plant growth", "height"],
                    "unit": "cm",
                    "range": {"min": 10.00, "max": 188.54, "avg": 19.99},
                    "description": "Plant height measurements"
                },
                "fruit_count": {
                    "persian_terms": ["تعداد میوه", "شمار میوه", "میوه ها"],
                    "english_terms": ["fruit count", "fruit number", "fruits"],
                    "unit": "count",
                    "range": {"min": 0.00, "max": 19.90, "avg": 1.72},
                    "description": "Number of fruits per plant"
                },
                "fruit_size": {
                    "persian_terms": ["اندازه میوه", "سایز میوه", "بزرگی میوه"],
                    "english_terms": ["fruit size", "fruit diameter", "size"],
                    "unit": "cm",
                    "range": {"min": 1.00, "max": 1.90, "avg": 1.21},
                    "description": "Fruit size measurements"
                },
                
                # Nutrient Sensors
                "nitrogen_level": {
                    "persian_terms": ["نیتروژن", "ازت", "سطح نیتروژن"],
                    "english_terms": ["nitrogen", "n level", "nitrogen content"],
                    "unit": "ppm",
                    "range": {"min": 20.00, "max": 96.57, "avg": 62.96},
                    "description": "Nitrogen level in soil"
                },
                "phosphorus_level": {
                    "persian_terms": ["فسفر", "سطح فسفر", "مقدار فسفر"],
                    "english_terms": ["phosphorus", "p level", "phosphorus content"],
                    "unit": "ppm",
                    "range": {"min": 10.00, "max": 50.00, "avg": 34.97},
                    "description": "Phosphorus level in soil"
                },
                "potassium_level": {
                    "persian_terms": ["پتاسیم", "سطح پتاسیم", "مقدار پتاسیم"],
                    "english_terms": ["potassium", "k level", "potassium content"],
                    "unit": "ppm",
                    "range": {"min": 30.00, "max": 145.65, "avg": 95.59},
                    "description": "Potassium level in soil"
                },
                
                # Pest & Disease Sensors
                "pest_count": {
                    "persian_terms": ["تعداد آفت", "شمار آفت", "آفات", "آفت", "حشره", "حشرات", "مگس", "مگس‌ها", "پشه", "پشه‌ها", "کرم", "کرم‌ها", "لارو", "لاروها", "تخم", "تخم‌ها", "آفت‌ها", "آفات مضر", "حشرات مضر", "رشد آفات", "رشد آفت", "افزایش آفات", "افزایش آفت"],
                    "english_terms": ["pest count", "pest number", "pests", "pest", "insect", "insects", "fly", "flies", "mosquito", "mosquitoes", "worm", "worms", "larva", "larvae", "egg", "eggs", "harmful pests", "harmful insects"],
                    "unit": "count",
                    "range": {"min": 0.00, "max": 48.32, "avg": 1.43},
                    "description": "Number of pests detected"
                },
                "pest_detection": {
                    "persian_terms": ["تشخیص آفت", "شناسایی آفت", "آفت یابی"],
                    "english_terms": ["pest detection", "pest identified", "detection"],
                    "unit": "binary",
                    "range": {"min": 0.00, "max": 1.00, "avg": 0.02},
                    "description": "Pest detection status"
                },
                "disease_risk": {
                    "persian_terms": ["خطر بیماری", "ریسک بیماری", "احتمال بیماری"],
                    "english_terms": ["disease risk", "risk level", "disease probability"],
                    "unit": "%",
                    "range": {"min": 0.00, "max": 98.44, "avg": 47.28},
                    "description": "Disease risk percentage"
                },
                
                # Water Management
                "water_usage": {
                    "persian_terms": ["مصرف آب", "استفاده آب", "آب مصرفی", "آبیاری", "ابیاری", "آب", "آب استفاده شده", "مصرف آب", "استفاده از آب", "آب مصرف شده", "مقدار آب", "حجم آب", "لیتر آب", "آب لیتری"],
                    "english_terms": ["water usage", "water consumption", "water used", "irrigation", "watering", "water", "water consumed", "water usage", "water use", "water consumed", "water amount", "water volume", "water liters", "liters of water"],
                    "unit": "L",
                    "range": {"min": 0.00, "max": 49.74, "avg": 4.33},
                    "description": "Water usage in liters"
                },
                "water_efficiency": {
                    "persian_terms": ["بازدهی آب", "کارایی آب", "مصرف بهینه آب"],
                    "english_terms": ["water efficiency", "water optimization", "efficiency"],
                    "unit": "%",
                    "range": {"min": 61.52, "max": 94.86, "avg": 81.15},
                    "description": "Water usage efficiency"
                },
                
                # Yield & Production
                "yield_prediction": {
                    "persian_terms": ["پیش بینی محصول", "تخمین محصول", "محصول پیش بینی"],
                    "english_terms": ["yield prediction", "crop yield", "predicted yield"],
                    "unit": "kg",
                    "range": {"min": 100.00, "max": 174.51, "avg": 105.50},
                    "description": "Predicted crop yield"
                },
                "yield_efficiency": {
                    "persian_terms": ["بازدهی محصول", "کارایی محصول", "بهره وری"],
                    "english_terms": ["yield efficiency", "production efficiency", "efficiency"],
                    "unit": "%",
                    "range": {"min": 62.57, "max": 89.86, "avg": 86.40},
                    "description": "Crop yield efficiency"
                },
                
                # Market & Economics
                "tomato_price": {
                    "persian_terms": ["قیمت گوجه", "بهای گوجه", "گوجه قیمت"],
                    "english_terms": ["tomato price", "price per kg", "market price"],
                    "unit": "price_per_kg",  # Normalized: removed $ unit not in DB schema
                    "range": {"min": 1.50, "max": 4.46, "avg": 2.71},
                    "description": "Tomato market price"
                },
                "lettuce_price": {
                    "persian_terms": ["قیمت کاهو", "بهای کاهو", "کاهو قیمت"],
                    "english_terms": ["lettuce price", "price per head", "market price"],
                    "unit": "price_per_head",  # Normalized: removed $ unit not in DB schema
                    "range": {"min": 0.80, "max": 2.98, "avg": 1.59},
                    "description": "Lettuce market price"
                },
                "pepper_price": {
                    "persian_terms": ["قیمت فلفل", "بهای فلفل", "فلفل قیمت"],
                    "english_terms": ["pepper price", "price per kg", "market price"],
                    "unit": "price_per_kg",  # Normalized: removed $ unit not in DB schema
                    "range": {"min": 2.01, "max": 5.00, "avg": 3.40},
                    "description": "Pepper market price"
                },
                
                # Additional Sensors
                "motion": {
                    "persian_terms": ["حرکت", "جنبش", "فعالیت"],
                    "english_terms": ["motion", "movement", "activity"],
                    "unit": "count",
                    "range": {"min": 0.00, "max": 30.00, "avg": 0.52},
                    "description": "Motion detection"
                },
                "fertilizer_usage": {
                    "persian_terms": ["مصرف کود", "استفاده کود", "کود مصرفی"],
                    "english_terms": ["fertilizer usage", "fertilizer consumption", "fertilizer used"],
                    "unit": "kg",
                    "range": {"min": 0.00, "max": 5.00, "avg": 0.38},
                    "description": "Fertilizer usage in kilograms"
                },
                "energy_usage": {
                    "persian_terms": ["مصرف انرژی", "استفاده برق", "انرژی مصرفی"],
                    "english_terms": ["energy usage", "power consumption", "energy used"],
                    "unit": "kWh",
                    "range": {"min": 10.00, "max": 195.80, "avg": 26.05},
                    "description": "Energy consumption in kilowatt-hours"
                },
                
                # Normalized: co2 -> co2_level (removed duplicate)
                # Normalized: cost_per_kg -> tomato_price (removed duplicate)
                "demand_level": {
                    "persian_terms": ["سطح تقاضا", "میزان تقاضا", "تقاضا"],
                    "english_terms": ["demand level", "demand", "market demand"],
                    "unit": "level",  # Normalized: removed % unit not in DB schema
                    "range": {"min": 0.00, "max": 100.00, "avg": 75.00},
                    "description": "Market demand level"
                },
                "leaf_count": {
                    "persian_terms": ["تعداد برگ", "شمار برگ", "برگ ها"],
                    "english_terms": ["leaf count", "leaf number", "leaves"],
                    "unit": "count",
                    "range": {"min": 5.00, "max": 50.00, "avg": 25.00},
                    "description": "Number of leaves per plant"
                },
                "leaf_wetness": {
                    "persian_terms": ["رطوبت برگ", "نم برگ", "آب برگ"],
                    "english_terms": ["leaf wetness", "leaf moisture", "foliar wetness"],
                    "unit": "%",
                    "range": {"min": 0.00, "max": 100.00, "avg": 45.00},
                    "description": "Leaf wetness percentage"
                },
                "nutrient_uptake": {
                    "persian_terms": ["جذب مواد مغذی", "مصرف مواد مغذی", "مواد مغذی"],
                    "english_terms": ["nutrient uptake", "nutrient absorption", "nutrient consumption"],
                    "unit": "mg/L",
                    "range": {"min": 0.00, "max": 100.00, "avg": 50.00},
                    "description": "Nutrient uptake rate"
                },
                "profit_margin": {
                    "persian_terms": ["حاشیه سود", "سود", "درآمد"],
                    "english_terms": ["profit margin", "profit", "revenue"],
                    "unit": "%",
                    "range": {"min": 15.00, "max": 35.00, "avg": 25.00},
                    "description": "Profit margin percentage"
                },
                "supply_level": {
                    "persian_terms": ["سطح عرضه", "میزان عرضه", "عرضه"],
                    "english_terms": ["supply level", "supply", "market supply"],
                    "unit": "%",
                    "range": {"min": 0.00, "max": 100.00, "avg": 80.00},
                    "description": "Market supply level percentage"
                },
                "test_temperature": {
                    "persian_terms": ["دما تست", "دمای آزمایش", "تست دما"],
                    "english_terms": ["test temperature", "testing temperature", "experimental temperature"],
                    "unit": "°C",
                    "range": {"min": 15.00, "max": 35.00, "avg": 25.00},
                    "description": "Test temperature readings"
                }
            },
            "query_patterns": {
                "current_value": {
                    "persian": ["الان", "فعلا", "حالا", "اکنون", "امروز"],
                    "english": ["current", "now", "today", "latest", "recent"],
                    "sql_pattern": "SELECT * FROM sensor_data WHERE sensor_type = '{sensor_type}' ORDER BY timestamp DESC LIMIT 1"
                },
                "average_value": {
                    "persian": ["میانگین", "متوسط", "میانه"],
                    "english": ["average", "mean", "avg"],
                    "sql_pattern": "SELECT AVG(value) as avg_value FROM sensor_data WHERE sensor_type = '{sensor_type}'"
                },
                "trend_analysis": {
                    "persian": ["روند", "تغییرات", "نوسانات"],
                    "english": ["trend", "changes", "fluctuations"],
                    "sql_pattern": "SELECT timestamp, value FROM sensor_data WHERE sensor_type = '{sensor_type}' ORDER BY timestamp DESC LIMIT 10"
                },
                "comparison": {
                    "persian": ["مقایسه", "تفاوت", "فرق"],
                    "english": ["compare", "difference", "vs"],
                    "sql_pattern": "SELECT sensor_type, AVG(value) as avg_value FROM sensor_data WHERE sensor_type IN ('{sensor1}', '{sensor2}') GROUP BY sensor_type"
                },
                "time_based": {
                    "persian": ["سه روز", "چهار روز", "پنج روز", "شش روز", "هفت روز", "یک هفته", "دو هفته", "سه هفته", "یک ماه", "دو ماه", "سه ماه", "اخیر", "گذشته", "قبلی"],
                    "english": ["three days", "four days", "five days", "six days", "seven days", "one week", "two weeks", "three weeks", "one month", "two months", "three months", "last", "past", "previous"],
                    "sql_pattern": "SELECT timestamp, value FROM sensor_data WHERE sensor_type = '{sensor_type}' AND timestamp >= datetime('now', '-{days} days') ORDER BY timestamp DESC"
                }
            },
            "chart_patterns": {
                "trend_chart": {
                    "persian": [
                        "روند", "نمودار", "گراف", "تغییرات", "نوسانات", "مقیاس زمانی", 
                        "نمودار روند", "گراف تغییرات", "رشد", "افزایش", "کاهش", 
                        "نمودار رشد", "گراف رشد", "روند رشد", "تغییرات رشد",
                        "نمودار زمانی", "گراف زمانی", "روند زمانی", "تغییرات زمانی",
                        "نمودار سه روز", "نمودار هفته", "نمودار ماه", "نمودار سال",
                        "نمودار اخیر", "نمودار گذشته", "نمودار فعلی"
                    ],
                    "english": [
                        "trend", "chart", "graph", "changes", "fluctuations", "over time", 
                        "timeline", "trend chart", "line chart", "growth", "increase", 
                        "decrease", "growth chart", "growth graph", "growth trend",
                        "time chart", "time graph", "time trend", "time changes",
                        "last 3 days", "last week", "last month", "last year",
                        "recent", "past", "current", "over time"
                    ],
                    "chart_type": "line"
                },
                "comparison_chart": {
                    "persian": [
                        "مقایسه", "تفاوت", "فرق", "نسبت", "مقایسه بین", "نمودار مقایسه", 
                        "گراف مقایسه", "مقایسه با", "نسبت به", "در مقابل", "مقایسه دو",
                        "مقایسه چند", "مقایسه همه", "مقایسه کل", "مقایسه جزئی",
                        "نمودار ستونی", "گراف ستونی", "نمودار میله‌ای", "گراف میله‌ای"
                    ],
                    "english": [
                        "compare", "difference", "vs", "between", "comparison", "ratio", 
                        "comparison chart", "bar chart", "compared to", "relative to", 
                        "versus", "compare two", "compare multiple", "compare all",
                        "column chart", "bar graph", "side by side"
                    ],
                    "chart_type": "bar"
                },
                "distribution_chart": {
                    "persian": [
                        "توزیع", "پراکندگی", "محدوده", "بازه", "نمودار توزیع", 
                        "گراف پراکندگی", "توزیع داده", "پراکندگی داده", "محدوده داده",
                        "بازه داده", "نمودار هیستوگرام", "گراف هیستوگرام", "توزیع آماری",
                        "پراکندگی آماری", "محدوده آماری", "بازه آماری"
                    ],
                    "english": [
                        "distribution", "spread", "range", "variation", "distribution chart", 
                        "histogram", "data distribution", "data spread", "data range",
                        "statistical distribution", "statistical spread", "statistical range"
                    ],
                    "chart_type": "histogram"
                },
                "pie_chart": {
                    "persian": [
                        "درصد", "نسبت", "سهم", "بخش", "نمودار دایره‌ای", 
                        "گراف درصدی", "نمودار کیکی", "گراف کیکی", "نمودار دایره",
                        "گراف دایره", "درصد کل", "نسبت کل", "سهم کل", "بخش کل",
                        "نمودار درصدی", "گراف درصدی", "نمودار نسبی", "گراف نسبی"
                    ],
                    "english": [
                        "percentage", "proportion", "share", "part", "pie chart", 
                        "percentage chart", "circle chart", "donut chart", "percentage of total",
                        "proportion of total", "share of total", "part of total"
                    ],
                    "chart_type": "pie"
                },
                "agricultural_specific": {
                    "persian": [
                        "نمودار کشاورزی", "گراف کشاورزی", "نمودار مزرعه", "گراف مزرعه",
                        "نمودار محصول", "گراف محصول", "نمودار آفات", "گراف آفات",
                        "نمودار آبیاری", "گراف آبیاری", "نمودار کود", "گراف کود",
                        "نمودار برداشت", "گراف برداشت", "نمودار محیط", "گراف محیط",
                        "نمودار خاک", "گراف خاک", "نمودار آب", "گراف آب",
                        "نمودار دما", "گراف دما", "نمودار رطوبت", "گراف رطوبت"
                    ],
                    "english": [
                        "agricultural chart", "farm chart", "crop chart", "pest chart",
                        "irrigation chart", "fertilizer chart", "harvest chart", "environment chart",
                        "soil chart", "water chart", "temperature chart", "humidity chart",
                        "agricultural graph", "farm graph", "crop graph", "pest graph"
                    ],
                    "chart_type": "line"
                }
            },
            "sample_queries": {
                "irrigation": [
                    "رطوبت خاک الان چقدره؟",
                    "آب مصرفی امروز چقدره؟",
                    "بازدهی آب چطوره؟",
                    "نمودار روند آبیاری",
                    "مقایسه مصرف آب",
                    "نمودار رشد مصرف آب در سه روز اخیر",
                    "مقایسه آبیاری بین مناطق مختلف",
                    "توزیع مصرف آب در مزرعه",
                    "درصد مصرف آب هر بخش",
                    "What is the current soil moisture?",
                    "How much water was used today?",
                    "Show me water efficiency trends",
                    "Water usage trend chart",
                    "Compare irrigation between different zones",
                    "Show water distribution histogram"
                ],
                "environment": [
                    "دما الان چقدره؟",
                    "رطوبت هوا چطوره؟",
                    "فشار هوا چقدره؟",
                    "نمودار تغییرات دما",
                    "مقایسه دما و رطوبت",
                    "نمودار رشد آفات در سه روز اخیر",
                    "مقایسه شرایط محیطی بین مناطق",
                    "توزیع دما در مزرعه",
                    "درصد رطوبت نسبی هوا",
                    "نمودار روند تغییرات آب و هوا",
                    "What is the current temperature?",
                    "Show me humidity levels",
                    "Are the environmental conditions optimal?",
                    "Temperature trend over time",
                    "Show pest growth chart for last 3 days",
                    "Environmental distribution histogram"
                ],
                "pest": [
                    "آفات امروز چقدره؟",
                    "خطر بیماری چطوره؟",
                    "تشخیص آفت انجام شده؟",
                    "نمودار توزیع آفات",
                    "مقایسه آفات و بیماری",
                    "نمودار رشد آفات در سه روز اخیر",
                    "مقایسه آفات بین مناطق مختلف",
                    "توزیع آفات در مزرعه",
                    "درصد آفات هر نوع",
                    "نمودار روند افزایش آفات",
                    "What pests have been detected today?",
                    "Show me disease risk levels",
                    "Is pest detection active?",
                    "Pest distribution chart",
                    "Show pest growth trend for last 3 days",
                    "Compare pest levels between zones"
                ],
                "growth": [
                    "قد گیاه چقدره؟",
                    "تعداد میوه چقدره؟",
                    "پیش بینی محصول چطوره؟",
                    "نمودار رشد گیاه",
                    "مقایسه اندازه میوه",
                    "What is the plant height?",
                    "How many fruits are there?",
                    "Show me yield predictions",
                    "Plant growth trend chart"
                ],
                "market": [
                    "قیمت گوجه چقدره؟",
                    "بهای کاهو چطوره؟",
                    "قیمت فلفل چقدره؟",
                    "نمودار قیمت‌ها",
                    "مقایسه قیمت محصولات",
                    "What is the tomato price?",
                    "Show me lettuce prices",
                    "How are pepper prices trending?",
                    "Price comparison chart"
                ]
            }
        }
    
    def _get_live_sensor_data(self, sensor_types: List[str] = None) -> List[Dict[str, Any]]:
        """Get live sensor data from SQLite database"""
        try:
            # Use proper database path for Liara
            if os.getenv("LIARA_APP_ID"):
                db_dir = "/var/lib/data"
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, "smart_dashboard.db")
            else:
                db_path = "smart_dashboard.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            if sensor_types:
                # Get specific sensor types
                placeholders = ','.join(['?' for _ in sensor_types])
                query = f"""
                    SELECT timestamp, sensor_type, value 
                    FROM sensor_data 
                    WHERE sensor_type IN ({placeholders})
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """
                cursor.execute(query, sensor_types)
            else:
                # Get all recent data
                cursor.execute("""
                    SELECT timestamp, sensor_type, value 
                    FROM sensor_data 
                    ORDER BY timestamp DESC 
                    LIMIT 20
                """)
            
            results = cursor.fetchall()
            live_data = []
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
    
    def process_query(self, query: str, feature_context: str = "dashboard", session_id: str = "default", intent: str = "data_query", is_comparison: bool = False) -> Dict[str, Any]:
        """Main processing function with conversation history"""
        try:
            logger.info(f" Processing query: '{query}' for session: {session_id} with intent: {intent}")
            
            # Get conversation history
            conversation_context = self._get_conversation_context(session_id)
            logger.info(f" Conversation context: {len(conversation_context)} characters")
            
            # Step 1: Detect language
            detected_lang = self.translator.detect_language(query)
            translated_query = query
            
            # Step 2: If Persian, translate to English using LLM
            if detected_lang == 'fa':
                translated_query = self.translator.translate_query_to_english(query)
                logger.info(f" LLM Translated Persian query to English: {translated_query}")
            
            # Step 2.1: Parse time context using the new time_parser
            time_context = parse_time_context(translated_query)
            logger.info(f" Time context parsed: {time_context}")
            
            # Step 2.5: Detect comparison intent if not already set
            if not is_comparison:
                is_comparison = self._detect_comparison_intent(translated_query)
                logger.info(f" Comparison detection result: {is_comparison}")
            
            # NEW: Handle alert management intent
            if intent == "alert_management":
                return self._process_alert_query(translated_query, session_id, detected_lang)
            
            # Step 3: Generate and execute SQL using LangChain SQLDatabaseChain
            sql_result = self._generate_and_execute_sql(translated_query, feature_context, conversation_context, is_comparison, time_context)
            
            # Step 3.1: Log SQL for debugging time filtering
            if sql_result.get("sql"):
                sql_query = sql_result["sql"]
                logger.info(f"🔍 GENERATED SQL: {sql_query}")
                
                # Check if SQL contains proper time filtering
                if "timestamp" in sql_query.lower() and ("between" in sql_query.lower() or ">=" in sql_query.lower()):
                    logger.info(f"✅ SQL contains time filtering")
                else:
                    logger.warning(f"⚠️ SQL may be missing time filtering")
            else:
                logger.warning(f"⚠️ No SQL generated")
            
            # Step 3.5: Check if SQL execution failed
            if not sql_result.get("success", False):
                logger.error(f" SQL Execution Failed: {sql_result.get('error', 'Unknown error')}")
                error_response = {
                    "success": False,
                    "error": sql_result.get("error", "SQL execution failed"),
                    "query": query,
                    "translated_query": translated_query,
                    "sql": sql_result.get("sql", ""),
                    "validation": sql_result.get("validation", {}),
                    "language": detected_lang,
                    "feature_context": feature_context,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # If original was Persian, translate error to Persian
                if detected_lang == 'fa':
                    error_response["error"] = f"خطا در اجرای درخواست: {sql_result.get('error', 'خطای نامشخص')}"
                
                logger.error(f" BLOCKING RESPONSE: SQL execution failed, returning error instead of generating response")
                return error_response
            
            # Step 3.6: Check if no data was retrieved
            data_points = len(sql_result.get("raw_data", []))
            if data_points == 0:
                logger.warning(f" NO DATA RETRIEVED: SQL executed successfully but returned 0 data points")
                no_data_response = {
                    "success": True,
                    "response": "No data available for the requested time range and sensor type.",
                    "data": [],
                    "sql": sql_result.get("sql", ""),
                    "validation": sql_result.get("validation", {}),
                    "language": detected_lang,
                    "feature_context": feature_context,
                    "timestamp": datetime.utcnow().isoformat(),
                    "data_points": 0
                }
                
                # If original was Persian, translate to Persian
                if detected_lang == 'fa':
                    no_data_response["response"] = "هیچ داده‌ای برای بازه زمانی و نوع حسگر درخواستی موجود نیست."
                
                logger.warning(f" BLOCKING RESPONSE: No data retrieved, returning no-data response instead of generating fake data")
                return no_data_response
            
            # Step 4: Format result into structured JSON (only if SQL execution succeeded)
            structured_result = self._format_structured_response(sql_result, translated_query, feature_context, intent, query, detected_lang, time_context)
            
            # Step 5: If original was Persian, translate response back to Persian using LLM
            if detected_lang == 'fa':
                structured_result = self._translate_response_to_persian(structured_result)
            
            # Step 6: Save conversation history
            self._save_conversation_history(session_id, query, structured_result.get('summary', 'No response'))
            
            logger.info(f" Query processed successfully with conversation history")
            return structured_result
            
        except Exception as e:
            logger.error(f" Dynamic SQL Service Error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "query": query
            }
    
    def _detect_comparison_intent(self, query: str) -> bool:
        """Detect comparison intent from query - English only (after LLM translation)"""
        query_lower = query.lower()
        
        # STRICT comparison detection - only detect when user explicitly wants comparison
        
        # 1. EXPLICIT comparison keywords (high confidence)
        explicit_comparison_keywords = [
            "compare", "comparison", "vs", "versus", "against", "between", "difference", "compared to",
            "contrast", "versus", "against", "relative to", "in relation to"
        ]
        
        # 2. EXPLICIT time comparison patterns (high confidence)
        explicit_time_comparison_patterns = [
            "today vs yesterday", "today and yesterday", "this week vs last week", "this month vs last month",
            "this year vs last year", "current vs previous", "now vs then", "recent vs past",
            "last week vs this week", "last month vs this month", "yesterday vs today",
            "previous vs current", "old vs new", "past vs present", "past vs future"
        ]
        
        # 3. EXPLICIT trend analysis patterns (medium confidence - only if they mention comparison)
        trend_comparison_patterns = [
            "trend comparison", "trend difference", "trend vs", "trend versus",
            "growth trend vs", "growth trend versus", "growth trend comparison",
            "trend analysis vs", "trend analysis versus", "trend analysis comparison"
        ]
        
        # 4. EXPLICIT statistical comparison terms (medium confidence)
        statistical_comparison_patterns = [
            "correlation between", "relationship between", "connection between", "association between",
            "variation between", "difference between", "comparison between"
        ]
        
        # Check for explicit comparison keywords
        has_explicit_comparison = any(word in query_lower for word in explicit_comparison_keywords)
        
        # Check for explicit time comparison patterns
        has_explicit_time_comparison = any(pattern in query_lower for pattern in explicit_time_comparison_patterns)
        
        # Check for trend comparison patterns (only if they explicitly mention comparison)
        has_trend_comparison = any(pattern in query_lower for pattern in trend_comparison_patterns)
        
        # Check for statistical comparison patterns
        has_statistical_comparison = any(pattern in query_lower for pattern in statistical_comparison_patterns)
        
        # Additional checks for explicit comparison intent
        has_explicit_between = "between" in query_lower and any(word in query_lower for word in ["and", "vs", "versus"])
        has_explicit_vs = "vs" in query_lower or "versus" in query_lower
        has_explicit_compare = "compare" in query_lower or "comparison" in query_lower
        
        # Only return True if we have STRONG evidence of comparison intent
        is_comparison = (
            has_explicit_comparison or 
            has_explicit_time_comparison or 
            has_trend_comparison or 
            has_statistical_comparison or
            has_explicit_between or
            has_explicit_vs or
            has_explicit_compare
        )
        
        return is_comparison
    
    def _expand_time_ranges(self, detected_range: str, time_config: Dict[str, Any], is_comparison: bool = False) -> List[str]:
        """Expand user phrases into explicit time ranges for comparison using canonical format"""
        try:
            import re
            
            # Only expand for actual comparison queries
            if not is_comparison:
                return [detected_range] if detected_range else []
            
            # Handle specific time expressions with canonical format
            if "hours_ago" in detected_range:
                # Extract number of hours
                hour_match = re.search(r'(\d+)_hours_ago', detected_range)
                if hour_match:
                    hours = int(hour_match.group(1))
                    # For comparison queries, create multiple time periods
                    # For 4 hours, create: 1_hours_ago, 2_hours_ago, 3_hours_ago, 4_hours_ago
                    ranges = []
                    for i in range(1, hours + 1):
                        ranges.append(f"{i}_hours_ago")
                    return ranges
            
            # Handle time_config based expansion (when detected_range is not specific)
            elif time_config and "hours" in time_config:
                hours = time_config["hours"]
                # For comparison queries, create multiple time periods
                ranges = []
                for i in range(1, hours + 1):
                    ranges.append(f"{i}_hours_ago")
                return ranges
            
            elif "days_ago" in detected_range:
                # Extract number of days
                day_match = re.search(r'(\d+)_days_ago', detected_range)
                if day_match:
                    days = int(day_match.group(1))
                    # For comparison queries, create multiple time periods
                    ranges = []
                    for i in range(1, days + 1):
                        ranges.append(f"{i}_days_ago")
                    return ranges
            
            elif "weeks_ago" in detected_range:
                # Extract number of weeks
                week_match = re.search(r'(\d+)_weeks_ago', detected_range)
                if week_match:
                    weeks = int(week_match.group(1))
                    # For comparison queries, create multiple time periods
                    ranges = []
                    for i in range(1, weeks + 1):
                        ranges.append(f"{i}_weeks_ago")
                    return ranges
            
            # Handle granular time expressions - use canonical format consistently
            if time_config.get("granularity") == "hour":
                hours = time_config.get("hours", 1)
                # For comparison queries, create multiple time periods
                ranges = []
                for i in range(1, hours + 1):
                    ranges.append(f"{i}_hours_ago")
                return ranges
            elif time_config.get("granularity") == "day":
                days = time_config.get("days", 1)
                # For comparison queries, create multiple time periods
                ranges = []
                for i in range(1, days + 1):
                    ranges.append(f"{i}_days_ago")
                return ranges
            elif time_config.get("granularity") == "week":
                weeks = time_config.get("weeks", 1)
                # For comparison queries, create multiple time periods
                ranges = []
                for i in range(1, weeks + 1):
                    ranges.append(f"{i}_weeks_ago")
                return ranges
            
            # Default fallback
            return [detected_range]
                
        except Exception as e:
            logger.error(f"Error expanding time ranges: {e}")
            return [detected_range]

    def _compute_previous_time_range(self, time_range: str) -> str:
        """Compute the previous time range for comparison queries"""
        # Handle days_ago_X format specifically
        if time_range.startswith("days_ago_"):
            try:
                days = int(time_range.split("_")[2])
                return f"days_ago_{days + 1}"
            except (IndexError, ValueError):
                return f"previous_{time_range}"
        
        range_mapping = {
            "today": "yesterday",
            "yesterday": "day_before_yesterday", 
            "last_week": "previous_week",
            "this_week": "last_week",
            "last_month": "previous_month",
            "this_month": "last_month",
            "last_year": "previous_year",
            "this_year": "last_year",
            "last_3_days": "previous_3_days",
            "last_7_days": "previous_7_days",
            "last_30_days": "previous_30_days"
        }
        
        return range_mapping.get(time_range, f"previous_{time_range}")
    
    def _time_range_to_sql_filter(self, time_range: str, reference: str = "now") -> tuple:
        """Convert time range to SQL filter with smart time boundaries"""
        import datetime
        import re
        
        # Get current date for calculations - use UTC for consistency
        now = datetime.datetime.now(datetime.timezone.utc)
        
        # Handle canonical format: 1_hours_ago, 2_hours_ago, etc.
        if time_range.endswith("_hours_ago"):
            m = re.search(r'(\d+)_hours_ago', time_range)
            hours = int(m.group(1)) if m else 1
            # Correct semantics: X_hours_ago = window [now - X hours, now - (X-1) hours)
            # 1_hours_ago → [now - 1h, now)
            # 2_hours_ago → [now - 2h, now - 1h)
            start_date = now - datetime.timedelta(hours=hours)
            end_date = now - datetime.timedelta(hours=hours-1)
            label = f"{hours}_hours_ago"
            
        # Handle canonical format: 1_days_ago, 2_days_ago, etc.
        elif time_range.endswith("_days_ago"):
            m = re.search(r'(\d+)_days_ago', time_range)
            days = int(m.group(1)) if m else 1
            # Correct semantics: X_days_ago = window [target_day 00:00:00, target_day +1 00:00:00)
            # 1_days_ago → [yesterday 00:00, today 00:00)
            # 2_days_ago → [day_before_yesterday 00:00, yesterday 00:00)
            target = now - datetime.timedelta(days=days)
            start_date = target.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + datetime.timedelta(days=1)
            label = f"{days}_days_ago"
            
        # Handle canonical format: 1_weeks_ago, 2_weeks_ago, etc.
        elif time_range.endswith("_weeks_ago"):
            m = re.search(r'(\d+)_weeks_ago', time_range)
            weeks = int(m.group(1)) if m else 1
            # Correct semantics: X_weeks_ago = window [target_week_start, target_week_start + 7 days)
            # 1_weeks_ago → [last_week_monday 00:00, this_week_monday 00:00)
            # 2_weeks_ago → [week_before_last_monday 00:00, last_week_monday 00:00)
            target = now - datetime.timedelta(weeks=weeks)
            # Get start of week (Monday)
            days_since_monday = target.weekday()
            week_start = target - datetime.timedelta(days=days_since_monday)
            start_date = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + datetime.timedelta(days=7)
            label = f"{weeks}_weeks_ago"
            
        # Handle legacy formats for backward compatibility
        elif time_range == "today":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + datetime.timedelta(days=1)
            label = "today"
        elif time_range == "yesterday":
            # Yesterday = yesterday 00:00 to today 00:00
            yesterday = now - datetime.timedelta(days=1)
            start_date = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            label = "yesterday"
        elif time_range.startswith("last_") and time_range.endswith("_days"):
            # e.g., last_3_days -> rolling N days
            try:
                n = int(time_range.split("_")[1])
            except Exception:
                n = 3
            start_date = now - datetime.timedelta(days=n)
            end_date = now
            label = time_range
        elif time_range.startswith("previous_") and time_range.endswith("_days"):
            # previous_3_days -> prior N-day window before last_N_days
            try:
                n = int(time_range.split("_")[1])
            except Exception:
                n = 3
            # Smart logic: previous_3_days = 3 days before the last 3 days
            start_date = now - datetime.timedelta(days=2*n)
            end_date = now - datetime.timedelta(days=n)
            label = f"previous_{n}_days"
        elif time_range == "last_week":
            # Last 7 days (rolling)
            start_date = now - datetime.timedelta(days=7)
            end_date = now
            label = "last_week"
        elif time_range == "previous_week":
            # Previous week = 7 days before last week
            start_date = now - datetime.timedelta(days=14)
            end_date = now - datetime.timedelta(days=7)
            label = "previous_week"
        elif time_range == "last_month":
            # Last 30 days (rolling)
            start_date = now - datetime.timedelta(days=30)
            end_date = now
            label = "last_month"
        elif time_range == "previous_month":
            # Previous month = 30 days before last month
            start_date = now - datetime.timedelta(days=60)
            end_date = now - datetime.timedelta(days=30)
            label = "previous_month"
        elif time_range == "last_3_days":
            start_date = now - datetime.timedelta(days=3)
            end_date = now
            label = "last_3_days"
        elif time_range == "previous_3_days":
            # Previous 3 days = 3 days before the last 3 days
            start_date = now - datetime.timedelta(days=6)
            end_date = now - datetime.timedelta(days=3)
            label = "previous_3_days"
        else:
            # Default to last 24 hours
            start_date = now - datetime.timedelta(days=1)
            end_date = now
            label = time_range
        
        # Format for SQLite with exclusive end semantics - ensure UTC
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=datetime.timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=datetime.timezone.utc)
            
        start_iso = start_date.strftime("%Y-%m-%dT%H:%M:%S")
        end_iso = end_date.strftime("%Y-%m-%dT%H:%M:%S")
        
        # Use exclusive end semantics: >= start AND < end
        sqlite_condition = f"timestamp >= '{start_iso}' AND timestamp < '{end_iso}'"
        
        return (label, start_iso, end_iso, sqlite_condition)

    def _generate_semantic_json(self, english_query: str, language: str = "en", is_comparison: bool = False) -> Dict[str, Any]:
        """Generate semantic JSON from natural language query using LLM"""
        try:
            logger.info(f" Generating semantic JSON for: '{english_query}' (comparison: {is_comparison})")
            
            # Use the passed comparison flag instead of detecting it again
            print(f" COMPARISON DETECTION: query={len(english_query)} characters, is_comparison={is_comparison}")
            
            # Get mapping metadata
            mapping_result = self._map_query_to_sensor_type(english_query, language)
            sensor_type = mapping_result["sensor_type"]
            mapping_type = mapping_result.get("mapping_type", "unknown")
            
            # Override mapping_type if comparison detected
            if is_comparison:
                mapping_type = "comparison"
                print(f" OVERRIDE: Set mapping_type to 'comparison'")
            
            # Parse time expression
            time_config = self._parse_time_expression(english_query, language)
            print(f" TIME CONFIG: {time_config}")
            
            # Build semantic JSON based on mapping and time config
            semantic_json = self._build_semantic_json_from_mapping(sensor_type, time_config, english_query, mapping_type)
            
            # Validate semantic JSON
            validation_result = self.query_builder.validate_semantic_json(semantic_json)
            if not validation_result["valid"]:
                logger.error(f" Semantic JSON validation failed: {validation_result['error']}")
                # Return fallback semantic JSON with validation feedback
                return self._get_fallback_semantic_json(sensor_type, validation_result)
            
            print(f" SEMANTIC JSON BUILT: {semantic_json}")
            logger.info(f" Generated semantic JSON: {semantic_json}")
            return semantic_json
            
        except Exception as e:
            logger.error(f" Error generating semantic JSON: {e}")
            return self._get_fallback_semantic_json("temperature")
    
    def _build_semantic_json_from_mapping(self, sensor_type: str, time_config: Dict[str, Any], english_query: str, mapping_type: str = "unknown") -> Dict[str, Any]:
        """Build semantic JSON from sensor mapping and time configuration"""
        try:
            query_lower = english_query.lower()
            
            # Use mapping_type to determine if this is a comparison query
            is_comparison = mapping_type == "comparison"
            print(f" MAPPING TYPE: {mapping_type}, IS_COMPARISON: {is_comparison}")
            
            # Detect multiple time ranges for comparison
            time_ranges = self._detect_comparison_time_ranges(english_query, query_lower)
            print(f" TIME RANGES: {time_ranges}")
            
            # Handle comparison queries first
            if is_comparison:
                if len(time_ranges) > 1:
                    # Multiple time ranges detected
                    semantic_json = {
                        "entity": sensor_type,
                        "aggregation": "average",
                        "time_range": time_ranges,
                        "comparison": True,
                        "grouping": "by_day",
                        "format": "comparison"
                    }
                else:
                    # Single time range detected - expand to comparison pair
                    detected_range = time_ranges[0] if time_ranges else time_config.get("range", "last_week")
                    
                    # EXPAND TIME RANGES: Convert user phrases to explicit ranges
                    expanded_ranges = self._expand_time_ranges(detected_range, time_config, is_comparison)
                    print(f" EXPANDED TIME RANGES: {expanded_ranges}")
                    
                    # Set appropriate grouping based on time_config granularity (prioritize over detected_range)
                    if time_config and "granularity" in time_config:
                        granularity = time_config["granularity"]
                        if granularity == "day":
                            grouping = "by_day"
                        elif granularity == "hour":
                            grouping = "by_hour"
                        elif granularity == "minute":
                            grouping = "by_minute"
                        elif granularity == "week":
                            grouping = "by_week"
                        elif granularity == "month":
                            grouping = "by_month"
                        else:
                            grouping = "by_day"  # default
                    else:
                        # Fallback to detected_range pattern
                        if "week" in detected_range:
                            grouping = "by_week"
                        elif "month" in detected_range:
                            grouping = "by_month"
                        elif "day" in detected_range or detected_range in ["today", "yesterday"]:
                            grouping = "by_day"
                        elif "hour" in detected_range:
                            grouping = "by_hour"
                        else:
                            grouping = "by_day"  # default
                    
                    semantic_json = {
                        "entity": sensor_type,
                        "aggregation": "average",
                        "time_range": expanded_ranges,
                        "comparison": True,
                        "grouping": grouping,
                        "format": "comparison"
                    }
                    print(f" EXPANDED COMPARISON: {expanded_ranges}, grouping: {grouping}")
            # Handle compound queries (sensor_type is already a list)
            elif isinstance(sensor_type, list):
                semantic_json = {
                    "entity": sensor_type,
                    "aggregation": "average",
                    "time_range": "last_24_hours",
                    "comparison": False,
                    "grouping": "none",
                    "format": "comparison"
                }
            else:
                # Single entity (non-comparison)
                semantic_json = {
                    "entity": sensor_type,
                    "aggregation": "current",
                    "time_range": "last_24_hours",
                    "comparison": False,
                    "grouping": "none",
                    "format": "value"
                }
            
            # Update based on time configuration (but preserve expanded ranges for comparison queries)
            # CRITICAL: Do not override time_range for comparison queries that already have a list
            is_comparison_with_list = (semantic_json.get("comparison", False) and 
                                    isinstance(semantic_json.get("time_range"), list))
            
            logger.debug(f"Time config override check: is_comparison_with_list={is_comparison_with_list}, "
                        f"comparison={semantic_json.get('comparison')}, "
                        f"time_range_type={type(semantic_json.get('time_range'))}, "
                        f"time_range={semantic_json.get('time_range')}")
            
            if time_config and not is_comparison_with_list:
                if "days" in time_config:
                    days = time_config["days"]
                    semantic_json["time_range"] = self._map_days_to_time_range(days)
                
            if "hours" in time_config:
                hours = time_config["hours"]
                semantic_json["time_range"] = self._map_hours_to_time_range(hours)
                
                if "minutes" in time_config:
                    minutes = time_config["minutes"]
                    semantic_json["time_range"] = self._map_minutes_to_time_range(minutes)
                
                # Set grouping based on granularity (only for non-comparison queries)
                granularity = time_config.get("granularity", "day")
                print(f" GRANULARITY: {granularity}")
                if granularity == "day":
                    semantic_json["grouping"] = "by_day"
                elif granularity == "hour":
                    semantic_json["grouping"] = "by_hour"
                elif granularity == "minute":
                    semantic_json["grouping"] = "by_minute"
                elif granularity == "week":
                    semantic_json["grouping"] = "by_week"
                print(f" GROUPING SET TO: {semantic_json['grouping']}")
            elif is_comparison_with_list:
                print(f" PRESERVING COMPARISON TIME_RANGE: {semantic_json.get('time_range')}")
            
            # Update aggregation based on query patterns
            if any(word in query_lower for word in ["average", "mean", "avg", "میانگین", "متوسط"]):
                semantic_json["aggregation"] = "average"
            elif any(word in query_lower for word in ["current", "latest", "now", "today", "الان", "فعلا", "امروز"]):
                semantic_json["aggregation"] = "current"
            elif any(word in query_lower for word in ["trend", "changes", "over time", "روند", "تغییرات"]):
                semantic_json["format"] = "trend"
                semantic_json["aggregation"] = "average"
            elif any(word in query_lower for word in ["compare", "comparison", "مقایسه", "تفاوت"]):
                semantic_json["format"] = "comparison"
                semantic_json["aggregation"] = "average"
            
            return semantic_json
            
        except Exception as e:
            logger.error(f" Error building semantic JSON: {e}")
            return self._get_fallback_semantic_json(sensor_type)
    
    def _detect_comparison_time_ranges(self, english_query: str, query_lower: str) -> List[str]:
        """ROBUST COMPARISON TIME RANGE DETECTOR: Handle ALL comparison scenarios intelligently"""
        time_ranges = []
        
        # Only detect comparison time ranges if the query explicitly mentions comparison
        has_explicit_comparison = any(word in query_lower for word in [
            "compare", "comparison", "vs", "versus", "against", "between", "difference", "compared to",
            "contrast", "relative to", "in relation to"
        ])
        
        if not has_explicit_comparison:
            return time_ranges  # Return empty list for non-comparison queries
        
        # ROBUST COMPARISON PATTERNS - Handle ALL comparison scenarios
        import re
        
        # 1. "Compare X vs Y" patterns
        compare_vs_pattern = re.search(r'compare\s+(.+?)\s+(?:vs|versus|against)\s+(.+?)', query_lower)
        if compare_vs_pattern:
            period1 = compare_vs_pattern.group(1).strip()
            period2 = compare_vs_pattern.group(2).strip()
            time_ranges = [self._map_time_period_to_range(period1), self._map_time_period_to_range(period2)]
            return time_ranges
        
        # 2. "Between X and Y" patterns
        between_pattern = re.search(r'between\s+(.+?)\s+and\s+(.+?)', query_lower)
        if between_pattern:
            period1 = between_pattern.group(1).strip()
            period2 = between_pattern.group(2).strip()
            time_ranges = [self._map_time_period_to_range(period1), self._map_time_period_to_range(period2)]
            return time_ranges
        
        # 3. "X vs Y" patterns
        vs_pattern = re.search(r'(.+?)\s+(?:vs|versus)\s+(.+?)', query_lower)
        if vs_pattern:
            period1 = vs_pattern.group(1).strip()
            period2 = vs_pattern.group(2).strip()
            time_ranges = [self._map_time_period_to_range(period1), self._map_time_period_to_range(period2)]
            return time_ranges
        
        # 4. "X hours ago" patterns (only for comparison)
        hours_ago_match = re.search(r'(\d+)\s*hours?\s*ago', query_lower)
        if hours_ago_match:
            hours = int(hours_ago_match.group(1))
            time_ranges = [f"hours_ago_{hours}", f"hours_ago_{hours + 1}"]
            return time_ranges

        # 5. "last/past N days" patterns (only for comparison)
        last_days = re.search(r'(?:last|past)\s*(\d+)\s*days?', query_lower)
        if last_days:
            n = int(last_days.group(1))
            time_ranges = [f"last_{n}_days", f"previous_{n}_days"]
            return time_ranges
        
        # 6. "last/past N hours" patterns (only for comparison)
        last_hours = re.search(r'(?:last|past)\s*(\d+)\s*hours?', query_lower)
        if last_hours:
            n = int(last_hours.group(1))
            time_ranges = [f"last_{n}_hours", f"previous_{n}_hours"]
            return time_ranges

        return time_ranges
    
    def _map_time_period_to_range(self, period: str) -> str:
        """Map a time period description to a time range"""
        period_lower = period.lower().strip()
        
        # Map common time period descriptions
        period_mapping = {
            "today": "today",
            "yesterday": "yesterday", 
            "last week": "last_week",
            "this week": "this_week",
            "last month": "last_month",
            "this month": "this_month",
            "last year": "last_year",
            "this year": "this_year",
            "last hour": "last_hour",
            "this hour": "this_hour",
            "last day": "last_day",
            "this day": "this_day"
        }
        
        # Check for exact matches first
        if period_lower in period_mapping:
            return period_mapping[period_lower]
        
        # Check for "last N days/hours" patterns
        import re
        last_days_match = re.search(r'last\s+(\d+)\s+days?', period_lower)
        if last_days_match:
            n = int(last_days_match.group(1))
            return f"last_{n}_days"
        
        last_hours_match = re.search(r'last\s+(\d+)\s+hours?', period_lower)
        if last_hours_match:
            n = int(last_hours_match.group(1))
            return f"last_{n}_hours"
        
        # Default fallback
        return period_lower

    def _process_comparison_data(self, raw_data: List[Dict[str, Any]], time_ranges: List[str]) -> Dict[str, Any]:
        """Process comparison data to compute deltas and percentage changes"""
        try:
            if not raw_data or len(time_ranges) < 2:
                return None
            
            # Group data by time period and sensor type
            grouped_data = {}
            for item in raw_data:
                time_period = item.get("time_period", "")
                sensor_type = item.get("sensor_type", "unknown")
                avg_value = item.get("avg_value", 0)
                
                if time_period not in grouped_data:
                    grouped_data[time_period] = {}
                grouped_data[time_period][sensor_type] = avg_value
            
            # Map time periods to time ranges
            time_period_mapping = {}
            for i, time_range in enumerate(time_ranges):
                # Find the closest time period for this range
                for time_period in grouped_data.keys():
                    if self._time_period_matches_range(time_period, time_range):
                        time_period_mapping[time_range] = time_period
                        break
            
            # Compute comparison metrics
            comparison_results = {}
            for sensor_type in set([item.get("sensor_type") for item in raw_data]):
                sensor_comparison = {}
                
                # Get values for each time range
                for time_range in time_ranges:
                    time_period = time_period_mapping.get(time_range)
                    if time_period and time_period in grouped_data:
                        value = grouped_data[time_period].get(sensor_type, 0)
                        sensor_comparison[time_range] = value
                
                # Compute deltas if we have at least 2 values
                if len(sensor_comparison) >= 2:
                    values = list(sensor_comparison.values())
                    if len(values) == 2:
                        # Two-period comparison
                        old_value, new_value = values
                        delta = new_value - old_value
                        percent_change = (delta / old_value * 100) if old_value != 0 else 0
                        
                        sensor_comparison["delta"] = delta
                        sensor_comparison["percent_change"] = percent_change
                        sensor_comparison["trend"] = "increasing" if delta > 0 else "decreasing" if delta < 0 else "stable"
                
                comparison_results[sensor_type] = sensor_comparison
            
            return {
                "time_ranges": time_ranges,
                "time_period_mapping": time_period_mapping,
                "sensor_comparisons": comparison_results,
                "overall_trend": self._compute_overall_trend(comparison_results)
            }
            
        except Exception as e:
            logger.error(f" Error processing comparison data: {e}")
            return None
    
    def _time_period_matches_range(self, time_period: str, time_range: str) -> bool:
        """Check if a time period matches a specific time range"""
        try:
            from datetime import datetime, timedelta
            
            # Parse time period (format: YYYY-MM-DD or YYYY-WW)
            if len(time_period) == 10:  # YYYY-MM-DD format
                period_date = datetime.strptime(time_period, "%Y-%m-%d").date()
                today = datetime.now().date()
                
                if time_range == "today":
                    return period_date == today
                elif time_range == "yesterday":
                    return period_date == today - timedelta(days=1)
                elif time_range == "this_week":
                    week_start = today - timedelta(days=today.weekday())
                    return week_start <= period_date <= today
                elif time_range == "last_week":
                    week_start = today - timedelta(days=today.weekday())
                    last_week_start = week_start - timedelta(days=7)
                    last_week_end = week_start - timedelta(days=1)
                    return last_week_start <= period_date <= last_week_end
            
            return False
            
        except Exception as e:
            logger.error(f" Error matching time period: {e}")
            return False
    
    def _compute_overall_trend(self, comparison_results: Dict[str, Any]) -> str:
        """Compute overall trend across all sensors"""
        try:
            trends = []
            for sensor_type, comparison in comparison_results.items():
                if "trend" in comparison:
                    trends.append(comparison["trend"])
            
            if not trends:
                return "unknown"
            
            # Count trends
            increasing = trends.count("increasing")
            decreasing = trends.count("decreasing")
            stable = trends.count("stable")
            
            if increasing > decreasing and increasing > stable:
                return "increasing"
            elif decreasing > increasing and decreasing > stable:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            logger.error(f" Error computing overall trend: {e}")
            return "unknown"

    def _get_fallback_semantic_json(self, sensor_type: str, validation_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get fallback semantic JSON with validation feedback"""
        # Check if entity is missing and provide feedback
        if validation_result and "missing_entity" in validation_result.get("error", ""):
            logger.warning(f"  Entity missing in semantic JSON, defaulting to temperature. Original sensor_type: {sensor_type}")
            sensor_type = "temperature"  # Default fallback
        
        if isinstance(sensor_type, list):
            entities = sensor_type
            return {
                "entity": entities,
                "aggregation": "current",
                "time_range": "last_24_hours",
                "comparison": False,
                "grouping": "none",
                "format": "value",
                "fallback_reason": validation_result.get("error", "unknown") if validation_result else "default"
            }
        else:
            return {
                "entity": sensor_type,
                "aggregation": "current",
                "time_range": "last_24_hours",
                "comparison": False,
                "grouping": "none",
                "format": "value",
                "fallback_reason": validation_result.get("error", "unknown") if validation_result else "default"
            }
    
    def _generate_and_execute_sql(self, english_query: str, feature_context: str, conversation_context: str = "", is_comparison: bool = False, time_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate and execute SQL query using semantic JSON flow with fallback mechanism"""
        try:
            logger.info(f" Generating SQL using semantic JSON flow for: '{english_query}' (comparison: {is_comparison})")
            
            # Step 1: Generate semantic JSON from natural language query
            semantic_json = self._generate_semantic_json(english_query, language="en", is_comparison=is_comparison)
            print(f" SEMANTIC JSON GENERATED: {semantic_json}")
            logger.info(f" Generated semantic JSON: {semantic_json}")
            
            # Step 2: Convert semantic JSON to SQL using QueryBuilder
            # Include time_context in semantic_json metadata
            if time_context:
                semantic_json["time_context"] = time_context
            sql_query = self.query_builder.build_sql_from_semantic_json(semantic_json)
            print(f" SQL FROM SEMANTIC JSON: {sql_query}")
            logger.info(f" Generated SQL from semantic JSON: {sql_query}")
            logger.debug(f"SQL generation details: semantic_json={semantic_json} -> sql={sql_query}")
            
            # Step 3: Execute SQL with validation
            execution_result = self._execute_direct_sql(sql_query)
            
            # Step 4: Check if execution was successful
            if not execution_result["success"]:
                logger.error(f" SQL Execution Failed: {execution_result['error']}")
                logger.error(f" ERROR: SQL execution failed for query: {sql_query}")
                logger.error(f" ERROR: Execution result: {execution_result}")
                return {
                    "sql": sql_query,
                    "raw_data": [],
                    "success": False,
                    "error": execution_result["error"],
                    "validation": execution_result.get("validation", {}),
                    "semantic_json": semantic_json,
                    "refined_by_llm": False
                }
            
            # Step 5: Check if validation failed
            validation_result = execution_result.get("validation", {})
            if not validation_result.get("valid", True):
                logger.error(f" SQL Validation Failed: {validation_result.get('message', 'Unknown validation error')}")
                logger.error(f" ERROR: SQL validation failed for query: {sql_query}")
                logger.error(f" ERROR: Validation result: {validation_result}")
                return {
                    "sql": sql_query,
                    "raw_data": [],
                    "success": False,
                    "error": validation_result.get("message", "Query validation failed"),
                    "validation": validation_result,
                    "semantic_json": semantic_json,
                    "refined_by_llm": False
                }
            
            # Step 6: Check if we got data
            data_points = len(execution_result["data"])
            logger.info(f" Data Points: {data_points}")
            
            # Step 7: If no data, try fallback with relaxed semantic JSON
            if data_points == 0:
                logger.warning(f" No data returned, trying fallback with relaxed semantic JSON")
                fallback_result = self._try_fallback_semantic_json(english_query, semantic_json)
                if fallback_result["success"] and len(fallback_result["raw_data"]) > 0:
                    logger.info(f" Fallback successful: {len(fallback_result['raw_data'])} data points")
                    return fallback_result
                else:
                    logger.warning(f" Fallback also returned no data")
                    # CRITICAL: Return failure when no data is found
                    return {
                        "sql": sql_query,
                        "raw_data": [],
                        "success": False,
                        "error": "No data available for the requested time range and sensor type",
                        "validation": execution_result.get("validation", {}),
                        "semantic_json": semantic_json,
                        "refined_by_llm": False
                    }
            
            # Step 8: Return successful result only if we have data
            return {
                "sql": sql_query,
                "raw_data": execution_result["data"],
                "success": True,
                "validation": execution_result.get("validation", {}),
                "semantic_json": semantic_json,
                "refined_by_llm": False
            }
                
        except Exception as e:
            logger.error(f" SQL Generation Error: {str(e)}")
            return {
                "sql": "SELECT * FROM sensor_data LIMIT 5",
                "raw_data": [],
                "success": False,
                "error": str(e),
                "semantic_json": {"entity": "temperature", "aggregation": "current", "time_range": "last_24_hours", "grouping": "none", "format": "value"},
                "refined_by_llm": False
            }
    
    def _try_fallback_semantic_json(self, english_query: str, original_semantic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Try fallback with relaxed semantic JSON (entity fallback, no grouping)"""
        try:
            logger.info(f" Trying fallback with relaxed semantic JSON")
            logger.warning(f" FALLBACK TRIGGERED: No data returned from original query, attempting relaxed semantic JSON fallback")
            
            # Create relaxed semantic JSON
            fallback_semantic_json = original_semantic_json.copy()
            
            # Remove grouping for fallback
            fallback_semantic_json["grouping"] = "none"
            
            # If compound query, try with first entity only
            if isinstance(fallback_semantic_json["entity"], list) and len(fallback_semantic_json["entity"]) > 1:
                fallback_semantic_json["entity"] = fallback_semantic_json["entity"][0]
                logger.info(f" Fallback: Using single entity instead of compound")
            
            # Try with current aggregation instead of average
            if fallback_semantic_json["aggregation"] == "average":
                fallback_semantic_json["aggregation"] = "current"
                logger.info(f" Fallback: Using current instead of average")
            
            # Generate SQL from fallback semantic JSON
            fallback_sql = self.query_builder.build_sql_from_semantic_json(fallback_semantic_json)
            logger.info(f" Fallback SQL: {fallback_sql}")
            
            # Execute fallback SQL
            execution_result = self._execute_direct_sql(fallback_sql)
            
            if execution_result["success"] and len(execution_result["data"]) > 0:
                return {
                    "sql": fallback_sql,
                    "raw_data": execution_result["data"],
                    "success": True,
                    "validation": execution_result.get("validation", {}),
                    "semantic_json": fallback_semantic_json,
                    "refined_by_llm": True,
                    "fallback_used": True
                }
            else:
                # Second-level fallback: Use direct LLM SQL agent
                logger.warning(f"  First fallback failed, trying direct LLM SQL agent")
                return self._try_direct_llm_sql_agent(english_query, fallback_semantic_json)
                
        except Exception as e:
            logger.error(f" Fallback semantic JSON error: {str(e)}")
            return {
                "sql": "SELECT * FROM sensor_data LIMIT 5",
                "raw_data": [],
                "success": False,
                "error": str(e),
                "semantic_json": original_semantic_json,
                "refined_by_llm": True,
                "fallback_used": True
            }
    
    def _try_direct_llm_sql_agent(self, english_query: str, fallback_semantic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Second-level fallback: Use direct LLM SQL agent when semantic JSON fails"""
        try:
            logger.info(f" Second-level fallback: Using direct LLM SQL agent for: '{english_query}'")
            logger.warning(f" FALLBACK TRIGGERED: First fallback failed, attempting direct LLM SQL agent fallback")
            
            # Check if SQL agent is available
            if not hasattr(self, 'sql_agent') or self.sql_agent is None:
                logger.warning(f"  SQL agent not available, using basic fallback")
                logger.warning(f" FALLBACK TRIGGERED: SQL agent unavailable, using basic fallback query")
                return self._get_basic_fallback_result(english_query, fallback_semantic_json)
            
            # Use direct LLM SQL agent
            try:
                agent_result = self.sql_agent.run(english_query)
                logger.info(f" Direct LLM SQL agent result: {str(agent_result)[:200]}...")
                
                # Extract SQL from agent result if possible
                if hasattr(agent_result, 'sql') and agent_result.sql:
                    sql_query = agent_result.sql
                elif isinstance(agent_result, str) and 'SELECT' in agent_result.upper():
                    # Try to extract SQL from string result
                    import re
                    sql_match = re.search(r'(SELECT.*?)(?:\n|$)', agent_result, re.IGNORECASE | re.DOTALL)
                    if sql_match:
                        sql_query = sql_match.group(1).strip()
                    else:
                        sql_query = "SELECT * FROM sensor_data LIMIT 5"
                else:
                    sql_query = "SELECT * FROM sensor_data LIMIT 5"
                
                # Execute the SQL
                execution_result = self._execute_direct_sql(sql_query)
                
                if execution_result["success"] and len(execution_result["data"]) > 0:
                    return {
                        "sql": sql_query,
                        "raw_data": execution_result["data"],
                        "success": True,
                        "validation": execution_result.get("validation", {}),
                        "semantic_json": fallback_semantic_json,
                        "refined_by_llm": True,
                        "fallback_used": True,
                        "direct_llm_agent_used": True
                    }
                else:
                    return self._get_basic_fallback_result(english_query, fallback_semantic_json)
                    
            except Exception as agent_error:
                logger.error(f" Direct LLM SQL agent error: {str(agent_error)}")
                return self._get_basic_fallback_result(english_query, fallback_semantic_json)
                
        except Exception as e:
            logger.error(f" Direct LLM SQL agent fallback error: {str(e)}")
            return self._get_basic_fallback_result(english_query, fallback_semantic_json)
    
    def _get_basic_fallback_result(self, english_query: str, fallback_semantic_json: Dict[str, Any]) -> Dict[str, Any]:
        """Basic fallback when all else fails"""
        basic_sql = "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 10"
        execution_result = self._execute_direct_sql(basic_sql)
        
        return {
            "sql": basic_sql,
            "raw_data": execution_result.get("data", []),
            "success": execution_result["success"],
            "error": "All fallbacks exhausted, using basic query",
            "validation": execution_result.get("validation", {}),
            "semantic_json": fallback_semantic_json,
            "refined_by_llm": True,
            "fallback_used": True,
            "basic_fallback_used": True
        }
    
    def _detect_chart_request(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Detect if user wants a chart and what type"""
        query_lower = query.lower()
        chart_patterns = self.ontology.get("chart_patterns", {})
        
        for pattern_name, pattern_data in chart_patterns.items():
            # Check Persian terms
            if language == "fa":
                persian_terms = pattern_data.get("persian", [])
                for term in persian_terms:
                    if term in query_lower:
                        return {
                            "wants_chart": True,
                            "chart_type": pattern_data["chart_type"],
                            "pattern": pattern_name,
                            "matched_term": term
                        }
            
            # Check English terms
            english_terms = pattern_data.get("english", [])
            for term in english_terms:
                if term in query_lower:
                    return {
                        "wants_chart": True,
                        "chart_type": pattern_data["chart_type"],
                        "pattern": pattern_name,
                        "matched_term": term
                    }
        
        return {"wants_chart": False}

    def _process_aggregated_chart_data(self, aggregated_data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
        """Process aggregated data for chart visualization"""
        try:
            # Check if this is time breakdown data (has 'time_period' field)
            is_time_breakdown = "time_period" in aggregated_data[0] if aggregated_data else False
            is_daily_breakdown = "day" in aggregated_data[0] if aggregated_data else False
            
            if chart_type == "line":
                # Process aggregated data for line charts
                labels = []
                values = []
                min_values = []
                max_values = []
                
                for item in aggregated_data:
                    if is_daily_breakdown:
                        # Daily breakdown data
                        day = item.get("day", "Unknown")
                        avg_value = float(item.get("avg_value", 0))
                        min_value = float(item.get("min_value", 0))
                        max_value = float(item.get("max_value", 0))
                        
                        # Format day for display
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(day, "%Y-%m-%d")
                            labels.append(dt.strftime("%d %b"))  # "22 Sep", "23 Sep", etc.
                        except:
                            labels.append(day)
                        
                        values.append(avg_value)
                        min_values.append(min_value)
                        max_values.append(max_value)
                    elif is_time_breakdown:
                        # Time period breakdown data (hourly, weekly, monthly)
                        time_period = item.get("time_period", "Unknown")
                        avg_value = float(item.get("avg_value", 0))
                        min_value = float(item.get("min_value", 0))
                        max_value = float(item.get("max_value", 0))
                        
                        # Format time period for display based on period type
                        try:
                            from datetime import datetime
                            if ":" in time_period:  # Hourly data (YYYY-MM-DD HH:00)
                                dt = datetime.strptime(time_period, "%Y-%m-%d %H:%M")
                                labels.append(dt.strftime("%d %b %H:%M"))  # "22 Sep 14:00"
                            elif len(time_period) == 7:  # Weekly data (YYYY-WW)
                                year, week = time_period.split("-")
                                labels.append(f"Week {week}, {year}")  # "Week 39, 2025"
                            elif len(time_period) == 7 and time_period.count("-") == 1:  # Monthly data (YYYY-MM)
                                dt = datetime.strptime(time_period, "%Y-%m")
                                labels.append(dt.strftime("%b %Y"))  # "Sep 2025"
                            else:  # Daily data (YYYY-MM-DD)
                                dt = datetime.strptime(time_period, "%Y-%m-%d")
                                labels.append(dt.strftime("%d %b"))  # "22 Sep"
                        except:
                            labels.append(time_period)
                        
                        values.append(avg_value)
                        min_values.append(min_value)
                        max_values.append(max_value)
                    else:
                        # Regular time period data (legacy)
                        time_period = item.get("time_period", "Unknown")
                        avg_value = float(item.get("avg_value", 0))
                        
                        # Format time period for display
                        try:
                            from datetime import datetime
                            dt = datetime.strptime(time_period, "%Y-%m-%d")
                            labels.append(dt.strftime("%d %b"))  # "22 Sep", "23 Sep", etc.
                        except:
                            labels.append(time_period)
                        
                        values.append(avg_value)
                
                if (is_daily_breakdown or is_time_breakdown) and min_values and max_values:
                    # Enhanced chart data for daily breakdown with min/max ranges
                    chart_data = {
                        "labels": labels,
                        "datasets": [
                            {
                                "label": "Average Value",
                                "data": values,
                                "borderColor": "rgb(59, 130, 246)",
                                "backgroundColor": "rgba(59, 130, 246, 0.1)",
                                "tension": 0.4,
                                "fill": True,
                                "pointRadius": 6,
                                "pointHoverRadius": 8,
                                "pointBackgroundColor": "rgb(59, 130, 246)",
                                "pointBorderColor": "#ffffff",
                                "pointBorderWidth": 2
                            },
                            {
                                "label": "Min Value",
                                "data": min_values,
                                "borderColor": "rgb(239, 68, 68)",
                                "backgroundColor": "rgba(239, 68, 68, 0.1)",
                                "tension": 0.4,
                                "fill": False,
                                "pointRadius": 4,
                                "pointHoverRadius": 6,
                                "pointBackgroundColor": "rgb(239, 68, 68)",
                                "pointBorderColor": "#ffffff",
                                "pointBorderWidth": 2,
                                "borderDash": [5, 5]
                            },
                            {
                                "label": "Max Value",
                                "data": max_values,
                                "borderColor": "rgb(16, 185, 129)",
                                "backgroundColor": "rgba(16, 185, 129, 0.1)",
                                "tension": 0.4,
                                "fill": False,
                                "pointRadius": 4,
                                "pointHoverRadius": 6,
                                "pointBackgroundColor": "rgb(16, 185, 129)",
                                "pointBorderColor": "#ffffff",
                                "pointBorderWidth": 2,
                                "borderDash": [5, 5]
                            }
                        ]
                    }
                else:
                    # Regular chart data
                    chart_data = {
                        "labels": labels,
                        "datasets": [{
                            "label": "Average Value",
                            "data": values,
                            "borderColor": "rgb(59, 130, 246)",
                            "backgroundColor": "rgba(59, 130, 246, 0.1)",
                            "tension": 0.4,
                            "fill": True,
                            "pointRadius": 6,
                            "pointHoverRadius": 8,
                            "pointBackgroundColor": "rgb(59, 130, 246)",
                            "pointBorderColor": "#ffffff",
                            "pointBorderWidth": 2
                        }]
                    }
                
            elif chart_type == "bar":
                # Process aggregated data for bar charts
                labels = []
                avg_values = []
                min_values = []
                max_values = []
                
                for item in aggregated_data:
                    time_period = item.get("time_period", "Unknown")
                    avg_value = float(item.get("avg_value", 0))
                    min_value = float(item.get("min_value", 0))
                    max_value = float(item.get("max_value", 0))
                    
                    # Format time period for display
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(time_period, "%Y-%m-%d")
                        labels.append(dt.strftime("%d %b"))
                    except:
                        labels.append(time_period)
                    
                    avg_values.append(avg_value)
                    min_values.append(min_value)
                    max_values.append(max_value)
                
                chart_data = {
                    "labels": labels,
                    "datasets": [
                        {
                            "label": " Average",
                            "data": avg_values,
                            "backgroundColor": "rgba(16, 185, 129, 0.8)",
                            "borderColor": "rgba(16, 185, 129, 1)",
                            "borderWidth": 2
                        },
                        {
                            "label": " Min",
                            "data": min_values,
                            "backgroundColor": "rgba(245, 101, 101, 0.8)",
                            "borderColor": "rgba(245, 101, 101, 1)",
                            "borderWidth": 2
                        },
                        {
                            "label": " Max",
                            "data": max_values,
                            "backgroundColor": "rgba(251, 191, 36, 0.8)",
                            "borderColor": "rgba(251, 191, 36, 1)",
                            "borderWidth": 2
                        }
                    ]
                }
                
            else:
                # Default fallback for other chart types
                labels = []
                values = []
                
                for item in aggregated_data:
                    time_period = item.get("time_period", "Unknown")
                    avg_value = float(item.get("avg_value", 0))
                    
                    try:
                        from datetime import datetime
                        dt = datetime.strptime(time_period, "%Y-%m-%d")
                        labels.append(dt.strftime("%d %b"))
                    except:
                        labels.append(time_period)
                    
                    values.append(avg_value)
                
                chart_data = {
                    "labels": labels,
                    "datasets": [{
                        "label": " Average Value",
                        "data": values,
                        "backgroundColor": "rgba(59, 130, 246, 0.8)",
                        "borderColor": "rgba(59, 130, 246, 1)",
                        "borderWidth": 2
                    }]
                }
            
            logger.info(f" Processed aggregated chart data: {len(labels)} labels, {len(values) if 'values' in locals() else 'N/A'} values")
            return chart_data
            
        except Exception as e:
            logger.error(f" Error processing aggregated chart data: {str(e)}")
            return None

    def _process_chart_data(self, raw_data: List[Dict[str, Any]], chart_type: str) -> Dict[str, Any]:
        """Process raw data for chart visualization with enhanced formatting (handles both aggregated and raw data)"""
        if not raw_data:
            return None
        
        # Check if data is in aggregated format (time-aware queries)
        if raw_data and "avg_value" in raw_data[0]:
            logger.info(f" Processing aggregated chart data with {len(raw_data)} time periods")
            return self._process_aggregated_chart_data(raw_data, chart_type)
        
        # Handle raw data format (legacy)
        logger.info(f" Processing raw chart data with {len(raw_data)} data points")
        if chart_type == "line":
            # Enhanced time series data for line charts
            labels = []
            values = []
            timestamps = []
            
            # First pass: collect all timestamps and values
            for item in raw_data:
                timestamp = item.get("timestamp", "")
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        timestamps.append(dt)
                        values.append(float(item.get("value", 0)))
                    except:
                        timestamps.append(None)
                        values.append(float(item.get("value", 0)))
                else:
                    timestamps.append(None)
                    values.append(float(item.get("value", 0)))
            
            # Determine time range and format accordingly
            if timestamps and any(timestamps):
                valid_timestamps = [t for t in timestamps if t is not None]
                if valid_timestamps:
                    min_time = min(valid_timestamps)
                    max_time = max(valid_timestamps)
                    time_diff = max_time - min_time
                    
                    # Format labels based on time range
                    for i, timestamp in enumerate(timestamps):
                        if timestamp is not None:
                            if time_diff.days >= 1:
                                # Multi-day range: show "23 Sep", "24 Sep", etc.
                                labels.append(timestamp.strftime("%d %b"))
                            elif time_diff.total_seconds() >= 3600:  # 1 hour or more
                                # Multi-hour range: show "23 Sep 14:00", "23 Sep 15:00", etc.
                                labels.append(timestamp.strftime("%d %b %H:%M"))
                            elif time_diff.total_seconds() >= 300:  # 5 minutes or more
                                # Multi-minute range: show "14:00", "14:15", etc.
                                labels.append(timestamp.strftime("%H:%M"))
                            else:
                                # Very short range: show "14:00:30", "14:00:45", etc.
                                labels.append(timestamp.strftime("%H:%M:%S"))
                        else:
                            labels.append(f"Point {i+1}")
                    
                    # Remove duplicate labels while preserving order
                    seen = set()
                    unique_labels = []
                    for label in labels:
                        if label not in seen:
                            unique_labels.append(label)
                            seen.add(label)
                        else:
                            # Add a small suffix to make it unique
                            counter = 1
                            while f"{label}_{counter}" in seen:
                                counter += 1
                            unique_labels.append(f"{label}_{counter}")
                            seen.add(f"{label}_{counter}")
                    
                    labels = unique_labels
                else:
                    # No valid timestamps, use generic labels
                    labels = [f"Point {i+1}" for i in range(len(values))]
            else:
                # No timestamps at all, use generic labels
                labels = [f"Point {i+1}" for i in range(len(values))]
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "label": " Sensor Reading",
                    "data": values,
                    "borderColor": "rgb(59, 130, 246)",
                    "backgroundColor": "rgba(59, 130, 246, 0.1)",
                    "tension": 0.4,
                    "fill": True,
                    "pointRadius": 4,
                    "pointHoverRadius": 6,
                    "pointBackgroundColor": "rgb(59, 130, 246)",
                    "pointBorderColor": "#ffffff",
                    "pointBorderWidth": 2
                }]
            }
        
        elif chart_type == "bar":
            # Enhanced comparison data for bar charts
            sensor_types = []
            avg_values = []
            
            # Group data by sensor type and calculate averages
            sensor_data = {}
            for item in raw_data:
                sensor_type = item.get("sensor_type", "Unknown")
                value = float(item.get("value", 0))
                
                if sensor_type not in sensor_data:
                    sensor_data[sensor_type] = []
                sensor_data[sensor_type].append(value)
            
            for sensor_type, values in sensor_data.items():
                sensor_types.append(sensor_type.replace('_', ' ').title())
                avg_values.append(sum(values) / len(values))
            
            chart_data = {
                "labels": sensor_types,
                "datasets": [{
                    "label": " Average Value",
                    "data": avg_values,
                    "backgroundColor": "rgba(16, 185, 129, 0.8)",
                    "borderColor": "rgba(16, 185, 129, 1)",
                    "borderWidth": 2,
                    "borderRadius": 4,
                    "borderSkipped": False
                }]
            }
        
        elif chart_type == "histogram":
            # Enhanced distribution data for histograms
            values = [float(item.get("value", 0)) for item in raw_data]
            
            if not values:
                return None
                
            min_val, max_val = min(values), max(values)
            range_val = max_val - min_val
            
            # Dynamic bin creation based on data range
            num_bins = min(6, max(3, len(values) // 5))
            bin_size = range_val / num_bins if range_val > 0 else 1
            
            bins = [0] * num_bins
            bin_labels = []
            
            for i in range(num_bins):
                bin_start = min_val + (i * bin_size)
                bin_end = min_val + ((i + 1) * bin_size)
                bin_labels.append(f"{bin_start:.1f}-{bin_end:.1f}")
            
            for value in values:
                bin_index = min(int((value - min_val) / bin_size), num_bins - 1)
                bins[bin_index] += 1
            
            chart_data = {
                "labels": bin_labels,
                "datasets": [{
                    "label": " Frequency Distribution",
                    "data": bins,
                    "backgroundColor": "rgba(245, 101, 101, 0.8)",
                    "borderColor": "rgba(245, 101, 101, 1)",
                    "borderWidth": 2,
                    "borderRadius": 4,
                    "borderSkipped": False
                }]
            }
        
        elif chart_type == "pie":
            # Enhanced categorical data for pie charts
            sensor_counts = {}
            
            for item in raw_data:
                sensor_type = item.get("sensor_type", "Unknown")
                sensor_counts[sensor_type] = sensor_counts.get(sensor_type, 0) + 1
            
            labels = []
            data = []
            
            for sensor_type, count in sensor_counts.items():
                labels.append(sensor_type.replace('_', ' ').title())
                data.append(count)
            
            # Professional color palette
            colors = [
                "rgba(59, 130, 246, 0.8)",   # Blue
                "rgba(16, 185, 129, 0.8)",   # Green
                "rgba(245, 101, 101, 0.8)",  # Red
                "rgba(251, 191, 36, 0.8)",   # Yellow
                "rgba(139, 92, 246, 0.8)",   # Purple
                "rgba(236, 72, 153, 0.8)",   # Pink
                "rgba(34, 197, 94, 0.8)",    # Emerald
                "rgba(249, 115, 22, 0.8)"    # Orange
            ]
            
            chart_data = {
                "labels": labels,
                "datasets": [{
                    "data": data,
                    "backgroundColor": colors[:len(data)],
                    "borderColor": "#ffffff",
                    "borderWidth": 2,
                    "hoverBorderWidth": 3
                }]
            }
        
        else:
            # Default fallback
            chart_data = {
                "labels": [f"Data Point {i+1}" for i in range(len(raw_data))],
                "datasets": [{
                    "label": " Values",
                    "data": [float(item.get("value", 0)) for item in raw_data],
                    "backgroundColor": "rgba(59, 130, 246, 0.8)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 2
                }]
            }
        
        return chart_data

    def _create_histogram_bins(self, values: List[float]) -> List[int]:
        """Create histogram bins for distribution charts"""
        bins = [0, 0, 0, 0, 0, 0]  # 6 bins
        for value in values:
            if value < 10:
                bins[0] += 1
            elif value < 20:
                bins[1] += 1
            elif value < 30:
                bins[2] += 1
            elif value < 40:
                bins[3] += 1
            elif value < 50:
                bins[4] += 1
            else:
                bins[5] += 1
        return bins
    
    def _map_query_to_sensor_type(self, query: str, language: str = "en", feature: str = "dashboard") -> Dict[str, Any]:
        """Map natural language query to sensor type using ontology"""
        # Normalize query (remove ZWJ, normalize Arabic letters, strip diacritics)
        def _normalize_text(text: str) -> str:
            try:
                import re
                # Remove zero-width non-joiner and joiner
                text = text.replace('\u200c', '').replace('\u200d', '')
                # Normalize Arabic Yeh/Kaf variants
                text = text.replace('ي', 'ی').replace('ك', 'ک')
                # Remove diacritics
                text = re.sub(r"[\u064B-\u065F]", "", text)
                return text
            except Exception:
                return text
        query_norm = _normalize_text(query)
        query_lower = query_norm.lower()
        ontology = self.ontology
        
        # Check for dangerous queries first (more specific to avoid false positives)
        dangerous_keywords = ['drop table', 'delete from', 'update set', 'insert into', 'alter table', 'create table', 'truncate table', 'remove table', 'clear table']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                logger.warning(f"  Dangerous query detected in sensor mapping: {keyword}")
                return {
                    "sensor_type": query,
                    "matched_term": keyword,
                    "mapping_type": "dangerous",
                    "confidence": 0.0,
                    "candidates": []
                }
        
        # Check for comparison queries FIRST (highest priority)
        comparison_words = ["مقایسه", "compare", "vs", "با", "versus"]
        is_comparison = any(word in query_lower for word in comparison_words)
        matched_comparison_words = [word for word in comparison_words if word in query_lower]
        print(f" DEBUG _map_query_to_sensor_type: query={len(query)} characters")
        print(f" DEBUG _map_query_to_sensor_type: query_lower={len(query_lower)} characters")
        print(f" DEBUG _map_query_to_sensor_type: matched_comparison_words={matched_comparison_words}")
        print(f" DEBUG _map_query_to_sensor_type: is_comparison={is_comparison}")
        if is_comparison:
            print(f" COMPARISON DETECTED - proceed with normal ontology mapping; will only affect time/grouping")
            # Do NOT choose entity here. Comparison should influence time_range/grouping, not entity.
            # We still skip compound mappings later when is_comparison is True.
        
        # Check for compound queries (multiple sensors) - but NOT for comparison queries
        if not is_comparison:  # Skip compound mappings for comparison queries
            compound_mappings = {
            "fa": {
                "خاک و آب": ["soil_moisture", "water_usage"],
                "دما و رطوبت": ["temperature", "humidity"],
                "آفات و بیماری": ["pest_count", "disease_risk"],
                "خاک و کود": ["soil_moisture", "fertilizer_usage"],
                "نور و دما": ["light", "temperature"],
                # COMPREHENSIVE IRRIGATION MAPPINGS
                "ابیاری": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "آبیاری": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "آب دادن": ["soil_moisture", "water_usage", "humidity"],
                "آبیاری کنم": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "آبیاری کنم یا نه": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "آبیاری امروز": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "آبیاری لازم": ["soil_moisture", "water_usage", "humidity"],
                "آب خاک": ["soil_moisture", "water_usage"],
                "رطوبت خاک": ["soil_moisture", "water_usage"],
                "مصرف آب": ["water_usage", "water_efficiency"],
                "آب مصرفی": ["water_usage", "water_efficiency"],
                "استفاده آب": ["water_usage", "water_efficiency"],
                "بازدهی آب": ["water_efficiency", "water_usage"],
                "کارایی آب": ["water_efficiency", "water_usage"],
                "مصرف بهینه آب": ["water_efficiency", "water_usage"],
                "آبیاری خودکار": ["soil_moisture", "water_usage", "humidity"],
                "سیستم آبیاری": ["soil_moisture", "water_usage", "humidity"],
                "آبیاری قطره‌ای": ["soil_moisture", "water_usage", "humidity"],
                "آبیاری بارانی": ["soil_moisture", "water_usage", "humidity"],
                "آبیاری هوشمند": ["soil_moisture", "water_usage", "humidity", "temperature"],
                # COMPREHENSIVE PEST MANAGEMENT MAPPINGS
                "سم پاشی": ["pest_count", "pest_detection", "disease_risk", "temperature", "humidity"],
                "آفت کش": ["pest_count", "pest_detection", "disease_risk", "temperature", "humidity"],
                "آفات": ["pest_count", "pest_detection", "disease_risk"],
                "کنترل آفات": ["pest_count", "pest_detection", "disease_risk"],
                "مبارزه با آفات": ["pest_count", "pest_detection", "disease_risk"],
                "پیشگیری آفات": ["pest_count", "pest_detection", "disease_risk"],
                "سموم": ["pest_count", "pest_detection", "disease_risk"],
                "آفت‌کش": ["pest_count", "pest_detection", "disease_risk"],
                "حشره‌کش": ["pest_count", "pest_detection", "disease_risk"],
                "قارچ‌کش": ["pest_count", "pest_detection", "disease_risk"],
                "علف‌کش": ["pest_count", "pest_detection", "disease_risk"],
                "بیماری گیاهی": ["disease_risk", "pest_count"],
                "قارچ": ["disease_risk", "pest_count"],
                "ویروس": ["disease_risk", "pest_count"],
                "باکتری": ["disease_risk", "pest_count"],
                # COMPREHENSIVE ENVIRONMENTAL MAPPINGS
                "محیط": ["temperature", "humidity", "co2_level", "light"],
                "گلخانه": ["temperature", "humidity", "co2_level", "light"],
                "شرایط محیطی": ["temperature", "humidity", "co2_level", "light"],
                "آب و هوا": ["temperature", "humidity", "pressure", "wind_speed", "rainfall"],
                "اقلیم": ["temperature", "humidity", "pressure", "wind_speed", "rainfall"],
                "هوا": ["temperature", "humidity", "pressure", "wind_speed"],
                "جو": ["temperature", "humidity", "pressure", "wind_speed"],
                "تهویه": ["temperature", "humidity", "co2_level", "wind_speed"],
                "تهویه مطبوع": ["temperature", "humidity", "co2_level", "wind_speed"],
                "سیستم تهویه": ["temperature", "humidity", "co2_level", "wind_speed"],
                "فن": ["temperature", "humidity", "co2_level", "wind_speed"],
                "کولر": ["temperature", "humidity", "co2_level"],
                "گرمایش": ["temperature", "humidity"],
                "سرمایش": ["temperature", "humidity"],
                "کنترل دما": ["temperature", "humidity"],
                "کنترل رطوبت": ["humidity", "temperature"],
                "کنترل نور": ["light", "temperature"],
                "کنترل co2": ["co2_level", "temperature", "humidity"],
            },
            "en": {
                "soil and water": ["soil_moisture", "water_usage"],
                "temperature and humidity": ["temperature", "humidity"],
                "pests and disease": ["pest_count", "disease_risk"],
                "soil and fertilizer": ["soil_moisture", "fertilizer_usage"],
                "light and temperature": ["light", "temperature"],
                # COMPREHENSIVE IRRIGATION MAPPINGS
                "irrigation": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "watering": ["soil_moisture", "water_usage", "humidity"],
                "should i water": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "water today": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "irrigate today": ["soil_moisture", "water_usage", "humidity", "temperature"],
                "soil moisture": ["soil_moisture", "water_usage"],
                "water usage": ["water_usage", "water_efficiency"],
                "water consumption": ["water_usage", "water_efficiency"],
                "water used": ["water_usage", "water_efficiency"],
                "water efficiency": ["water_efficiency", "water_usage"],
                "water optimization": ["water_efficiency", "water_usage"],
                "efficiency": ["water_efficiency", "water_usage"],
                "automatic irrigation": ["soil_moisture", "water_usage", "humidity"],
                "irrigation system": ["soil_moisture", "water_usage", "humidity"],
                "drip irrigation": ["soil_moisture", "water_usage", "humidity"],
                "sprinkler irrigation": ["soil_moisture", "water_usage", "humidity"],
                "smart irrigation": ["soil_moisture", "water_usage", "humidity", "temperature"],
                # COMPREHENSIVE PEST MANAGEMENT MAPPINGS
                "pesticide": ["pest_count", "pest_detection", "disease_risk", "temperature", "humidity"],
                "spray pesticide": ["pest_count", "pest_detection", "disease_risk", "temperature", "humidity"],
                "pest control": ["pest_count", "pest_detection", "disease_risk"],
                "pest management": ["pest_count", "pest_detection", "disease_risk"],
                "pest prevention": ["pest_count", "pest_detection", "disease_risk"],
                "insecticide": ["pest_count", "pest_detection", "disease_risk"],
                "fungicide": ["pest_count", "pest_detection", "disease_risk"],
                "herbicide": ["pest_count", "pest_detection", "disease_risk"],
                "plant disease": ["disease_risk", "pest_count"],
                "fungus": ["disease_risk", "pest_count"],
                "virus": ["disease_risk", "pest_count"],
                "bacteria": ["disease_risk", "pest_count"],
                # COMPREHENSIVE ENVIRONMENTAL MAPPINGS
                "environment": ["temperature", "humidity", "co2_level", "light"],
                "greenhouse": ["temperature", "humidity", "co2_level", "light"],
                "environmental conditions": ["temperature", "humidity", "co2_level", "light"],
                "weather": ["temperature", "humidity", "pressure", "wind_speed", "rainfall"],
                "climate": ["temperature", "humidity", "pressure", "wind_speed", "rainfall"],
                "air": ["temperature", "humidity", "pressure", "wind_speed"],
                "atmosphere": ["temperature", "humidity", "pressure", "wind_speed"],
                "ventilation": ["temperature", "humidity", "co2_level", "wind_speed"],
                "air conditioning": ["temperature", "humidity", "co2_level", "wind_speed"],
                "ventilation system": ["temperature", "humidity", "co2_level", "wind_speed"],
                "fan": ["temperature", "humidity", "co2_level", "wind_speed"],
                "cooler": ["temperature", "humidity", "co2_level"],
                "heating": ["temperature", "humidity"],
                "cooling": ["temperature", "humidity"],
                "temperature control": ["temperature", "humidity"],
                "humidity control": ["humidity", "temperature"],
                "light control": ["light", "temperature"],
                "co2 control": ["co2_level", "temperature", "humidity"]
            }
        }
        
            # Check for compound queries first
            for compound_query, sensor_types in compound_mappings.get(language, {}).items():
                if compound_query in query_lower:
                    logger.info(f" Mapped compound query '{compound_query}' to sensors: {sensor_types}")
                    return {
                        "sensor_type": sensor_types,  # Return as list, not compound string
                        "matched_term": compound_query,
                        "mapping_type": "compound",
                        "confidence": 0.9,
                        "candidates": sensor_types
                    }
        
        # Map query to sensor type using ontology
        sensor_mappings = ontology.get("sensor_mappings", {})
        
        # First pass: Check for exact matches (more specific terms first)
        exact_matches = []
        for sensor_type, mapping in sensor_mappings.items():
            # Check Persian terms
            if language == "fa":
                persian_terms = mapping.get("persian_terms", [])
                for term in persian_terms:
                    if term in query_lower:
                        exact_matches.append((len(term), sensor_type, term))  # Sort by length (longer = more specific)
            
            # Check English terms
            english_terms = mapping.get("english_terms", [])
            for term in english_terms:
                if term in query_lower:
                    exact_matches.append((len(term), sensor_type, term))  # Sort by length (longer = more specific)
        
        # Second pass: Check for partial and phrase matches (if no exact match found)
        if not exact_matches:
            partial_matches = []
            # High-priority pest growth phrases
            pest_growth_phrases_fa = ["رشد آفات", "افزایش آفات", "رشد آفت", "افزایش آفت"]
            pest_growth_phrases_en = ["pest growth", "increase in pests", "pest trend"]
            if any(p in query_lower for p in pest_growth_phrases_fa + pest_growth_phrases_en):
                logger.info(" Phrase match: pest growth -> pest_count")
                return {
                    "sensor_type": "pest_count",
                    "matched_term": "pest_growth_phrase",
                    "mapping_type": "phrase",
                    "confidence": 0.92,
                    "candidates": ["pest_count"]
                }

            # Language-agnostic heuristic: pest tokens + growth/trend tokens in any order
            pest_tokens_fa = ["آفات", "آفت", "حشره", "حشرات"]
            pest_tokens_en = ["pest", "pests", "insect", "insects"]
            growth_tokens_fa = ["رشد", "افزایش", "روند", "تغییرات"]
            growth_tokens_en = ["growth", "increase", "trend", "changes"]
            has_pest = any(t in query_lower for t in pest_tokens_fa + pest_tokens_en)
            has_growth = any(t in query_lower for t in growth_tokens_fa + growth_tokens_en)
            if has_pest and has_growth:
                logger.info(" Heuristic match: pest + growth terms -> pest_count")
                return {
                    "sensor_type": "pest_count",
                    "matched_term": "pest_growth_heuristic",
                    "mapping_type": "heuristic",
                    "confidence": 0.9,
                    "candidates": ["pest_count"]
                }
            for sensor_type, mapping in sensor_mappings.items():
                # Check Persian terms for partial matches
                if language == "fa":
                    persian_terms = mapping.get("persian_terms", [])
                    for term in persian_terms:
                        # Check if any word from the term appears in the query
                        term_words = term.split()
                        for word in term_words:
                            if len(word) > 2 and word in query_lower:  # Only words longer than 2 characters
                                partial_matches.append((len(word), sensor_type, word))
                
                # Check English terms for partial matches
                english_terms = mapping.get("english_terms", [])
                for term in english_terms:
                    term_words = term.split()
                    for word in term_words:
                        if len(word) > 2 and word in query_lower:
                            partial_matches.append((len(word), sensor_type, word))
            
            # Sort by length (descending) to prioritize longer matches
            partial_matches.sort(reverse=True)
            if partial_matches:
                _, sensor_type, word = partial_matches[0]
                logger.info(f" Mapped partial term '{word}' to sensor '{sensor_type}'")
                print(f" Mapped partial term '{word}' to sensor '{sensor_type}'")
                return {
                    "sensor_type": sensor_type,
                    "matched_term": word,
                    "mapping_type": "partial",
                    "confidence": 0.8,
                    "candidates": [sensor_type]
                }
        
        # Sort by length (descending) to prioritize more specific terms
        exact_matches.sort(reverse=True)
        
        if exact_matches:
            # Take the longest (most specific) match
            _, sensor_type, term = exact_matches[0]
            logger.info(f" Mapped specific term '{term}' to sensor '{sensor_type}'")
            print(f" Mapped specific term '{term}' to sensor '{sensor_type}'")
            return {
                "sensor_type": sensor_type,
                "matched_term": term,
                "mapping_type": "exact",
                "confidence": 0.95,
                "candidates": [sensor_type]
            }

        # Feature-based tie-break (only if still no mapping)
        if feature in ["pest-detection", "pest", "pest_detection"]:
            logger.info(" Feature bias: pest-detection -> pest_count")
            return {
                "sensor_type": "pest_count",
                "matched_term": "feature_bias",
                "mapping_type": "feature_bias",
                "confidence": 0.75,
                "candidates": ["pest_count"]
            }
        
        # Enhanced fallback with fuzzy matching
        fallback_mappings = {
            "fa": {
                "چطوره": "temperature",  # Default to temperature for general "how is" queries
                "وضعیت": "temperature",  # Default to temperature for general "status" queries
                "امروز": "temperature",  # Default to temperature for "today" queries
                "الان": "temperature",   # Default to temperature for "now" queries
                "فعلا": "temperature",   # Default to temperature for "currently" queries
                "حالا": "temperature",   # Default to temperature for "now" queries
                "اکنون": "temperature",  # Default to temperature for "now" queries
                "برگ": "leaf_wetness",   # "leaf" maps to leaf wetness
                "میوه": "fruit_count",   # "fruit" maps to fruit count
                "تست": "test_temperature", # "test" maps to test temperature
                "آزمایش": "test_temperature" # "experiment" maps to test temperature
            },
            "en": {
                "how": "temperature",    # Default to temperature for "how" queries
                "status": "temperature", # Default to temperature for "status" queries
                "today": "temperature",  # Default to temperature for "today" queries
                "now": "temperature",    # Default to temperature for "now" queries
                "current": "temperature", # Default to temperature for "current" queries
                "leaf": "leaf_wetness",  # "leaf" maps to leaf wetness
                "fruit": "fruit_count",  # "fruit" maps to fruit count
                "test": "test_temperature", # "test" maps to test temperature
                "experimental": "test_temperature" # "experimental" maps to test temperature
            }
        }
        
        # Context-specific mappings (higher priority than general fallbacks)
        context_mappings = {
            "fa": {
                "خاک": "soil_moisture",  # "soil" maps to soil moisture
                "زمین": "soil_moisture", # "ground" maps to soil moisture
                "آب": "water_usage",     # "water" maps to water usage
                "آبیاری": "water_usage", # "irrigation" maps to water usage
                "دما": "temperature",    # "temperature" maps to temperature
                "رطوبت": "humidity",     # "humidity" maps to humidity
                "آفات": "pest_count",    # "pests" maps to pest count
                "بیماری": "disease_risk" # "disease" maps to disease risk
            },
            "en": {
                "soil": "soil_moisture",  # "soil" maps to soil moisture
                "ground": "soil_moisture", # "ground" maps to soil moisture
                "water": "water_usage",   # "water" maps to water usage
                "irrigation": "water_usage", # "irrigation" maps to water usage
                "temperature": "temperature", # "temperature" maps to temperature
                "humidity": "humidity",   # "humidity" maps to humidity
                "pest": "pest_count",     # "pest" maps to pest count
                "disease": "disease_risk" # "disease" maps to disease risk
            }
        }
        
        # Check context-specific mappings first (higher priority)
        for term, sensor_type in context_mappings.get(language, {}).items():
            if term in query_lower:
                logger.info(f" Mapped context term '{term}' to sensor '{sensor_type}'")
                return {
                    "sensor_type": sensor_type,
                    "matched_term": term,
                    "mapping_type": "context",
                    "confidence": 0.8,
                    "candidates": [sensor_type]
                }
        
        # No direct mapping found - use LLM to find closest ontology match
        logger.info(f" No direct mapping found for query: {query}, using LLM to find closest ontology match")
        return self._llm_map_to_ontology(query, language)
    
    def _llm_map_to_ontology(self, query: str, language: str = "en") -> Dict[str, Any]:
        """Use LLM to map query to closest ontology sensor type and log new synonyms"""
        try:
            # Get all available sensor types from ontology
            sensor_mappings = self.ontology.get("sensor_mappings", {})
            available_sensors = list(sensor_mappings.keys())
            
            # Create ontology context for LLM
            ontology_context = "\n".join([
                f"- {sensor}: {mapping.get('description', 'No description')}"
                for sensor, mapping in sensor_mappings.items()
            ])
            
            prompt = f"""You are an expert in agricultural sensor data mapping. Your task is to map the user query to the closest matching sensor type from our ontology.

USER QUERY: "{query}"
LANGUAGE: {language}

AVAILABLE SENSOR TYPES IN ONTOLOGY:
{ontology_context}

INSTRUCTIONS:
1. Analyze the user query and find the closest matching sensor type from the ontology
2. If the query contains terms not in the ontology, suggest the closest semantic match
3. Return your response in this exact JSON format:
{{
    "sensor_type": "closest_sensor_type",
    "matched_term": "term_from_query",
    "mapping_type": "llm_mapping",
    "confidence": 0.0-1.0,
    "reasoning": "explanation of why this sensor type was chosen",
    "new_synonyms": ["new_term1", "new_term2"] // terms from query not in ontology
}}

EXAMPLES:
- Query: "رشد آفات" -> sensor_type: "pest_count" (pest growth = pest count)
- Query: "رطوبت خاک" -> sensor_type: "soil_moisture" (soil humidity = soil moisture)
- Query: "مصرف آب" -> sensor_type: "water_usage" (water consumption = water usage)

RESPONSE:"""

            # Log LLM call
            truncated_prompt = prompt[:200] + "..." if len(prompt) > 200 else prompt
            logger.info(f"🤖 LLM Call - Ontology Mapping (Prompt): {truncated_prompt}")
            
            response = self.llm.invoke(prompt)
            response_text = getattr(response, 'content', None) or getattr(response, 'text', '')
            
            # Log LLM response
            truncated_response = response_text[:100] + "..." if len(response_text) > 100 else response_text
            logger.info(f"🤖 LLM Call - Ontology Mapping (Response): {truncated_response}")
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response_text.strip())
                
                # Log new synonyms for developer to add to ontology
                if result.get("new_synonyms"):
                    logger.info(f" NEW SYNONYMS DETECTED for developer to add to ontology:")
                    for synonym in result["new_synonyms"]:
                        logger.info(f"   - '{synonym}' -> '{result['sensor_type']}'")
                    
                    # Persist synonyms to ontology for future use
                    self._persist_synonyms_to_ontology(result["new_synonyms"], result["sensor_type"])
                
                # Ensure required fields
                return {
                    "sensor_type": result.get("sensor_type", "temperature"),
                    "matched_term": result.get("matched_term", "llm_mapped"),
                    "mapping_type": "llm_mapping",
                    "confidence": result.get("confidence", 0.7),
                    "candidates": [result.get("sensor_type", "temperature")],
                    "reasoning": result.get("reasoning", "LLM mapping"),
                    "new_synonyms": result.get("new_synonyms", [])
                }
                
            except json.JSONDecodeError:
                logger.error(f" Failed to parse LLM ontology mapping response: {response_text}")
                # Fallback to pest_count for pest-related queries
                if any(term in query.lower() for term in ["آفات", "pest", "رشد", "growth"]):
                    return {
                        "sensor_type": "pest_count",
                        "matched_term": "pest_related",
                        "mapping_type": "llm_fallback",
                        "confidence": 0.5,
                        "candidates": ["pest_count"],
                        "reasoning": "Fallback to pest_count for pest-related query",
                        "new_synonyms": []
                    }
                else:
                    return {
                        "sensor_type": "temperature",
                        "matched_term": "llm_fallback",
                        "mapping_type": "llm_fallback",
                        "confidence": 0.3,
                        "candidates": ["temperature"],
                        "reasoning": "LLM parsing failed, using temperature fallback",
                        "new_synonyms": []
                    }
                    
        except Exception as e:
            logger.error(f" Error in LLM ontology mapping: {e}")
            logger.error(f" ERROR: Ontology mapping failed for query: {query}")
            logger.error(f" ERROR: Language: {language}, Available sensors: {list(self.ontology.get('sensor_mappings', {}).keys())}")
            return {
                "sensor_type": "temperature",
                "matched_term": "error_fallback",
                "mapping_type": "error_fallback",
                "confidence": 0.1,
                "candidates": ["temperature"],
                "reasoning": f"Error in LLM mapping: {str(e)}",
                "new_synonyms": []
            }
    
    def _generate_ontology_sql(self, english_query: str, language: str = "en") -> str:
        """Generate SQL query using ontology mappings"""
        try:
            logger.info(f" Generating ontology-based SQL for: '{english_query}'")
            
            # Map query to sensor type
            mapping_result = self._map_query_to_sensor_type(english_query, language)
            sensor_type = mapping_result["sensor_type"]
            
            # Handle compound queries (sensor_type is already a list)
            if isinstance(sensor_type, list):
                return self._generate_compound_sql(sensor_type, english_query, language)
            
            # Determine query pattern
            query_patterns = self.ontology.get("query_patterns", {})
            query_lower = english_query.lower()
            
            # Check for current/latest value
            current_indicators = query_patterns.get("current_value", {}).get("persian", []) + \
                               query_patterns.get("current_value", {}).get("english", [])
            if any(indicator in query_lower for indicator in current_indicators):
                sql = f"SELECT * FROM sensor_data WHERE sensor_type = '{sensor_type}' ORDER BY timestamp DESC LIMIT 1"
                logger.info(f" Generated current value SQL: {sql}")
                return sql
            
            # Check for average value
            avg_indicators = query_patterns.get("average_value", {}).get("persian", []) + \
                           query_patterns.get("average_value", {}).get("english", [])
            if any(indicator in query_lower for indicator in avg_indicators):
                sql = f"SELECT AVG(value) as avg_value FROM sensor_data WHERE sensor_type = '{sensor_type}'"
                logger.info(f" Generated average value SQL: {sql}")
                return sql
            
            # Check for time-based queries using new time-aware system
            time_config = self._parse_time_expression(english_query, language)
            if time_config:
                sql = self._generate_time_aware_sql(sensor_type, time_config, english_query)
                logger.info(f" Generated time-aware SQL: {sql}")
                return sql
            
            # Check for trend analysis
            trend_indicators = query_patterns.get("trend_analysis", {}).get("persian", []) + \
                             query_patterns.get("trend_analysis", {}).get("english", [])
            if any(indicator in query_lower for indicator in trend_indicators):
                sql = f"SELECT timestamp, value FROM sensor_data WHERE sensor_type = '{sensor_type}' ORDER BY timestamp DESC LIMIT 10"
                logger.info(f" Generated trend analysis SQL: {sql}")
                return sql
            
            # Fallback: Default to last 24 hours with hourly aggregation
            logger.info(f" No time expression detected, using fallback: last 24 hours with hourly aggregation")
            fallback_config = {"days": 1, "granularity": "hour"}
            sql = self._generate_time_aware_sql(sensor_type, fallback_config, english_query)
            logger.info(f" Generated fallback SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f" Error in ontology SQL generation: {e}")
            return self._generate_simple_sql(english_query)
    
    def _parse_time_expression(self, query: str, language: str = "en") -> Dict[str, Any]:
        """ROBUST TIME PARSER: Parse ANY time expression intelligently using regex patterns"""
        try:
            import re
            query_lower = query.lower()
            
            # UNIVERSAL TIME PARSER - Handles ALL time expressions with regex
            time_patterns = [
                # Hours patterns (most specific first)
                (r'(\d+)\s*hours?\s*(?:ago|back|earlier|before)', self._parse_hours_ago),
                (r'(?:last|past|previous|recent)\s*(\d+)\s*hours?', self._parse_hours_last),
                (r'(?:in|for|over|during)\s*(?:the\s*)?(?:last|past|previous|recent)\s*(\d+)\s*hours?', self._parse_hours_last),
                (r'(?:this|current)\s*(\d+)\s*hours?', self._parse_hours_current),
                
                # Word number patterns for hours
                (r'(?:last|past|previous|recent)\s*(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve)\s*hours?', self._parse_hours_last_word),
                
                # Days patterns
                (r'(\d+)\s*days?\s*(?:ago|back|earlier|before)', self._parse_days_ago),
                (r'(?:last|past|previous|recent)\s*(\d+)\s*days?', self._parse_days_last),
                (r'(?:in|for|over|during)\s*(?:the\s*)?(?:last|past|previous|recent)\s*(\d+)\s*days?', self._parse_days_last),
                (r'(?:this|current)\s*(\d+)\s*days?', self._parse_days_current),
                
                # Weeks patterns
                (r'(\d+)\s*weeks?\s*(?:ago|back|earlier|before)', self._parse_weeks_ago),
                (r'(?:last|past|previous|recent)\s*(\d+)\s*weeks?', self._parse_weeks_last),
                (r'(?:in|for|over|during)\s*(?:the\s*)?(?:last|past|previous|recent)\s*(\d+)\s*weeks?', self._parse_weeks_last),
                (r'(?:this|current)\s*(\d+)\s*weeks?', self._parse_weeks_current),
                
                # Minutes patterns
                (r'(\d+)\s*minutes?\s*(?:ago|back|earlier|before)', self._parse_minutes_ago),
                (r'(?:last|past|previous|recent)\s*(\d+)\s*minutes?', self._parse_minutes_last),
                
                # Special patterns
                (r'(?:today|this\s*day)', self._parse_today),
                (r'(?:yesterday|yesterdays)', self._parse_yesterday),
                (r'(?:this\s*week|current\s*week)', self._parse_this_week),
                (r'(?:last\s*week|previous\s*week)', self._parse_last_week),
                (r'(?:this\s*month|current\s*month)', self._parse_this_month),
                (r'(?:last\s*month|previous\s*month)', self._parse_last_month),
            ]
            
            # Try each pattern in order
            for pattern, parser_func in time_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    result = parser_func(match, query_lower)
                    if result:
                        return result
            
            # Default fallback
            return {"days": 1, "hours": 24, "minutes": 1440, "granularity": "day"}
            
        except Exception as e:
            logger.error(f"Error in robust time parser: {e}")
            return {"days": 1, "hours": 24, "minutes": 1440, "granularity": "day"}
    
    def _parse_hours_ago(self, match, query_lower):
        """Parse X hours ago patterns"""
        hours = int(match.group(1))
        return {"hours": hours, "granularity": "hour", "offset": -hours}
    
    def _parse_hours_last(self, match, query_lower):
        """Parse last X hours patterns"""
        hours = int(match.group(1))
        return {"hours": hours, "granularity": "hour"}
    
    def _parse_hours_last_word(self, match, query_lower):
        """Parse last X hours patterns with word numbers"""
        word_to_number = {
            "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
            "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12
        }
        word = match.group(1)
        hours = word_to_number.get(word, 2)  # Default to 2 if not found
        return {"hours": hours, "granularity": "hour"}
    
    def _parse_hours_current(self, match, query_lower):
        """Parse this X hours patterns"""
        hours = int(match.group(1))
        return {"hours": hours, "granularity": "hour"}
    
    def _parse_days_ago(self, match, query_lower):
        """Parse X days ago patterns"""
        days = int(match.group(1))
        return {"days": days, "granularity": "day", "offset": -days}
    
    def _parse_days_last(self, match, query_lower):
        """Parse last X days patterns"""
        days = int(match.group(1))
        return {"days": days, "granularity": "day"}
    
    def _parse_days_current(self, match, query_lower):
        """Parse this X days patterns"""
        days = int(match.group(1))
        return {"days": days, "granularity": "day"}
    
    def _parse_weeks_ago(self, match, query_lower):
        """Parse X weeks ago patterns"""
        weeks = int(match.group(1))
        return {"days": weeks * 7, "granularity": "week", "offset": -(weeks * 7)}
    
    def _parse_weeks_last(self, match, query_lower):
        """Parse last X weeks patterns"""
        weeks = int(match.group(1))
        return {"days": weeks * 7, "granularity": "week"}
    
    def _parse_weeks_current(self, match, query_lower):
        """Parse this X weeks patterns"""
        weeks = int(match.group(1))
        return {"days": weeks * 7, "granularity": "week"}
    
    def _parse_minutes_ago(self, match, query_lower):
        """Parse X minutes ago patterns"""
        minutes = int(match.group(1))
        return {"minutes": minutes, "granularity": "minute", "offset": -minutes}
    
    def _parse_minutes_last(self, match, query_lower):
        """Parse last X minutes patterns"""
        minutes = int(match.group(1))
        return {"minutes": minutes, "granularity": "minute"}
    
    def _parse_today(self, match, query_lower):
        """Parse today patterns"""
        return {"days": 1, "granularity": "day"}
    
    def _parse_yesterday(self, match, query_lower):
        """Parse yesterday patterns"""
        return {"days": 1, "granularity": "day", "offset": -1}
    
    def _parse_this_week(self, match, query_lower):
        """Parse this week patterns"""
        return {"days": 7, "granularity": "week"}
    
    def _parse_last_week(self, match, query_lower):
        """Parse last week patterns"""
        return {"days": 7, "granularity": "week", "offset": -7}
    
    def _parse_this_month(self, match, query_lower):
        """Parse this month patterns"""
        return {"days": 30, "granularity": "day"}
    
    def _parse_last_month(self, match, query_lower):
        """Parse last month patterns"""
        return {"days": 30, "granularity": "day", "offset": -30}
    
    def _map_hours_to_time_range(self, hours: int) -> str:
        """ROBUST HOURS MAPPING: Map any number of hours to the correct time range"""
        if hours <= 1:
            return "last_hour"
        elif hours <= 2:
            return "last_2_hours"
        elif hours <= 4:
            return "last_4_hours"
        elif hours <= 6:
            return "last_6_hours"
        elif hours <= 8:
            return "last_8_hours"
        elif hours <= 12:
            return "last_12_hours"
        elif hours <= 24:
            return "last_24_hours"
        elif hours <= 48:
            return "last_2_days"
        elif hours <= 72:
            return "last_3_days"
        elif hours <= 168:  # 1 week
            return "last_week"
        else:
            return "last_30_days"
    
    def _map_days_to_time_range(self, days: int) -> str:
        """ROBUST DAYS MAPPING: Map any number of days to the correct time range"""
        if days <= 1:
            return "last_24_hours"
        elif days <= 2:
            return "last_2_days"
        elif days <= 3:
            return "last_3_days"
        elif days <= 7:
            return "last_week"
        elif days <= 14:
            return "last_2_weeks"
        elif days <= 30:
            return "last_month"
        else:
            return "last_30_days"
    
    def _map_minutes_to_time_range(self, minutes: int) -> str:
        """ROBUST MINUTES MAPPING: Map any number of minutes to the correct time range"""
        if minutes <= 30:
            return "last_30_minutes"
        elif minutes <= 60:
            return "last_hour"
        elif minutes <= 120:
            return "last_2_hours"
        elif minutes <= 240:
            return "last_4_hours"
        elif minutes <= 360:
            return "last_6_hours"
        elif minutes <= 480:
            return "last_8_hours"
        elif minutes <= 720:
            return "last_12_hours"
        else:
            return "last_24_hours"
            
            # Persian time patterns with granularity and enhanced numeral support
            if language == "fa":
                persian_patterns = {
                    # Hours - FIXED: Use hour granularity for hour queries
                    "یک ساعت": {"hours": 1, "granularity": "hour"},
                    "دو ساعت": {"hours": 2, "granularity": "hour"},
                    "سه ساعت": {"hours": 3, "granularity": "hour"},
                    "چهار ساعت": {"hours": 4, "granularity": "hour"},
                    "پنج ساعت": {"hours": 5, "granularity": "hour"},
                    "شش ساعت": {"hours": 6, "granularity": "hour"},
                    "هفت ساعت": {"hours": 7, "granularity": "hour"},
                    "هشت ساعت": {"hours": 8, "granularity": "hour"},
                    "نه ساعت": {"hours": 9, "granularity": "hour"},
                    "ده ساعت": {"hours": 10, "granularity": "hour"},
                    "دوازده ساعت": {"hours": 12, "granularity": "hour"},
                    "بیست و چهار ساعت": {"hours": 24, "granularity": "hour"},
                    # Days with numerals - FIXED: Use day granularity for day queries
                    "یک روز": {"days": 1, "granularity": "day"},
                    "دو روز": {"days": 2, "granularity": "day"},
                    "سه روز": {"days": 3, "granularity": "day"},
                    "چهار روز": {"days": 4, "granularity": "day"},
                    "پنج روز": {"days": 5, "granularity": "day"},
                    "شش روز": {"days": 6, "granularity": "day"},
                    "هفت روز": {"days": 7, "granularity": "day"},
                    # Weeks - FIXED: Use week granularity for week queries
                    "یک هفته": {"days": 7, "granularity": "week"},
                    "دو هفته": {"days": 14, "granularity": "week"},
                    "سه هفته": {"days": 21, "granularity": "week"},
                    # Months
                    "یک ماه": {"days": 30, "granularity": "day"},
                    "دو ماه": {"days": 60, "granularity": "day"},
                    "سه ماه": {"days": 90, "granularity": "day"},
                    # Minutes - COMPLETE COVERAGE
                    "یک دقیقه": {"minutes": 1, "granularity": "minute"},
                    "دو دقیقه": {"minutes": 2, "granularity": "minute"},
                    "سه دقیقه": {"minutes": 3, "granularity": "minute"},
                    "چهار دقیقه": {"minutes": 4, "granularity": "minute"},
                    "پنج دقیقه": {"minutes": 5, "granularity": "minute"},
                    "شش دقیقه": {"minutes": 6, "granularity": "minute"},
                    "هفت دقیقه": {"minutes": 7, "granularity": "minute"},
                    "هشت دقیقه": {"minutes": 8, "granularity": "minute"},
                    "نه دقیقه": {"minutes": 9, "granularity": "minute"},
                    "ده دقیقه": {"minutes": 10, "granularity": "minute"},
                    "پانزده دقیقه": {"minutes": 15, "granularity": "minute"},
                    "بیست دقیقه": {"minutes": 20, "granularity": "minute"},
                    "سی دقیقه": {"minutes": 30, "granularity": "minute"},
                    "چهل دقیقه": {"minutes": 40, "granularity": "minute"},
                    "پنجاه دقیقه": {"minutes": 50, "granularity": "minute"},
                    "شصت دقیقه": {"minutes": 60, "granularity": "minute"},
                    # Special cases
                    "امروز": {"days": 1, "granularity": "hour"},
                    "دیروز": {"days": 1, "granularity": "hour", "offset": -1},
                    "هفته گذشته": {"days": 7, "granularity": "week", "offset": -7},
                    "هفته اخیر": {"days": 7, "granularity": "week"},
                    "ماه قبل": {"days": 30, "granularity": "day", "offset": -30},
                    "ماه اخیر": {"days": 30, "granularity": "day"},
                    "اخیراً": {"days": 1, "granularity": "hour"},
                    "گذشته": {"days": 3, "granularity": "day"},
                    "اخیر": {"days": 3, "granularity": "day"},
                    
                    # Enhanced "ago" patterns
                    "یک ساعت پیش": {"hours": 1, "granularity": "hour", "offset": -1},
                    "دو ساعت پیش": {"hours": 2, "granularity": "hour", "offset": -2},
                    "سه ساعت پیش": {"hours": 3, "granularity": "hour", "offset": -3},
                    "چهار ساعت پیش": {"hours": 4, "granularity": "hour", "offset": -4},
                    "پنج ساعت پیش": {"hours": 5, "granularity": "hour", "offset": -5},
                    "شش ساعت پیش": {"hours": 6, "granularity": "hour", "offset": -6},
                    
                    # Enhanced "last" patterns
                    "هفته گذشته": {"days": 7, "granularity": "week", "offset": -7},
                    "ماه گذشته": {"days": 30, "granularity": "day", "offset": -30},
                    "روز گذشته": {"days": 1, "granularity": "day", "offset": -1},
                    
                    # Enhanced "recent" patterns
                    "اخیراً": {"days": 1, "granularity": "hour"},
                    "اخیر": {"days": 3, "granularity": "day"},
                    "گذشته": {"days": 3, "granularity": "day"}
                }
                
                # Check for exact pattern matches first
                for pattern, config in persian_patterns.items():
                    if pattern in query_lower:
                        logger.info(f" Parsed Persian time pattern: {pattern} -> {config}")
                        return config
                
                # Enhanced regex-based parsing for Persian numerals
                import re
                
                # Pattern for "X روز اخیر/گذشته" where X is Persian numeral or digit
                # Use word boundaries to match complete Persian words
                day_pattern = r'\b(یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده|۱|۲|۳|۴|۵|۶|۷|۸|۹|۰|\d+)\s*روز\s*(اخیر|گذشته)'
                day_match = re.search(day_pattern, query_lower)
                if day_match:
                    number_text = day_match.group(1)
                    # Convert Persian numeral to number
                    if number_text in persian_numerals:
                        days = persian_numerals[number_text]
                    else:
                        try:
                            days = int(number_text)
                        except ValueError:
                            days = 3  # Default fallback
                    
                    # FIXED: Use day granularity for day queries
                    granularity = "day"
                    logger.info(f" Parsed Persian numeral pattern: {number_text} روز -> {days} days, granularity: {granularity}")
                    return {"days": days, "granularity": granularity}
                
                # Pattern for "X هفته اخیر/گذشته"
                week_pattern = r'\b(یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده|۱|۲|۳|۴|۵|۶|۷|۸|۹|۰|\d+)\s*هفته\s*(اخیر|گذشته)'
                week_match = re.search(week_pattern, query_lower)
                if week_match:
                    number_text = week_match.group(1)
                    if number_text in persian_numerals:
                        weeks = persian_numerals[number_text]
                    else:
                        try:
                            weeks = int(number_text)
                        except ValueError:
                            weeks = 1  # Default fallback
                    
                    days = weeks * 7
                    # FIXED: Use week granularity for week queries
                    logger.info(f" Parsed Persian numeral pattern: {number_text} هفته -> {days} days, granularity: week")
                    return {"days": days, "granularity": "week"}
                
                # Pattern for "X ماه اخیر/گذشته"
                month_pattern = r'\b(یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده|۱|۲|۳|۴|۵|۶|۷|۸|۹|۰|\d+)\s*ماه\s*(اخیر|گذشته)'
                month_match = re.search(month_pattern, query_lower)
                if month_match:
                    number_text = month_match.group(1)
                    if number_text in persian_numerals:
                        months = persian_numerals[number_text]
                    else:
                        try:
                            months = int(number_text)
                        except ValueError:
                            months = 1  # Default fallback
                    
                    days = months * 30
                    logger.info(f" Parsed Persian numeral pattern: {number_text} ماه -> {days} days")
                    return {"days": days, "granularity": "day"}
                
                # Pattern for "X ساعت اخیر/گذشته"
                hour_pattern = r'\b(یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده|۱|۲|۳|۴|۵|۶|۷|۸|۹|۰|\d+)\s*ساعت\s*(اخیر|گذشته)'
                hour_match = re.search(hour_pattern, query_lower)
                if hour_match:
                    number_text = hour_match.group(1)
                    if number_text in persian_numerals:
                        hours = persian_numerals[number_text]
                    else:
                        try:
                            hours = int(number_text)
                        except ValueError:
                            hours = 1  # Default fallback
                    
                    # Use hour granularity for hour queries
                    granularity = "hour"
                    logger.info(f" Parsed Persian numeral pattern: {number_text} ساعت -> {hours} hours, granularity: {granularity}")
                    return {"hours": hours, "granularity": granularity}
                
                # Pattern for "X دقیقه اخیر/گذشته"
                minute_pattern = r'\b(یک|دو|سه|چهار|پنج|شش|هفت|هشت|نه|ده|پانزده|بیست|سی|چهل|پنجاه|شصت|۱|۲|۳|۴|۵|۶|۷|۸|۹|۰|\d+)\s*دقیقه\s*(اخیر|گذشته)'
                minute_match = re.search(minute_pattern, query_lower)
                if minute_match:
                    number_text = minute_match.group(1)
                    if number_text in persian_numerals:
                        minutes = persian_numerals[number_text]
                    else:
                        try:
                            minutes = int(number_text)
                        except ValueError:
                            minutes = 30  # Default fallback
                    
                    # Use minute granularity for minute queries
                    granularity = "minute"
                    logger.info(f" Parsed Persian numeral pattern: {number_text} دقیقه -> {minutes} minutes, granularity: {granularity}")
                    return {"minutes": minutes, "granularity": granularity}
            
            # English time patterns with granularity
            english_patterns = {
                # Hours - FIXED: Use hour granularity for hour queries
                "one hour": {"hours": 1, "granularity": "hour"},
                "two hours": {"hours": 2, "granularity": "hour"},
                "three hours": {"hours": 3, "granularity": "hour"},
                "four hours": {"hours": 4, "granularity": "hour"},
                "five hours": {"hours": 5, "granularity": "hour"},
                "six hours": {"hours": 6, "granularity": "hour"},
                "seven hours": {"hours": 7, "granularity": "hour"},
                "eight hours": {"hours": 8, "granularity": "hour"},
                "nine hours": {"hours": 9, "granularity": "hour"},
                "ten hours": {"hours": 10, "granularity": "hour"},
                "twelve hours": {"hours": 12, "granularity": "hour"},
                "twenty four hours": {"hours": 24, "granularity": "hour"},
                # Days - FIXED: Use day granularity for day queries
                "one day": {"days": 1, "granularity": "day"},
                "two days": {"days": 2, "granularity": "day"},
                "three days": {"days": 3, "granularity": "day"},
                "four days": {"days": 4, "granularity": "day"},
                "five days": {"days": 5, "granularity": "day"},
                "six days": {"days": 6, "granularity": "day"},
                "seven days": {"days": 7, "granularity": "day"},
                # Weeks
                "one week": {"days": 7, "granularity": "week"},
                "two weeks": {"days": 14, "granularity": "week"},
                "three weeks": {"days": 21, "granularity": "week"},
                # Enhanced "ago" patterns
                "one hour ago": {"hours": 1, "granularity": "hour", "offset": -1},
                "two hours ago": {"hours": 2, "granularity": "hour", "offset": -2},
                "three hours ago": {"hours": 3, "granularity": "hour", "offset": -3},
                "four hours ago": {"hours": 4, "granularity": "hour", "offset": -4},
                "five hours ago": {"hours": 5, "granularity": "hour", "offset": -5},
                "six hours ago": {"hours": 6, "granularity": "hour", "offset": -6},
                "one day ago": {"days": 1, "granularity": "day", "offset": -1},
                "two days ago": {"days": 2, "granularity": "day", "offset": -2},
                "three days ago": {"days": 3, "granularity": "day", "offset": -3},
                "one week ago": {"days": 7, "granularity": "week", "offset": -7},
                "two weeks ago": {"days": 14, "granularity": "week", "offset": -14},
                "three weeks ago": {"days": 21, "granularity": "week", "offset": -21},
                # Enhanced "last" patterns
                "last week": {"days": 7, "granularity": "week", "offset": -7},
                "last month": {"days": 30, "granularity": "day", "offset": -30},
                "last day": {"days": 1, "granularity": "day", "offset": -1},
                "last hour": {"hours": 1, "granularity": "hour", "offset": -1},
                # Enhanced "recent" patterns
                "recently": {"days": 1, "granularity": "hour"},
                "recent": {"days": 3, "granularity": "day"},
                "past": {"days": 3, "granularity": "day"},
                # Months
                "one month": {"days": 30, "granularity": "day"},
                "two months": {"days": 60, "granularity": "day"},
                "three months": {"days": 90, "granularity": "day"},
                # Minutes
                "ten minutes": {"minutes": 10, "granularity": "minute"},
                "twenty minutes": {"minutes": 20, "granularity": "minute"},
                "thirty minutes": {"minutes": 30, "granularity": "minute"},
                "forty minutes": {"minutes": 40, "granularity": "minute"},
                "fifty minutes": {"minutes": 50, "granularity": "minute"},
                # Special cases
                "today": {"days": 1, "granularity": "hour"},
                "yesterday": {"days": 1, "granularity": "hour", "offset": -1},
                "last week": {"days": 7, "granularity": "week", "offset": -7},
                "past week": {"days": 7, "granularity": "week"},
                "last month": {"days": 30, "granularity": "day", "offset": -30},
                "past month": {"days": 30, "granularity": "day"},
                "recently": {"days": 1, "granularity": "hour"},
                "past": {"days": 3, "granularity": "day"}
            }
            
            for pattern, config in english_patterns.items():
                if pattern in query_lower:
                    logger.info(f" Parsed English time pattern: {pattern} -> {config}")
                    return config
            
            # Check for generic "last" patterns with better context detection
            if "last" in query_lower or "past" in query_lower:
                # Check for week context
                if any(word in query_lower for word in ["week", "weeks"]):
                    logger.info(f" Generic 'last week' pattern detected, using 7 days")
                    return {"days": 7, "granularity": "week"}
                # Check for month context
                elif any(word in query_lower for word in ["month", "months"]):
                    logger.info(f" Generic 'last month' pattern detected, using 30 days")
                    return {"days": 30, "granularity": "day"}
                # Check for day context
                elif any(word in query_lower for word in ["day", "days"]):
                    logger.info(f" Generic 'last day' pattern detected, using 1 day")
                    return {"days": 1, "granularity": "day"}
                # Check for hour context - extract specific number of hours
                elif any(word in query_lower for word in ["hour", "hours"]):
                    # Try to extract specific number of hours
                    import re
                    hour_match = re.search(r'(\d+)\s*hours?', query_lower)
                    if hour_match:
                        hours = int(hour_match.group(1))
                        logger.info(f" Generic 'last {hours} hours' pattern detected, using {hours} hours")
                        return {"hours": hours, "granularity": "hour"}
                    else:
                         logger.info(f" Generic 'last hour' pattern detected, using 1 hour")
                    return {"hours": 1, "granularity": "hour"}
                # Default fallback
                else:
                    logger.info(f" Generic 'last' pattern detected, defaulting to 3 days")
                    return {"days": 3, "granularity": "day"}
    
    def _llm_refine_sql(self, original_query: str, generated_sql: str, execution_summary: str, ontology_snippet: str, schema: str) -> Dict[str, Any]:
        """Use LLM to refine SQL query when execution returns empty results"""
        try:
            prompt = f"""You are an expert SQL query optimizer for an agriculture sensor database.

DATABASE SCHEMA:
{schema}

ONTOLOGY CONTEXT:
{ontology_snippet}

ORIGINAL USER QUERY: {original_query}
GENERATED SQL: {generated_sql}
EXECUTION RESULT: {execution_summary}

The SQL query returned empty results. Please analyze and provide a corrected SQL query or suggest alternative sensor types.

RULES:
1. Only provide SELECT queries
2. Use sensor_data table only
3. Prefer SQL correction over sensor suggestions
4. Ensure proper time filtering
5. Use appropriate aggregation for time-based queries

Respond in JSON format:
{{
    "action": "correct_sql" | "suggest_sensors",
    "corrected_sql": "SELECT ... FROM sensor_data WHERE ...",
    "suggested_sensors": ["sensor1", "sensor2"],
    "reasoning": "Explanation of the correction",
    "confidence": 0.0-1.0
}}

If correcting SQL, provide the corrected_sql field.
If suggesting sensors, provide the suggested_sensors field.
Always provide reasoning and confidence score."""

            # Log LLM call with truncated prompt
            truncated_prompt = prompt[:200] + "..." if len(prompt) > 200 else prompt
            logger.info(f"🤖 LLM Call - SQL Refinement (Prompt): {truncated_prompt}")
            
            response = self.llm.invoke(prompt)
            response_text = response.content.strip()
            
            # Log LLM response (truncated)
            truncated_response = response_text[:100] + "..." if len(response_text) > 100 else response_text
            logger.info(f"🤖 LLM Call - SQL Refinement (Response): {truncated_response}")
            
            # Parse JSON response
            import json
            try:
                result = json.loads(response_text)
                logger.info(f"🤖 LLM SQL refinement result: {result}")
                return result
            except json.JSONDecodeError:
                logger.error(f" Failed to parse LLM refinement response as JSON: {response_text}")
                return {
                    "action": "suggest_sensors",
                    "suggested_sensors": ["temperature", "humidity"],
                    "reasoning": "Failed to parse LLM response",
                    "confidence": 0.1
                }
                
        except Exception as e:
            logger.error(f" Error in LLM SQL refinement: {str(e)}")
            return {
                "action": "suggest_sensors", 
                "suggested_sensors": ["temperature"],
                "reasoning": f"LLM refinement error: {str(e)}",
                "confidence": 0.1
            }
    
    def _generate_time_aware_sql(self, sensor_type: str, time_config: Dict[str, Any], english_query: str) -> str:
        """Generate time-aware SQL with proper aggregation and grouping"""
        try:
            granularity = time_config.get("granularity", "day")
            offset = time_config.get("offset", 0)
            
            # Build time window condition
            time_condition = self._build_time_window_condition(time_config, offset)
            
            # Build GROUP BY clause based on granularity
            group_by_clause = self._build_group_by_clause(granularity)
            
            # Build SELECT clause with aggregations
            select_clause = self._build_aggregation_select(granularity)
            
            # Generate the complete SQL
            sql = f"""
            SELECT {select_clause}
            FROM sensor_data 
            WHERE sensor_type = '{sensor_type}' 
            AND {time_condition}
            GROUP BY {group_by_clause}
            ORDER BY {group_by_clause} ASC
            """
            
            # Clean up the SQL (remove extra whitespace)
            sql = ' '.join(sql.split())
            
            logger.info(f" Generated time-aware SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f" Error generating time-aware SQL: {e}")
            return f"SELECT * FROM sensor_data WHERE sensor_type = '{sensor_type}' ORDER BY timestamp DESC LIMIT 10"
    
    def _build_time_window_condition(self, time_config: Dict[str, Any], offset: int = 0) -> str:
        """Build SQL time window condition"""
        try:
            if "days" in time_config:
                days = time_config["days"] + offset
                if offset < 0:
                    # For past periods (yesterday, last week)
                    return f"timestamp >= datetime('now', '-{abs(days)} days') AND timestamp < datetime('now', '-{abs(offset)} days')"
                else:
                    return f"timestamp >= datetime('now', '-{days} days')"
            
            elif "hours" in time_config:
                hours = time_config["hours"] + offset
                if offset < 0:
                    return f"timestamp >= datetime('now', '-{abs(hours)} hours') AND timestamp < datetime('now', '-{abs(offset)} hours')"
                else:
                    return f"timestamp >= datetime('now', '-{hours} hours')"
            
            elif "minutes" in time_config:
                minutes = time_config["minutes"] + offset
                if offset < 0:
                    return f"timestamp >= datetime('now', '-{abs(minutes)} minutes') AND timestamp < datetime('now', '-{abs(offset)} minutes')"
                else:
                    return f"timestamp >= datetime('now', '-{minutes} minutes')"
            
            else:
                # Default to last 24 hours
                return "timestamp >= datetime('now', '-1 days')"
                
        except Exception as e:
            logger.error(f" Error building time window: {e}")
            return "timestamp >= datetime('now', '-1 days')"
    
    def _build_group_by_clause(self, granularity: str) -> str:
        """Build GROUP BY clause based on time granularity"""
        try:
            if granularity == "day":
                return "DATE(timestamp)"
            elif granularity == "hour":
                return "strftime('%Y-%m-%d %H:00', timestamp)"
            elif granularity == "minute":
                return "strftime('%Y-%m-%d %H:%M', timestamp)"
            elif granularity == "week":
                # Group by week: use strftime to get week number
                return "strftime('%Y-%W', timestamp)"
            else:
                return "DATE(timestamp)"
                
        except Exception as e:
            logger.error(f" Error building GROUP BY clause: {e}")
            return "DATE(timestamp)"
    
    def _build_aggregation_select(self, granularity: str) -> str:
        """Build SELECT clause with proper aggregations"""
        try:
            if granularity == "day":
                return "DATE(timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
            elif granularity == "hour":
                return "strftime('%Y-%m-%d %H:00', timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
            elif granularity == "minute":
                return "strftime('%Y-%m-%d %H:%M', timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
            elif granularity == "week":
                return "strftime('%Y-%W', timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
            else:
                return "DATE(timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                
        except Exception as e:
            logger.error(f" Error building aggregation SELECT: {e}")
            return "DATE(timestamp) as time_period, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
    
    def _generate_compound_time_aware_sql(self, sensor_types: List[str], time_config: Dict[str, Any], english_query: str) -> str:
        """Generate time-aware SQL for compound queries with multiple sensor types"""
        try:
            granularity = time_config.get("granularity", "day")
            offset = time_config.get("offset", 0)
            
            # Create IN clause for multiple sensor types
            sensor_list = "', '".join(sensor_types)
            
            # Build time window condition
            time_condition = self._build_time_window_condition(time_config, offset)
            
            # Build GROUP BY clause based on granularity
            group_by_clause = self._build_group_by_clause(granularity)
            
            # Build SELECT clause with aggregations for compound queries
            if granularity == "day":
                select_clause = f"DATE(timestamp) as time_period, sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                group_by_clause = f"DATE(timestamp), sensor_type"
            elif granularity == "hour":
                select_clause = f"strftime('%Y-%m-%d %H:00', timestamp) as time_period, sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                group_by_clause = f"strftime('%Y-%m-%d %H:00', timestamp), sensor_type"
            elif granularity == "minute":
                select_clause = f"strftime('%Y-%m-%d %H:%M', timestamp) as time_period, sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                group_by_clause = f"strftime('%Y-%m-%d %H:%M', timestamp), sensor_type"
            elif granularity == "week":
                select_clause = f"strftime('%Y-%W', timestamp) as time_period, sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                group_by_clause = f"strftime('%Y-%W', timestamp), sensor_type"
            else:
                select_clause = f"DATE(timestamp) as time_period, sensor_type, AVG(value) as avg_value, MIN(value) as min_value, MAX(value) as max_value, COUNT(*) as data_points"
                group_by_clause = f"DATE(timestamp), sensor_type"
            
            # Generate the complete SQL
            sql = f"""
            SELECT {select_clause}
            FROM sensor_data 
            WHERE sensor_type IN ('{sensor_list}') 
            AND {time_condition}
            GROUP BY {group_by_clause}
            ORDER BY {group_by_clause} ASC
            """
            
            # Clean up the SQL (remove extra whitespace)
            sql = ' '.join(sql.split())
            
            logger.info(f" Generated compound time-aware SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f" Error generating compound time-aware SQL: {e}")
            sensor_list = "', '".join(sensor_types)
            return f"SELECT * FROM sensor_data WHERE sensor_type IN ('{sensor_list}') ORDER BY timestamp DESC LIMIT 10"
    
    def _generate_compound_sql(self, sensor_types: List[str], english_query: str, language: str = "en") -> str:
        """Generate SQL for compound queries with multiple sensor types"""
        try:
            logger.info(f" Generating compound SQL for sensors: {sensor_types}")
            
            # Create IN clause for multiple sensor types
            sensor_list = "', '".join(sensor_types)
            
            # Determine query pattern
            query_patterns = self.ontology.get("query_patterns", {})
            query_lower = english_query.lower()
            
            # Check for time-based queries using new time-aware system
            time_config = self._parse_time_expression(english_query, language)
            if time_config:
                sql = self._generate_compound_time_aware_sql(sensor_types, time_config, english_query)
                logger.info(f" Generated compound time-aware SQL: {sql}")
                return sql
            
            # Check for current/latest value
            current_indicators = query_patterns.get("current_value", {}).get("persian", []) + \
                               query_patterns.get("current_value", {}).get("english", [])
            if any(indicator in query_lower for indicator in current_indicators):
                sql = f"SELECT * FROM sensor_data WHERE sensor_type IN ('{sensor_list}') ORDER BY timestamp DESC LIMIT {len(sensor_types)}"
                logger.info(f" Generated compound current value SQL: {sql}")
                return sql
            
            # Check for average value
            avg_indicators = query_patterns.get("average_value", {}).get("persian", []) + \
                           query_patterns.get("average_value", {}).get("english", [])
            if any(indicator in query_lower for indicator in avg_indicators):
                sql = f"SELECT sensor_type, AVG(value) as avg_value FROM sensor_data WHERE sensor_type IN ('{sensor_list}') GROUP BY sensor_type"
                logger.info(f" Generated compound average value SQL: {sql}")
                return sql
            
            # Check for trend analysis
            trend_indicators = query_patterns.get("trend_analysis", {}).get("persian", []) + \
                             query_patterns.get("trend_analysis", {}).get("english", [])
            if any(indicator in query_lower for indicator in trend_indicators):
                sql = f"SELECT timestamp, sensor_type, value FROM sensor_data WHERE sensor_type IN ('{sensor_list}') ORDER BY timestamp DESC LIMIT 20"
                logger.info(f" Generated compound trend analysis SQL: {sql}")
                return sql
            
            # Default: get latest values for all sensors
            sql = f"SELECT * FROM sensor_data WHERE sensor_type IN ('{sensor_list}') ORDER BY timestamp DESC LIMIT {len(sensor_types)}"
            logger.info(f" Generated compound default SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f" Error in compound SQL generation: {e}")
            # Fallback to simple compound query
            sensor_list = "', '".join(sensor_types)
            return f"SELECT * FROM sensor_data WHERE sensor_type IN ('{sensor_list}') ORDER BY timestamp DESC LIMIT 10"

    def _generate_simple_sql(self, english_query: str) -> str:
        """Generate simple SQL based on query content"""
        query_lower = english_query.lower()
        
        # Check for dangerous queries first (more specific to avoid false positives)
        dangerous_keywords = ['drop table', 'delete from', 'update set', 'insert into', 'alter table', 'create table', 'truncate table', 'remove table', 'clear table']
        for keyword in dangerous_keywords:
            if keyword in query_lower:
                logger.warning(f"  Dangerous query detected in SQL generation: {keyword}")
                # Return the dangerous query as-is so validation can catch it
                return english_query
        
        # Generate safe SQL for normal queries
        if any(word in query_lower for word in ['temperature', 'temp']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type = 'temperature' ORDER BY timestamp DESC LIMIT 10"
        elif any(word in query_lower for word in ['humidity', 'moisture']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type = 'humidity' ORDER BY timestamp DESC LIMIT 10"
        elif any(word in query_lower for word in ['irrigation', 'water', 'soil']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type IN ('soil_moisture', 'water_usage') ORDER BY timestamp DESC LIMIT 10"
        elif any(word in query_lower for word in ['pest', 'disease']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type IN ('pest_count', 'disease_risk') ORDER BY timestamp DESC LIMIT 10"
        elif any(word in query_lower for word in ['co2', 'carbon']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type = 'co2_level' ORDER BY timestamp DESC LIMIT 10"
        elif any(word in query_lower for word in ['light', 'luminosity']):
            return "SELECT timestamp, value FROM sensor_data WHERE sensor_type = 'light' ORDER BY timestamp DESC LIMIT 10"
        else:
            return "SELECT timestamp, sensor_type, value FROM sensor_data ORDER BY timestamp DESC LIMIT 10"
    
    def _execute_direct_sql(self, sql_query: str) -> Dict[str, Any]:
        """Execute SQL query directly and return results with validation"""
        try:
            import sqlite3
            
            # Step 1: Validate SQL query before execution
            validation_result = self._validate_sql_query(sql_query)
            if not validation_result["valid"]:
                logger.error(f" SQL Validation Failed: {validation_result['message']}")
                return {
                    "success": False,
                    "error": validation_result["message"],
                    "data": [],
                    "validation": validation_result
                }
            
            logger.info(f" SQL Validation Passed: {validation_result['message']}")
            
            # Step 2: Connect to database
            # Use proper database path for Liara
            if os.getenv("LIARA_APP_ID"):
                db_dir = "/var/lib/data"
                os.makedirs(db_dir, exist_ok=True)
                db_path = os.path.join(db_dir, "smart_dashboard.db")
            else:
                db_path = "smart_dashboard.db"
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Step 3: Execute the query with error handling and query logging
            try:
                # Log the query being executed
                logger.info(f" Executing SQL Query: {sql_query}")
                
                cursor.execute(sql_query)
                results = cursor.fetchall()
                
                # Step 4: Get column names
                columns = [description[0] for description in cursor.description]
                
                # Step 5: Convert to list of dictionaries
                data = []
                for row in results:
                    row_dict = {}
                    for i, value in enumerate(row):
                        row_dict[columns[i]] = value
                    data.append(row_dict)
                
                logger.info(f" SQL Execution Success: {len(data)} rows returned")
                logger.info(f" Query Columns: {columns}")
                logger.info(f" Sample Data: {data[:3] if data else 'No data'}")
                
                return {
                    "success": True,
                    "data": data,
                    "validation": validation_result,
                    "columns": columns,
                    "query_executed": sql_query
                }
                
            except sqlite3.Error as e:
                logger.error(f" SQL Execution Error: {str(e)}")
                logger.error(f" Failed Query: {sql_query}")
                return {
                    "success": False,
                    "error": f"SQL execution failed: {str(e)}",
                    "data": [],
                    "validation": {"valid": False, "message": f"Execution error: {str(e)}"},
                    "query_executed": sql_query
                }
            finally:
                conn.close()
            
        except Exception as e:
            logger.error(f" Database Connection Error: {str(e)}")
            return {
                "success": False,
                "error": f"Database connection failed: {str(e)}",
                "data": [],
                "validation": {"valid": False, "message": f"Connection error: {str(e)}"}
            }
    
    def _validate_sql_query(self, sql_query: str) -> Dict[str, Any]:
        """Validate SQL query for safety and correctness"""
        try:
            sql_lower = sql_query.lower().strip()
            
            # Check 1: Only SELECT queries allowed
            if not sql_lower.startswith('select'):
                return {
                    "valid": False,
                    "message": "Only SELECT queries are allowed"
                }
            
            # Check 2: No dangerous operations
            dangerous_keywords = ['drop table', 'delete from', 'insert into', 'update set', 'alter table', 'create table', 'truncate table']
            for keyword in dangerous_keywords:
                if keyword in sql_lower:
                    return {
                        "valid": False,
                        "message": f"Dangerous operation '{keyword}' not allowed"
                    }
            
            # Check 3: Must use sensor_data table
            if 'sensor_data' not in sql_lower:
                return {
                    "valid": False,
                    "message": "Query must use sensor_data table"
                }
            
            # Check 4: Check for valid sensor types
            valid_sensor_types = [
                'temperature', 'humidity', 'co2_level', 'light', 'pressure',
                'soil_moisture', 'water_usage', 'pest_count', 'disease_risk',
                'rainfall', 'wind_speed', 'energy_usage', 'yield_prediction',
                'soil_temperature', 'leaf_wetness', 'motion', 'fruit_count',
                'fruit_size', 'plant_height', 'nutrient_uptake', 'fertilizer_usage',
                'soil_ph', 'nitrogen_level', 'phosphorus_level', 'potassium_level',
                'pest_detection', 'water_efficiency', 'yield_efficiency',
                'tomato_price', 'lettuce_price', 'pepper_price',
                'co2', 'cost_per_kg', 'demand_level', 'leaf_count',
                'profit_margin', 'supply_level', 'test_temperature'
            ]
            
            # Check if query references valid sensor types (only if sensor_type is explicitly mentioned)
            if 'sensor_type' in sql_lower:
                print(f" SQL Query contains sensor_type: {sql_lower}")
            has_valid_sensor_type = False
            for sensor_type in valid_sensor_types:
                # Check for sensor type with quotes (both single and double)
                if f"'{sensor_type}'" in sql_lower or f'"{sensor_type}"' in sql_lower or sensor_type in sql_lower:
                    has_valid_sensor_type = True
                    print(f" Found valid sensor type: {sensor_type}")
                    break
            
            if not has_valid_sensor_type:
                print(f" Query does not reference valid sensor types: {sql_lower}")
                return {
                    "valid": False,
                    "message": "Query must reference valid sensor types"
                }
            
            # Check 5: Basic SQL syntax check
            if not ('from' in sql_lower and 'select' in sql_lower):
                return {
                    "valid": False,
                    "message": "Invalid SQL syntax"
                }
            
            return {
                "valid": True,
                "message": "Query validation passed",
                "sensor_types_found": [st for st in valid_sensor_types if st in sql_lower],
                "query_type": "SELECT",
                "table_used": "sensor_data"
            }
            
        except Exception as e:
            return {
                "valid": False,
                "message": f"Validation error: {str(e)}"
            }
    
    def _extract_sql_from_response(self, agent_response) -> str:
        """Extract SQL query from agent response"""
        try:
            if hasattr(agent_response, 'output'):
                output = agent_response.output
                # Look for SQL in the output - the agent shows the query in the logs
                if 'SELECT' in output.upper():
                    lines = output.split('\n')
                    for line in lines:
                        if 'SELECT' in line.upper() and 'FROM' in line.upper():
                            # Clean up the SQL query
                            sql = line.strip()
                            if sql.startswith('```sql'):
                                sql = sql.replace('```sql', '').replace('```', '').strip()
                            return sql
            return "SELECT * FROM sensor_data LIMIT 5"
        except:
            return "SELECT * FROM sensor_data LIMIT 5"
    
    def _extract_data_from_response(self, agent_response) -> List[Dict[str, Any]]:
        """Extract data from agent response"""
        try:
            if hasattr(agent_response, 'output'):
                output = agent_response.output
                # The agent response contains the actual data in the logs
                # Look for data patterns like: [('2025-09-20 07:28:27', 18.11), ...]
                import re
                
                # Find data tuples in the output
                data_pattern = r"\[(\([^)]+\),?\s*)+]"
                matches = re.findall(data_pattern, output)
                
                if matches:
                    # Parse the first match
                    data_str = matches[0]
                    # Convert string representation to actual data
                    try:
                        # This is a simplified parser - in production you'd want more robust parsing
                        data_str = data_str.replace("'", '"')  # Convert single quotes to double quotes
                        data_list = eval(data_str)  # Convert string to list of tuples
                        
                        # Convert tuples to dictionaries
                        result = []
                        for item in data_list:
                            if len(item) >= 2:
                                result.append({
                                    "timestamp": item[0],
                                    "value": item[1]
                                })
                        return result
                    except:
                        pass
                
                # Fallback: try to extract from the structured output
                if 'Final Answer:' in output:
                    # Extract data from the final answer section
                    lines = output.split('\n')
                    result = []
                    for line in lines:
                        if ' - ' in line and any(char.isdigit() for char in line):
                            parts = line.split(' - ')
                            if len(parts) >= 2:
                                timestamp = parts[0].strip()
                                value = parts[1].strip()
                                try:
                                    result.append({
                                        "timestamp": timestamp,
                                        "value": float(value)
                                    })
                                except:
                                    pass
                    return result
                    
            return []
        except Exception as e:
            logger.error(f"Data extraction error: {str(e)}")
            return []
    
    def _generate_mock_sql_result(self, english_query: str) -> Dict[str, Any]:
        """Generate mock SQL result for testing"""
        # Mock SQL based on query content
        if any(word in english_query.lower() for word in ['irrigation', 'water', 'soil']):
            sql = "SELECT * FROM sensor_data WHERE sensor_type IN ('soil_moisture', 'water_usage') ORDER BY timestamp DESC LIMIT 5"
            raw_data = [
                {"timestamp": "2025-09-20T04:44:08", "sensor_type": "soil_moisture", "value": 45.2},
                {"timestamp": "2025-09-20T04:44:05", "sensor_type": "water_usage", "value": 125.8}
            ]
        elif any(word in english_query.lower() for word in ['pest', 'disease']):
            sql = "SELECT * FROM sensor_data WHERE sensor_type IN ('pest_count', 'disease_risk') ORDER BY timestamp DESC LIMIT 5"
            raw_data = [
                {"timestamp": "2025-09-20T04:44:10", "sensor_type": "pest_count", "value": 2.1},
                {"timestamp": "2025-09-20T04:44:07", "sensor_type": "disease_risk", "value": 15.3}
            ]
        else:
            sql = "SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 5"
            raw_data = [
                {"timestamp": "2025-09-20T04:44:17", "sensor_type": "temperature", "value": 18.8},
                {"timestamp": "2025-09-20T04:44:15", "sensor_type": "humidity", "value": 86.65}
            ]
        
        return {
            "sql": sql,
            "raw_data": raw_data,
            "success": True
        }
    
    def _format_structured_response(self, sql_result: Dict[str, Any], english_query: str, feature_context: str, intent: str = "data_query", original_query: str = None, detected_lang: str = "en", time_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Format result into unified structured JSON with consistent schema"""
        # Initialize base response structure
        base_response = {
            "success": True,
                    "summary": "",
                    "metrics": {},
                    "raw_data": [],
            "chart": None,
            "chart_type": None,
            "chart_metadata": None,
            "comparison": None,
            "sql": "",
                    "translated_query": english_query,
                    "feature_context": feature_context,
                    "timestamp": datetime.utcnow().isoformat(),
            "validation": {
                "query_valid": True,
                "execution_success": True,
                "data_points": 0,
                "sensor_types": [],
                "chart_requested": False,
                "mapping": {},
                "refined_by_llm": False,
                "semantic_json": {}
            }
        }
        
        try:
            raw_data = sql_result.get("raw_data", [])
            sql_query = sql_result.get("sql", "")
            validation_result = sql_result.get("validation", {})
            
            # Check if validation failed
            if not validation_result.get("valid", True):
                logger.error(f" Validation failed: {validation_result.get('message', 'Unknown validation error')}")
                return self._create_error_response(
                    base_response=base_response,
                    error_message=validation_result.get("message", "Query validation failed"),
                    detected_lang=detected_lang,
                    sql_query=sql_query,
                    validation_result=validation_result,
                    sql_result=sql_result
                )
            
            # Detect chart request using original query and detected language
            chart_query = original_query if original_query else english_query
            chart_request = self._detect_chart_request(chart_query, detected_lang)
            
            # Extract metrics from raw data FIRST
            metrics = self._extract_metrics(raw_data)
            
            # Check if this is a comparison query
            semantic_json = sql_result.get("semantic_json", {})
            is_comparison = semantic_json.get("comparison", False)
            time_ranges = semantic_json.get("time_range", [])
            
            # Process comparison data if needed
            comparison_data = None
            if is_comparison and isinstance(time_ranges, list) and len(time_ranges) > 1:
                comparison_data = self._process_comparison_data(raw_data, time_ranges)
            
            # Generate summary using LLM with metrics and comparison data and chart info
            summary = self._generate_summary(english_query, raw_data, feature_context, intent, metrics, comparison_data, chart_request, time_context)
            
            # Process chart data if requested
            chart_data = None
            chart_metadata = None
            if chart_request["wants_chart"]:
                chart_data = self._process_chart_data(raw_data, chart_request["chart_type"])
                logger.info(f" Chart requested: {chart_request['chart_type']} - {chart_request['matched_term']}")
                
                # Generate explicit chart metadata
                chart_metadata = self._generate_chart_metadata(
                    chart_type=chart_request["chart_type"],
                    data=raw_data,
                    semantic_json=semantic_json,
                    matched_term=chart_request.get("matched_term", ""),
                    entity=semantic_json.get("entity", "unknown")
                )
            
            # Update base response with actual data
            base_response.update({
                "success": True,
                "response": summary,  # CRITICAL FIX: Add "response" field for frontend compatibility
                "summary": summary,
                "data": raw_data,  # CRITICAL FIX: Add "data" field for frontend compatibility
                "metrics": metrics,
                "raw_data": raw_data,
                "chart": chart_data,
                "chart_type": chart_request["chart_type"] if chart_request["wants_chart"] else None,
                "chart_metadata": chart_metadata,
                "comparison": comparison_data,
                "sql": sql_query,
                "validation": {
                    "query_valid": True,
                    "execution_success": True,
                    "data_points": len(raw_data),
                    "sensor_types": list(set([item.get('sensor_type', 'unknown') for item in raw_data if 'sensor_type' in item])),
                    "chart_requested": chart_request["wants_chart"],
                    "mapping": sql_result.get("mapping", {}),
                    "refined_by_llm": sql_result.get("refined_by_llm", False),
                    "semantic_json": semantic_json
                }
            })
            
            return base_response
            
        except Exception as e:
            logger.error(f" Response Formatting Error: {str(e)}")
            return self._create_error_response(
                base_response=base_response,
                error_message=f"Response formatting error: {str(e)}",
                detected_lang=detected_lang,
                sql_query=sql_result.get("sql", ""),
                validation_result={"valid": False, "message": str(e)},
                sql_result=sql_result
            )
    
    def _generate_chart_metadata(self, chart_type: str, data: List[Dict[str, Any]], semantic_json: Dict[str, Any], matched_term: str = "", entity: str = "unknown") -> Dict[str, Any]:
        """Generate explicit chart metadata configuration"""
        try:
            # Extract sensor types from data
            sensor_types = list(set([item.get('sensor_type', 'unknown') for item in data if 'sensor_type' in item]))
            
            # Determine axis labels
            entity_str = entity if isinstance(entity, str) else entity[0] if isinstance(entity, list) and entity else "Value"
            x_axis_label = "Time" if "time_period" in (data[0] if data else {}) else "Data Point"
            y_axis_label = entity_str.replace('_', ' ').title()
            
            # Get unit from ontology
            unit = self.ontology.get("sensors", {}).get(entity_str, {}).get("unit", "")
            
            # Determine chart title
            time_range = semantic_json.get("time_range", "")
            if isinstance(time_range, list):
                time_range_str = " vs ".join(time_range)
            else:
                time_range_str = time_range
            
            chart_title = f"{y_axis_label} - {time_range_str}".title() if time_range_str else y_axis_label
            
            # Chart configuration
            metadata = {
                "chart_type": chart_type,
                "title": chart_title,
                "x_axis": {
                    "label": x_axis_label,
                    "type": "category" if "time_period" in (data[0] if data else {}) else "linear"
                },
                "y_axis": {
                    "label": y_axis_label,
                    "unit": unit,
                    "type": "linear"
                },
                "legend": {
                    "show": len(sensor_types) > 1,
                    "position": "top"
                },
                "colors": self._get_chart_colors(sensor_types),
                "data_points": len(data),
                "sensor_types": sensor_types,
                "matched_term": matched_term,
                "grouping": semantic_json.get("grouping", "none"),
                "time_range": time_range,
                "comparison": semantic_json.get("comparison", False)
            }
            
            # Add chart-specific configurations
            if chart_type == "line":
                metadata["line_config"] = {
                    "smooth": True,
                    "tension": 0.4,
                    "point_radius": 4,
                    "border_width": 2
                }
            elif chart_type == "bar":
                metadata["bar_config"] = {
                    "bar_thickness": 30,
                    "border_width": 1
                }
            elif chart_type == "pie":
                metadata["pie_config"] = {
                    "start_angle": 0,
                    "border_width": 2
                }
            
            return metadata
            
        except Exception as e:
            logger.error(f" Chart metadata generation error: {str(e)}")
            return {
                "chart_type": chart_type,
                "title": "Chart",
                "error": str(e)
            }
    
    def _get_chart_colors(self, sensor_types: List[str]) -> Dict[str, str]:
        """Get appropriate colors for chart based on sensor types"""
        color_palette = {
            "temperature": "#FF6384",
            "humidity": "#36A2EB",
            "soil_moisture": "#8B4513",
            "water_usage": "#4BC0C0",
            "water_efficiency": "#00CED1",
            "light": "#FFCE56",
            "co2_level": "#9966FF",
            "pest_count": "#FF9F40",
            "pest_detection": "#FF6384",
            "disease_risk": "#C9CBCF",
            "plant_height": "#4CAF50",
            "fruit_size": "#FF5722",
            "yield": "#FFC107",
            "ph": "#E91E63",
            "nutrient_level": "#795548",
            "default": "#808080"
        }
        
        colors = {}
        for sensor in sensor_types:
            colors[sensor] = color_palette.get(sensor, color_palette["default"])
        
        return colors
    
    def _create_error_response(self, base_response: Dict[str, Any], error_message: str, detected_lang: str, sql_query: str = "", validation_result: Dict[str, Any] = None, sql_result: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create unified error response with user-friendly messages in English and Persian"""
        try:
            # Create user-friendly error messages
            error_messages = self._get_user_friendly_error_messages(error_message, detected_lang)
            
            # Update base response for error case
            error_response = base_response.copy()
            error_response.update({
                "success": False,
                "error": error_messages["english"],
                "error_persian": error_messages["persian"],
                "summary": error_messages["summary"],
                "sql": sql_query,
                "validation": {
                    "query_valid": False,
                    "execution_success": False,
                    "data_points": 0,
                    "sensor_types": [],
                    "chart_requested": False,
                    "mapping": sql_result.get("mapping", {}) if sql_result else {},
                    "refined_by_llm": sql_result.get("refined_by_llm", False) if sql_result else False,
                    "semantic_json": sql_result.get("semantic_json", {}) if sql_result else {},
                    "error_details": validation_result or {}
                }
            })
            
            return error_response
            
        except Exception as e:
            logger.error(f" Error response creation failed: {str(e)}")
            # Fallback to basic error response
            return {
                "success": False,
                "error": "An unexpected error occurred",
                "error_persian": "خطای غیرمنتظره‌ای رخ داد",
                "summary": "Error processing query",
                "metrics": {},
                "raw_data": [],
                "chart": None,
                "chart_type": None,
                "chart_metadata": None,
                "comparison": None,
                "sql": sql_query,
                "translated_query": "",
                "feature_context": "",
                "timestamp": datetime.utcnow().isoformat(),
                "validation": {
                    "query_valid": False,
                    "execution_success": False,
                    "data_points": 0,
                    "sensor_types": [],
                    "chart_requested": False,
                    "mapping": {},
                    "refined_by_llm": False,
                    "semantic_json": {},
                    "error_details": {"message": str(e)}
                }
            }
    
    def _get_user_friendly_error_messages(self, error_message: str, detected_lang: str) -> Dict[str, str]:
        """Generate user-friendly error messages in English and Persian"""
        error_mappings = {
            "validation": {
                "english": "Your query couldn't be processed. Please try rephrasing your question.",
                "persian": "سوال شما قابل پردازش نیست. لطفاً سوال خود را به شکل دیگری بیان کنید.",
                "summary": "Query validation failed"
            },
            "execution": {
                "english": "No data available for your query. Please check:\n1. Sensor connectivity and power\n2. Data collection status\n3. Time range selection\n4. Sensor type availability",
                "persian": "داده‌ای برای سوال شما موجود نیست. لطفاً بررسی کنید:\n1. اتصال و برق سنسورها\n2. وضعیت جمع‌آوری داده\n3. انتخاب بازه زمانی\n4. در دسترس بودن نوع سنسور",
                "summary": "No data available - sensor troubleshooting"
            },
            "formatting": {
                "english": "There was an issue processing your request. Please try again.",
                "persian": "مشکلی در پردازش درخواست شما وجود دارد. لطفاً دوباره تلاش کنید.",
                "summary": "Request processing failed"
            },
            "default": {
                "english": "Something went wrong. Please try again or contact support.",
                "persian": "مشکلی پیش آمده است. لطفاً دوباره تلاش کنید یا با پشتیبانی تماس بگیرید.",
                "summary": "An error occurred"
            }
        }
        
        # Determine error type based on message content
        error_lower = error_message.lower()
        if "validation" in error_lower or "invalid" in error_lower:
            error_type = "validation"
        elif "execution" in error_lower or "sql" in error_lower or "database" in error_lower:
            error_type = "execution"
        elif "formatting" in error_lower or "response" in error_lower:
            error_type = "formatting"
        else:
            error_type = "default"
        
        return error_mappings[error_type]
    
    def _generate_summary(self, english_query: str, raw_data: List[Dict[str, Any]], feature_context: str, intent: str = "data_query", metrics: Dict[str, Any] = None, comparison_data: Dict[str, Any] = None, chart_request: Dict[str, Any] = None, time_context: Dict[str, Any] = None) -> str:
        """Generate summary using LLM with intent information, metrics, comparison data, and chart info"""
        try:
            if hasattr(self.llm, 'openai_api_key') and self.llm.openai_api_key:
                # Format metrics for LLM context
                metrics_text = ""
                if metrics:
                    if "aggregated" in metrics:
                        # Handle aggregated metrics (time-aware queries) with sensor type grouping
                        agg_metrics = metrics["aggregated"]
                        metrics_text = f"""
## AGGREGATED METRICS (Time-Aware Query):
- Sensor Types: {', '.join(agg_metrics.get('sensor_types', []))}
- Total Sensor Types: {agg_metrics.get('total_sensor_types', 0)}
- Total Data Points: {agg_metrics.get('total_data_points', 0)}
- Total Periods: {agg_metrics.get('total_periods', 0)}

## SENSOR-SPECIFIC METRICS:"""
                        
                        # Add metrics for each sensor type
                        for key, value in metrics.items():
                            if key not in ["aggregated"] and not key.endswith("_period_"):
                                sensor_type = key
                                sensor_metrics = value
                                metrics_text += f"""
### {sensor_type.replace('_', ' ').title()}:
- Average: {sensor_metrics.get('overall_average', 0)}
- Min: {sensor_metrics.get('overall_min', 0)}
- Max: {sensor_metrics.get('overall_max', 0)}
- Latest Period: {sensor_metrics.get('latest_period', 'unknown')}
- Latest Average: {sensor_metrics.get('latest_average', 0)}
- Data Points: {sensor_metrics.get('total_data_points', 0)}"""
                    else:
                        # Handle raw metrics (legacy)
                        metrics_text = f"\n## RAW METRICS:\n{json.dumps(metrics, indent=2)}"
                
                # Initialize variables
                time_periods_text = ""
                comparison_text = ""
                trend_analysis = ""
                
                # For time-based queries, show the actual time periods and values
                if raw_data and "avg_value" in raw_data[0]:
                    # This is aggregated data (time-aware query)
                    is_comparison = any(word in english_query.lower() for word in ["مقایسه", "compare", "vs", "با", "versus"])
                    
                    # Check if this is time breakdown data
                    is_daily_breakdown = "day" in raw_data[0]
                    is_time_breakdown = "time_period" in raw_data[0]
                    
                    # Start building time periods text with header
                    time_periods_text = "\n📊 Sensor Data by Time Range:\n"
                    
                    # Add comparison data if available
                    if comparison_data and comparison_data.get("sensor_comparisons"):
                        comparison_text = "\n## COMPARISON ANALYSIS:\n"
                        for sensor_type, comparison in comparison_data["sensor_comparisons"].items():
                            if "delta" in comparison and "percent_change" in comparison:
                                comparison_text += f"- {sensor_type}: {comparison['delta']:.2f} change ({comparison['percent_change']:.1f}%)\n"
                    
                    # Calculate trend for time breakdown
                    if (is_daily_breakdown or is_time_breakdown) and len(raw_data) > 1:
                        values = [item.get("avg_value", 0) for item in raw_data]
                        if len(values) >= 2:
                            first_val = values[0]
                            last_val = values[-1]
                            change = last_val - first_val
                            percent_change = (change / first_val * 100) if first_val != 0 else 0
                            
                            if change > 0:
                                trend_analysis = f"\n## Trend Analysis:\n- Overall trend: Increasing by {change:.2f} ({percent_change:.1f}%)\n"
                            elif change < 0:
                                trend_analysis = f"\n## Trend Analysis:\n- Overall trend: Decreasing by {abs(change):.2f} ({abs(percent_change):.1f}%)\n"
                            else:
                                trend_analysis = f"\n## Trend Analysis:\n- Overall trend: Stable (no significant change)\n"
                            
                            # Add period changes
                            period_changes = []
                            period_name = "Day" if is_daily_breakdown else "Period"
                            for i in range(1, len(values)):
                                prev_val = values[i-1]
                                curr_val = values[i]
                                period_change = curr_val - prev_val
                                period_changes.append(f"{period_name} {i}: {period_change:+.2f}")
                            
                            if period_changes:
                                trend_analysis += f"- {period_name} changes: {', '.join(period_changes)}\n"
                    
                    for i, item in enumerate(raw_data):
                        if is_daily_breakdown:
                            # Daily breakdown format with statistical data
                            day = item.get("day", f"Day {i+1}")
                            avg_value = item.get("avg_value", 0)
                            min_value = item.get("min_value", 0)
                            max_value = item.get("max_value", 0)
                            daily_range = item.get("daily_range", 0)
                            sensor_type = item.get("sensor_type", "sensor")
                            
                            time_periods_text += f"• {sensor_type.replace('_', ' ').title()}: Avg: {avg_value:.2f}, Min: {min_value:.2f}, Max: {max_value:.2f} ({day})\n"
                        elif is_time_breakdown:
                            # Time period breakdown format (hourly, weekly, monthly) with statistical data
                            time_period = item.get("time_period", f"Period {i+1}")
                            avg_value = item.get("avg_value", 0)
                            min_value = item.get("min_value", 0)
                            max_value = item.get("max_value", 0)
                            period_range = item.get("period_range", 0)
                            sensor_type = item.get("sensor_type", "sensor")
                            
                            # Format time period for display
                            display_period = time_period
                            if ":" in time_period:  # Hourly
                                try:
                                    from datetime import datetime
                                    dt = datetime.strptime(time_period, "%Y-%m-%d %H:%M")
                                    display_period = dt.strftime("%d %b %H:%M")
                                except:
                                    pass
                            elif len(time_period) == 7 and time_period.count("-") == 1:  # Weekly
                                try:
                                    year, week = time_period.split("-")
                                    display_period = f"Week {week}, {year}"
                                except:
                                    pass
                            elif len(time_period) == 7 and time_period.count("-") == 1:  # Monthly
                                try:
                                    from datetime import datetime
                                    dt = datetime.strptime(time_period, "%Y-%m")
                                    display_period = dt.strftime("%b %Y")
                                except:
                                    pass
                            
                            # Use exact time range from time_context if available
                            if time_context:
                                # Use the exact time range requested by user for ALL data points
                                time_range_label = f"Last {time_context['value']} {time_context['unit']}"
                            else:
                                time_range_label = display_period
                            time_periods_text += f"• {sensor_type.replace('_', ' ').title()}: Avg: {avg_value:.2f}, Min: {min_value:.2f}, Max: {max_value:.2f} ({time_range_label})\n"
                        else:
                            # Regular time period format with statistical data
                            time_period = item.get("time_period", f"Period {i+1}")
                            avg_value = item.get("avg_value", 0)
                            min_value = item.get("min_value", 0)
                            max_value = item.get("max_value", 0)
                            sensor_type = item.get("sensor_type", "sensor")
                            
                            if is_comparison and len(raw_data) == 2:
                                # For comparison queries, label periods as today/yesterday
                                if i == 0:
                                    period_label = "دیروز" if "دیروز" in english_query else "روز قبل"
                                else:
                                    period_label = "امروز" if "امروز" in english_query else "روز فعلی"
                                time_periods_text += f"• {sensor_type.replace('_', ' ').title()}: Avg: {avg_value:.2f}, Min: {min_value:.2f}, Max: {max_value:.2f} ({period_label})\n"
                            else:
                                # Use exact time range from time_context if available
                                if time_context:
                                    # Use the exact time range requested by user for ALL data points
                                    time_range_label = f"Last {time_context['value']} {time_context['unit']}"
                                else:
                                    time_range_label = time_period
                                time_periods_text += f"• {sensor_type.replace('_', ' ').title()}: Avg: {avg_value:.2f}, Min: {min_value:.2f}, Max: {max_value:.2f} ({time_range_label})\n"
                    
                # Build chart information text
                chart_info_text = ""
                if chart_request and chart_request.get("wants_chart"):
                    chart_info_text = f"""
## CHART AVAILABLE:
- Chart Type: {chart_request.get('chart_type', 'line')}
- Chart Purpose: Visualize the data trend over time
- Note: Mention that a visual chart is available to see the data graphically
"""
                
                # Add time_context information if available
                time_context_info = ""
                if time_context:
                    time_context_info = f"\n\nDetected Time Range: {time_context['value']} {time_context['unit']} (from {time_context['start_time']} to {time_context['end_time']})"
                    # Add specific instruction for time range display
                    time_context_info += f"\n\nCRITICAL INSTRUCTION: When displaying data, you MUST use the EXACT time range the user requested: '{time_context['value']} {time_context['unit']}'. DO NOT use generic labels like 'Last Hour', 'Last 6 Hours', 'Last 24 Hours', 'Last Week'. ONLY use the specific time range the user asked for."
                
                context = f"""You are a smart agriculture AI assistant. Provide concise, actionable responses.

RESPONSE FORMAT (KEEP IT SHORT):
1. **Brief overview** - 1-2 sentences about what the data shows
2. **Key data points** - Show the most important values  
3. **Quick analysis** - 2-3 sentences about trends/patterns
4. **Action items** - 2-3 specific recommendations

CRITICAL INSTRUCTIONS:
- Keep response under 200 words total
- Use EXACT time range from the data provided below
- NEVER use generic labels like "Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"
- NEVER use Persian generic labels like "آخرین ساعت", "آخرین ۶ ساعت", "آخرین ۲۴ ساعت", "آخرین هفته"
- ONLY use the EXACT time range shown in the data points below
- Be specific and actionable
- Focus on what matters most for farming decisions
- If Persian query, respond in Persian; if English, respond in English

DATA TO USE (USE THE EXACT TIME LABELS FROM THIS DATA):
{time_periods_text if time_periods_text else "No time period breakdown available"}

ANALYSIS TO INCLUDE:
{trend_analysis if trend_analysis else ""}
{comparison_text if comparison_text else ""}

{chart_info_text}

RESPONSE TEMPLATE:
```
📊 [Sensor Type] Data:
• [Copy the EXACT time labels from the data above, don't create new ones]

🔍 Analysis:
• [Brief trend analysis]

💡 Actions:
• [2-3 specific recommendations]
```

CRITICAL WARNING: DO NOT generate your own time range labels! Use ONLY the exact labels provided in the DATA TO USE section above!

Query: {english_query}
Feature Context: {feature_context}
Intent: {intent}
Data Points: {len(raw_data)}{time_context_info}

ACTUAL DATA FROM DATABASE (RAW):
{json.dumps(raw_data[:10], indent=2)}

Provide a natural, conversational response using the pre-formatted data sections above.
"""
                
                # Log LLM call with truncated context
                truncated_context = context[:200] + "..." if len(context) > 200 else context
                logger.info(f"🤖 LLM Call - Summary Generation (Prompt): {truncated_context}")
                
                response = self.llm.invoke(context)
                summary = response.content.strip()
                
                # Log LLM response (truncated)
                truncated_summary = summary[:100] + "..." if len(summary) > 100 else summary
                logger.info(f"🤖 LLM Call - Summary Generation (Response): {truncated_summary}")
                
                # Add intent information at the end
                intent_explanation = {
                    "data_query": " Data Query - Analyzed sensor data",
                    "chit_chat": " General Chat - Conversational response", 
                    "mixed": " Mixed Query - Combined data analysis and conversation"
                }
                
                intent_text = intent_explanation.get(intent, f" Intent: {intent}")
                return f"{summary}\n\n---\n{intent_text}"
            else:
                # Fallback for when LLM is not available
                return f"LLM service is currently unavailable. Please check your API configuration."
                    
        except Exception as e:
            logger.error(f"Summary generation error: {str(e)}")
            return f"Summary for query: {english_query}"
    
    def _extract_metrics(self, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metrics from raw data (handles both aggregated and raw data formats)"""
        try:
            if not raw_data:
                return {}
            
            # Check if data is in aggregated format (time-aware queries)
            if raw_data and "avg_value" in raw_data[0]:
                logger.info(f" Processing aggregated data format with {len(raw_data)} time periods")
                return self._extract_aggregated_metrics(raw_data)
            
            # Handle raw data format (legacy)
            logger.info(f" Processing raw data format with {len(raw_data)} data points")
            sensor_groups = {}
            for item in raw_data:
                sensor_type = item.get("sensor_type", "unknown")
                value = item.get("value", 0)
                
                if sensor_type not in sensor_groups:
                    sensor_groups[sensor_type] = []
                sensor_groups[sensor_type].append(value)
            
            # Calculate metrics for raw data
            metrics = {}
            for sensor_type, values in sensor_groups.items():
                if values:
                    metrics[sensor_type] = {
                        "count": len(values),
                        "average": round(sum(values) / len(values), 2),
                        "min": round(min(values), 2),
                        "max": round(max(values), 2),
                        "latest": round(values[0], 2) if values else 0
                    }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics extraction error: {str(e)}")
            return {}
    
    def _extract_aggregated_metrics(self, aggregated_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract metrics from aggregated data (time-aware queries) with proper sensor type grouping"""
        try:
            if not aggregated_data:
                return {}
            
            # Group data by sensor type for compound queries
            sensor_groups = {}
            for item in aggregated_data:
                sensor_type = item.get("sensor_type", "unknown")
                if sensor_type not in sensor_groups:
                    sensor_groups[sensor_type] = []
                sensor_groups[sensor_type].append(item)
            
            # Calculate metrics for each sensor type separately
            metrics = {}
            total_data_points = 0
            
            for sensor_type, sensor_data in sensor_groups.items():
                if sensor_data:
                    # Calculate metrics for this sensor type
                    avg_values = [item.get("avg_value", 0) for item in sensor_data]
                    min_values = [item.get("min_value", 0) for item in sensor_data]
                    max_values = [item.get("max_value", 0) for item in sensor_data]
                    data_points = sum(item.get("data_points", 0) for item in sensor_data)
                    total_data_points += data_points
                    
                    # Calculate weighted average for this sensor type
                    weighted_sum = sum(avg * item.get("data_points", 0) for avg, item in zip(avg_values, sensor_data))
                    sensor_average = weighted_sum / data_points if data_points > 0 else 0
                    
                    metrics[sensor_type] = {
                        "time_periods": len(sensor_data),
                        "total_data_points": data_points,
                        "overall_average": round(sensor_average, 2),
                        "overall_min": round(min(min_values), 2),
                        "overall_max": round(max(max_values), 2),
                        "latest_period": sensor_data[-1].get("time_period", "unknown") if sensor_data else "unknown",
                        "latest_average": round(sensor_data[-1].get("avg_value", 0), 2) if sensor_data else 0
                    }
                    
                    # Add individual period metrics for this sensor type
                    for i, period in enumerate(sensor_data):
                        period_key = f"{sensor_type}_period_{i+1}"
                        metrics[period_key] = {
                            "sensor_type": sensor_type,
                            "time_period": period.get("time_period", "unknown"),
                            "average": round(period.get("avg_value", 0), 2),
                            "min": round(period.get("min_value", 0), 2),
                            "max": round(period.get("max_value", 0), 2),
                            "data_points": period.get("data_points", 0)
                        }
            
            # Add overall summary
            metrics["aggregated"] = {
                "sensor_types": list(sensor_groups.keys()),
                "total_sensor_types": len(sensor_groups),
                "total_data_points": total_data_points,
                "total_periods": len(aggregated_data)
            }
            
            logger.info(f" Extracted aggregated metrics: {len(sensor_groups)} sensor types, {len(aggregated_data)} periods, {total_data_points} total data points")
            return metrics
            
        except Exception as e:
            logger.error(f"Aggregated metrics extraction error: {str(e)}")
            return {}
    
    def _translate_response_to_persian(self, structured_result: Dict[str, Any]) -> Dict[str, Any]:
        """Translate English response back to Persian using LLM"""
        try:
            # Translate the summary using LLM translator
            english_summary = structured_result.get("summary", "")
            if english_summary:
                persian_summary = self.translator.translate_response_to_persian(english_summary)
                structured_result["summary"] = persian_summary
                structured_result["original_summary"] = english_summary  # Keep original for debugging
            
            # Translate the output as well
            english_output = structured_result.get("output", "")
            if english_output:
                persian_output = self.translator.translate_response_to_persian(english_output)
                structured_result["output"] = persian_output
                structured_result["original_output"] = english_output  # Keep original for debugging
            
            structured_result["language"] = "fa"
            return structured_result
            
        except Exception as e:
            logger.error(f" Response Translation Error: {str(e)}")
            return structured_result
    
    def _generate_llm_response(self, original_query: str, translated_query: str, language: str, live_data: List[Dict[str, Any]], feature_context: str) -> Dict[str, Any]:
        """Generate intelligent response using LLM with full context"""
        try:
            # Prepare comprehensive context
            context = f"""
You are an expert agricultural AI assistant. Provide concise, helpful responses.

RESPONSE STRUCTURE:
1. **Brief Summary** - 2 sentences maximum about the current situation
2. **Clean Data Section** - Show the actual data in a readable format

GUIDELINES:
- Keep it short and to the point (2 sentences max)
- Give quick insights about what the data shows
- If user speaks Persian, reply in Persian; if English, reply in English
- Use EXACT time range from the data provided below
- NEVER use generic labels like "Last Hour", "Last 6 Hours", "Last 24 Hours", "Last Week"
- NEVER use Persian generic labels like "آخرین ساعت", "آخرین ۶ ساعت", "آخرین ۲۴ ساعت", "آخرین هفته"

FOR THE DATA SECTION, use this format:
```
📊 Sensor Data by Time Range:
• Sensor Name: Avg: X.X, Min: X.X, Max: X.X (EXACT TIME RANGE FROM DATA)
• Sensor Name: Avg: X.X, Min: X.X, Max: X.X (EXACT TIME RANGE FROM DATA)
• Sensor Name: Avg: X.X, Min: X.X, Max: X.X (EXACT TIME RANGE FROM DATA)
• Sensor Name: Avg: X.X, Min: X.X, Max: X.X (EXACT TIME RANGE FROM DATA)
```

CRITICAL INSTRUCTION: Copy the EXACT time labels from the data provided below. DO NOT create your own time range labels!

FOR THE ANALYSIS SECTION, use this format:
```
🔍 Analysis:
• Trend: [Describe the trend - increasing, decreasing, stable]
• Pattern: [Identify any patterns in the data]
• Significance: [What this means for the farm]
• Alert Level: [Low/Medium/High based on the data]
```

FOR THE RECOMMENDATIONS SECTION, use this format:
```
💡 Recommendations:
• Immediate Actions: [What to do right now]
• Monitoring: [What to watch for]
• Long-term: [Strategic advice for the future]
• Resources: [Any tools or methods to use]
```

IMPORTANT: Use the actual data values provided below. Be specific and helpful.

USER QUERY: {original_query}
LIVE DATA: {json.dumps(live_data[:3], indent=1, ensure_ascii=False)}
FEATURE: {feature_context}

Provide an intelligent, helpful response with a clean data section using the actual values above.
"""

            # Log the context being sent to LLM
            logger.info(f"🤖 LLM Context Length: {len(context)} characters")
            logger.info(f" Live Data Points: {len(live_data)}")
            logger.info(f" Language: {language}")
            logger.info(f" Feature Context: {feature_context}")

            # Get LLM response
            if hasattr(self.llm, 'openai_api_key') and self.llm.openai_api_key:
                logger.info(" Using Real LLM (OpenAI)")
                
                # Log LLM call with truncated context
                truncated_context = context[:200] + "..." if len(context) > 200 else context
                logger.info(f"🤖 LLM Call - Live Data Response (Prompt): {truncated_context}")
                
                response = self.llm.invoke(context)
                
                # Log LLM response (truncated)
                response_content = getattr(response, 'content', None) or getattr(response, 'text', '')
                truncated_response = response_content[:100] + "..." if len(response_content) > 100 else response_content
                logger.info(f"🤖 LLM Call - Live Data Response (Response): {truncated_response}")
                response_text = response.content.strip()
                logger.info(f" LLM Response Length: {len(response_text)} characters")
                logger.info(f" FINAL RESPONSE GENERATED: {response_text[:200]}..." if len(response_text) > 200 else f" FINAL RESPONSE: {response_text}")
            else:
                logger.info(" LLM not available - returning factual DB results only")
                # Return factual DB results when LLM is unavailable
                if live_data:
                    response_text = f"# Data Summary\n\n## Available Data Points: {len(live_data)}\n\n## Raw Sensor Data:\n"
                    for i, data_point in enumerate(live_data[:5]):  # Show first 5 data points
                        sensor_type = data_point.get('sensor_type', 'unknown')
                        value = data_point.get('value', data_point.get('avg_value', 'N/A'))
                        timestamp = data_point.get('timestamp', 'N/A')
                        response_text += f"- {sensor_type}: {value} (at {timestamp})\n"
                    if len(live_data) > 5:
                        response_text += f"... and {len(live_data) - 5} more data points\n"
                    response_text += "\n*Note: LLM analysis unavailable. Showing raw data only.*"
                else:
                    response_text = "No data available. LLM service is currently unavailable for analysis."
                logger.info(f" Fallback Response Length: {len(response_text)} characters")
                logger.info(f" FINAL FALLBACK RESPONSE: {response_text[:200]}..." if len(response_text) > 200 else f" FINAL FALLBACK RESPONSE: {response_text}")
            
            return {
                "success": True,
                "query": original_query,
                "response": response_text,
                "language": language,
                "feature_context": feature_context,
                "timestamp": datetime.utcnow().isoformat(),
                "data_points": len(live_data),
                "llm_type": "real" if hasattr(self.llm, 'openai_api_key') and self.llm.openai_api_key else "mock",
                "context_length": len(context)
            }
            
        except Exception as e:
            logger.error(f" Error generating LLM response: {str(e)}")
            return {
                "success": False,
                "error": f"خطا در تولید پاسخ: {str(e)}",
                "query": original_query
            }
    
    
    def get_sample_queries(self) -> Dict[str, List[str]]:
        """Get sample queries for each entity"""
        return {
            "irrigation": [
                "وضعیت آبیاری امروز چطوره؟",
                "آبیاری امروز کمه یا نه؟",
                "مصرف آب چقدر است؟",
                "رطوبت خاک چگونه است؟"
            ],
            "environment": [
                "دمای گلخانه چقدر است؟",
                "رطوبت هوا چگونه است؟",
                "وضعیت محیط چطوره؟",
                "تهویه گلخانه چطوره؟"
            ],
            "pest": [
                "وضعیت آفات چطوره؟",
                "آفات امروز چه هستند؟",
                "خطر بیماری چقدر است؟",
                "توصیه‌های آفت‌کشی چیست؟"
            ],
            "general": [
                "وضعیت کلی مزرعه چطوره؟",
                "آخرین قرائت‌ها چه هستند؟",
                "آمار کلی سنسورها را نشان دهید"
            ]
        }
    
    def get_ontology(self) -> Dict[str, Any]:
        """Get the complete ontology"""
        return self.ontology
    
    def _process_alert_query(self, query: str, session_id: str, detected_lang: str) -> Dict[str, Any]:
        """Process alert management queries"""
        try:
            from app.services.alert_manager import AlertManager
            
            alert_manager = AlertManager()
            query_lower = query.lower()
            
            # Handle different alert commands (English and Persian)
            create_commands = [
                # Basic alert commands
                "create", "alert me", "set alert", "add alert", "make alert", "new alert",
                # Send/notify commands
                "send an alert", "send alert", "send me an alert", "send me alert",
                "notify me", "notify", "notify when", "notify if",
                "warn me", "warn", "warn when", "warn if",
                "alert when", "alert if", "alert on",
                # Message/communication commands
                "message me", "message when", "message if",
                "tell me", "tell me when", "tell me if",
                "inform me", "inform when", "inform if",
                "let me know", "let me know when", "let me know if",
                # Action-based commands
                "remind me", "remind when", "remind if",
                "ping me", "ping when", "ping if",
                "buzz me", "buzz when", "buzz if",
                # Threshold/condition commands
                "when", "if", "whenever", "once", "as soon as",
                # Direct action commands
                "alert", "alerts", "alerting", "alerted",
                "notification", "notifications", "notify", "notifying",
                "warning", "warnings", "warn", "warning me"
            ]
            
            if any(cmd in query_lower for cmd in create_commands):
                # Create new alert
                result = alert_manager.create_alert_from_natural_language(query, session_id)
                
                if result["success"]:
                    if detected_lang == 'fa':
                        # Persian response
                        sensor_name = self._get_persian_sensor_name(result['sensor_type'])
                        condition_name = self._get_persian_condition_name(result['condition'])
                        
                        response_text = f"✅ هشدار با موفقیت ایجاد شد!\n\n"
                        response_text += f"**جزئیات هشدار:**\n"
                        response_text += f"- **سنسور**: {sensor_name}\n"
                        response_text += f"- **شرط**: {condition_name} {result['threshold']}\n"
                        response_text += f"- **وضعیت**: فعال\n\n"
                        response_text += f"**معنی این هشدار:**\n"
                        response_text += f"هر زمان که {sensor_name} {condition_name} {result['threshold']} باشد، به شما اطلاع داده می‌شود\n\n"
                        response_text += f"**مراحل بعدی:**\n"
                        response_text += f"- 'هشدارهای من را نشان بده' برای دیدن همه هشدارها\n"
                        response_text += f"- 'هشدار {sensor_name} را حذف کن' برای حذف این هشدار\n"
                        response_text += f"- 'زمانی که رطوبت < 40% است به من هشدار بده' برای ایجاد هشدار جدید"
                    else:
                        # English response
                        response_text = f"✅ Alert created successfully!\n\n"
                        response_text += f"**Alert Details:**\n"
                        response_text += f"- **Sensor**: {result['sensor_type'].replace('_', ' ').title()}\n"
                        response_text += f"- **Condition**: {result['condition']} {result['threshold']}\n"
                        response_text += f"- **Status**: Active\n\n"
                        response_text += f"**What this means:**\n"
                        response_text += f"You'll be notified whenever {result['sensor_type']} {result['condition']} {result['threshold']}\n\n"
                        response_text += f"**Next steps:**\n"
                        response_text += f"- Say 'Show my alerts' to see all your alerts\n"
                        response_text += f"- Say 'Delete {result['sensor_type']} alert' to remove this alert\n"
                        response_text += f"- Say 'Alert me when humidity < 40%' to create another alert"
                else:
                    if detected_lang == 'fa':
                        response_text = f"❌ ایجاد هشدار ناموفق: {result.get('error', 'خطای نامشخص')}\n\n"
                        response_text += f"**مثال‌های صحیح:**\n"
                        response_text += f"- 'زمانی که دما > 25°C است به من هشدار بده'\n"
                        response_text += f"- 'زمانی که رطوبت < 40% است به من هشدار بده'\n"
                        response_text += f"- 'زمانی که رطوبت خاک > 60% است به من هشدار بده'"
                    else:
                        response_text = f"❌ Failed to create alert: {result.get('error', 'Unknown error')}\n\n"
                        response_text += f"**Try these examples:**\n"
                        response_text += f"- 'Alert me when temperature > 25°C'\n"
                        response_text += f"- 'Alert me when humidity < 40%'\n"
                        response_text += f"- 'Alert me when soil moisture > 60%'"
                
                return {
                    "success": True,
                    "type": "alert_management",
                    "response": response_text,
                    "alert_data": result if result["success"] else None
                }
            
            elif any(cmd in query_lower for cmd in ["show", "list", "my alerts", "alerts"]):
                # Show existing alerts
                alerts = alert_manager.get_user_alerts(session_id)
                
                if not alerts:
                    response_text = "You don't have any alerts set up yet.\n\n"
                    response_text += "Create your first alert:\n"
                    response_text += "• 'Alert me when temperature > 25°C'\n"
                    response_text += "• 'Alert me when humidity < 40%'\n"
                    response_text += "• 'Alert me when soil moisture > 60%'"
                else:
                    response_text = f"Your Alerts ({len(alerts)} total):\n\n"
                    
                    for i, alert in enumerate(alerts, 1):
                        status = "🟢 Active" if alert["is_active"] else "🔴 Inactive"
                        response_text += f"{i}. {alert['alert_name']} {status}\n"
                        response_text += f"   • {alert['sensor_type'].replace('_', ' ').title()} {alert['condition_type']} {alert['threshold_value']}\n"
                        response_text += f"   • Created: {alert['created_at'][:10]}\n\n"
                    
                    response_text += "Commands:\n"
                    response_text += "• 'Delete [sensor] alert' to remove an alert\n"
                    response_text += "• 'Alert me when...' to create new alerts"
                
                return {
                    "success": True,
                    "type": "alert_management",
                    "response": response_text,
                    "alerts": alerts
                }
            
            elif any(cmd in query_lower for cmd in ["delete", "remove", "cancel"]):
                # Delete alert
                # Extract sensor type from query
                sensor_types = ["temperature", "humidity", "pressure", "light", "motion", "soil_moisture", "co2_level", "ph"]
                sensor_to_delete = None
                
                for sensor in sensor_types:
                    if sensor.replace("_", " ") in query_lower or sensor in query_lower:
                        sensor_to_delete = sensor
                        break
                
                if sensor_to_delete:
                    # Find and delete the alert
                    alerts = alert_manager.get_user_alerts(session_id)
                    alert_to_delete = None
                    
                    for alert in alerts:
                        if alert["sensor_type"] == sensor_to_delete:
                            alert_to_delete = alert
                            break
                    
                    if alert_to_delete:
                        success = alert_manager.delete_alert(alert_to_delete["id"], session_id)
                        if success:
                            response_text = f"✅ Deleted {alert_to_delete['alert_name']} successfully!"
                        else:
                            response_text = f"❌ Failed to delete {alert_to_delete['alert_name']}"
                    else:
                        response_text = f"❌ No {sensor_to_delete.replace('_', ' ')} alert found to delete"
                else:
                    response_text = "❌ Please specify which alert to delete (e.g., 'Delete temperature alert')"
                
                return {
                    "success": True,
                    "type": "alert_management",
                    "response": response_text
                }
            
            else:
                # Unknown alert command
                response_text = "🤔 I didn't understand that alert command.\n\n"
                response_text += "**Available commands:**\n"
                response_text += "- 'Alert me when temperature > 25°C' - Create new alert\n"
                response_text += "- 'Show my alerts' - List all alerts\n"
                response_text += "- 'Delete temperature alert' - Remove an alert\n\n"
                response_text += "**Examples:**\n"
                response_text += "- 'Alert me when humidity < 40%'\n"
                response_text += "- 'Alert me when soil moisture > 60%'\n"
                response_text += "- 'Alert me when pressure > 1000'"
                
                return {
                    "success": True,
                    "type": "alert_management",
                    "response": response_text
                }
                
        except Exception as e:
            logger.error(f"❌ Error processing alert query: {e}")
            return {
                "success": False,
                "type": "alert_management",
                "response": f"❌ Error processing alert command: {str(e)}"
            }

    def _get_persian_sensor_name(self, sensor_type: str) -> str:
        """Get Persian name for sensor type"""
        persian_names = {
            "temperature": "دما",
            "humidity": "رطوبت",
            "pressure": "فشار",
            "light": "نور",
            "motion": "حرکت",
            "soil_moisture": "رطوبت خاک",
            "co2_level": "سطح CO2",
            "ph": "پی اچ"
        }
        return persian_names.get(sensor_type, sensor_type)
    
    def _get_persian_condition_name(self, condition: str) -> str:
        """Get Persian name for condition type"""
        persian_names = {
            "above": "بیشتر از",
            "below": "کمتر از",
            "equals": "برابر با",
            "greater_equal": "بیشتر یا مساوی",
            "less_equal": "کمتر یا مساوی"
        }
        return persian_names.get(condition, condition)
    
    def _get_persian_severity_name(self, severity: str) -> str:
        """Get Persian name for severity level"""
        severity_map = {
            "info": "اطلاعی",
            "warning": "هشدار", 
            "critical": "بحرانی"
        }
        return severity_map.get(severity, severity)
    
    def _detect_enhanced_alert_intent(self, query: str, detected_lang: str) -> str:
        """Detect enhanced alert intent with ontology support"""
        query_lower = query.lower()
        
        # Enhanced create commands with severity and action support
        create_commands = [
            "create", "alert me", "set alert", "add alert", "make alert", "new alert",
            "send an alert", "send alert", "notify me", "notify", "warn me", "warn",
            "critical alert", "urgent alert", "emergency alert", "بحرانی", "فوری",
            "auto alert", "automatic alert", "خودکار", "اتوماتیک"
        ]
        
        if any(cmd in query_lower for cmd in create_commands):
            return "create"
        elif any(cmd in query_lower for cmd in ["show", "list", "my alerts", "alerts"]):
            return "list"
        elif any(cmd in query_lower for cmd in ["delete", "remove", "cancel"]):
            return "delete"
        else:
            return "unknown"

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the service"""
        try:
            # Test basic functionality
            test_result = self.process_query("test query")
            
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "llm_available": hasattr(self.llm, 'openai_api_key'),
                "ontology_entities": len(self.ontology["entities"]),
                "test_query_success": test_result["success"]
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
