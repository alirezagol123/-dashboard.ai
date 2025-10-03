import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy import create_engine

# LangChain imports
from langchain.agents import initialize_agent, AgentType
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class MockLLM:
    """Mock LLM for testing without OpenAI API"""
    
    def invoke(self, prompt: str) -> str:
        return f"Mock LLM response to: {prompt[:100]}..."

class LangChainOrchestrator:
    """LangChain Orchestrator Service for AI-powered data analysis"""

    def __init__(self):
        # Initialize LLM with custom API endpoint
        self.api_key = os.getenv('OPENAI_API_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySUQiOiI2ODQ1NzQzNDdkOTQ0NDlhMzc2NDFhNzgiLCJ0eXBlIjoiYXV0aCIsImlhdCI6MTc1ODEzNDY2N30.BdDAu4IF_y2oVZPUyZH41Ap_PZpfjZwRJoR3V8CCsGk')
        self.base_url = os.getenv('OPENAI_BASE_URL', 'https://ai.liara.ir/api/v1/688a24a93d0c49e74e362a7f')
        self.model_name = os.getenv('OPENAI_MODEL', 'openai/gpt-4o-mini')

        if not self.api_key:
            logger.warning("No API key provided. Using mock LLM.")
            self.llm = MockLLM()
        else:
            # Use ChatOpenAI with custom endpoint
            self.llm = ChatOpenAI(
                openai_api_key=self.api_key,
                openai_api_base=self.base_url,
                model_name=self.model_name,
                temperature=0.7
            )
            logger.info(f"Using custom AI API: {self.base_url} with model {self.model_name}")

        self.agent = None
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
        self.sql_db = None
        self.sql_toolkit = None
        self.python_tool = None
        
    def setup_database_connection(self):
        """Setup SQL database connection for SQLDatabaseChain"""
        try:
            # Get database URL from environment (defaults to SQLite)
            database_url = os.getenv("DATABASE_URL", "sqlite:///./smart_dashboard.db")
            
            # Create SQLAlchemy engine
            engine = create_engine(database_url)
            self.sql_db = SQLDatabase(engine)
            self.sql_toolkit = SQLDatabaseToolkit(db=self.sql_db, llm=self.llm)
            logger.info(f"SQL database connection established: {database_url}")
        except Exception as e:
            logger.error(f"Error setting up database connection: {str(e)}")
            
    def create_orchestrator_agent(self):
        """Create LangChain orchestrator agent with SQL and Python tools"""
        try:
            # Setup database connection
            self.setup_database_connection()
            
            # Initialize Python REPL tool
            self.python_tool = PythonREPLTool()
            
            # Prepare tools list
            tools = []
            
            # Add SQL tools if database is available
            if self.sql_toolkit:
                sql_tools = self.sql_toolkit.get_tools()
                tools.extend(sql_tools)
                logger.info(f"Added {len(sql_tools)} SQL tools")
            
            # Add Python REPL tool
            tools.append(self.python_tool)
            logger.info("Added Python REPL tool")
            
            if not tools:
                logger.warning("No tools available, creating basic agent")
                return None
            
            # Create SQL agent with custom tools
            self.agent = create_sql_agent(
                llm=self.llm,
                toolkit=self.sql_toolkit,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=5,
                early_stopping_method="generate",
                agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                system_message="""You are a data analyst AI assistant. You MUST use the available tools to answer questions about sensor data.

IMPORTANT RULES:
1. Always respond in Persian (Farsi)
2. You MUST use the available tools:
   - SQL Database tools: for querying sensor_data table
   - Python REPL: for mathematical calculations and statistics
3. NEVER give generic answers - ALWAYS use tools first
4. Format responses with bullet points in Persian

Response format:
• خلاصه کلی: [brief summary]
• آمار کلیدی: [specific values]
• الگوهای شناسایی شده: [patterns and trends]
• نتیجه‌گیری: [practical conclusions]

Example:
User: "What is the average temperature in the last 24 hours?"
You: Use SQL tool to query temperature data, then Python tool for calculations, then explain results in Persian.

ALWAYS USE TOOLS - NO GENERIC RESPONSES!"""
            )
            
            logger.info("Orchestrator agent created successfully")
            return self.agent
            
        except Exception as e:
            logger.error(f"Error creating orchestrator agent: {str(e)}")
            raise
    
    def query(self, question: str) -> Dict[str, Any]:
        """Process user query using orchestrator agent - matches checklist format"""
        try:
            # Create agent if not exists
            if self.agent is None:
                self.create_orchestrator_agent()
            
            if self.agent is None:
                return {
                    "answer": "Could not create orchestrator agent",
                    "tool_used": "none",
                    "raw_result": "Agent creation failed",
                    "success": False
                }
            
            # For mock LLM, provide a simple response
            if isinstance(self.llm, MockLLM):
                return {
                    "answer": f"Mock analysis for query: '{question}'. This is a mock response - add your OpenAI API key for real analysis.",
                    "tool_used": "mock",
                    "raw_result": "Mock response",
                    "success": True
                }
            
            # Use the orchestrator agent
            response = self.agent.invoke({"input": question})
            
            # Extract the response content
            if hasattr(response, 'output'):
                response_text = response.output
            elif hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            # Determine which tool was used (simplified detection)
            tool_used = "sql_database" if "sql" in str(response).lower() else "python_repl" if "python" in str(response).lower() else "unknown"
            
            return {
                "answer": response_text,
                "tool_used": tool_used,
                "raw_result": str(response),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in orchestrator query: {str(e)}")
            return {
                "answer": f"Error processing query: {str(e)}",
                "tool_used": "error",
                "raw_result": str(e),
                "success": False
            }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of database schema and data"""
        try:
            if self.sql_db is None:
                return {"error": "Database not connected"}
            
            # Get table info
            table_info = self.sql_db.get_table_info()
            
            # Get sample data
            sample_query = "SELECT * FROM sensor_data LIMIT 5"
            sample_data = self.sql_db.run(sample_query)
            
            # Get count
            count_query = "SELECT COUNT(*) as total FROM sensor_data"
            total_count = self.sql_db.run(count_query)
            
            return {
                "table_info": table_info,
                "sample_data": sample_data,
                "total_count": total_count,
                "columns": ["id", "timestamp", "sensor_type", "value"],
                "shape": [total_count, 4] if total_count else [0, 4]
            }
            
        except Exception as e:
            logger.error(f"Error getting data summary: {str(e)}")
            return {"error": str(e)}