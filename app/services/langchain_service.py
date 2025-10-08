import os
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any, Optional, ClassVar
import logging
from datetime import datetime
import json
import base64
import io

# LangChain imports
from langchain_community.llms import OpenAI
from langchain.agents import initialize_agent, Tool, AgentType
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.tools import BaseTool, tool
from langchain.schema import AgentAction, AgentFinish
from langchain.callbacks.manager import CallbackManagerForToolRun
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain_experimental.tools import PythonREPLTool
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

class DataAnalysisTool(BaseTool):
    """Tool for analyzing data using pandas operations"""
    
    name: str = "data_analysis"
    description: str = "Analyze data using pandas operations. Input should be a pandas operation string."
    
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Execute pandas operations safely
            result = eval(f"self.df.{query}")
            return str(result)
        except Exception as e:
            return f"Error in data analysis: {str(e)}"

class VisualizationTool(BaseTool):
    """Tool for creating visualizations"""
    
    name: str = "create_visualization"
    description: str = "Create visualizations (line, bar, scatter, histogram). Input format: 'chart_type:column1,column2'"
    
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self.df = df
        self.chart_count = 0
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            self.chart_count += 1
            chart_type, columns = query.split(':')
            columns = [col.strip() for col in columns.split(',')]
            
            # Create visualization based on type
            if chart_type.lower() == 'line':
                fig = px.line(self.df, x=columns[0], y=columns[1], title=f"Line Chart: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'bar':
                fig = px.bar(self.df, x=columns[0], y=columns[1], title=f"Bar Chart: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'scatter':
                fig = px.scatter(self.df, x=columns[0], y=columns[1], title=f"Scatter Plot: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'histogram':
                fig = px.histogram(self.df, x=columns[0], title=f"Histogram: {columns[0]}")
            else:
                return "Unsupported chart type. Use: line, bar, scatter, histogram"
            
            # Convert to base64 for web display
            chart_html = fig.to_html(include_plotlyjs='cdn')
            return f"Visualization created: {chart_type} chart"
            
        except Exception as e:
            return f"Error creating visualization: {str(e)}"

class DataInsightTool(BaseTool):
    """Tool for generating data insights using LLM"""
    
    name: str = "data_insights"
    description: str = "Generate insights about the data using natural language analysis"
    
    def __init__(self, df: pd.DataFrame, llm):
        super().__init__()
        self.df = df
        self.llm = llm
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            # Get basic data info
            data_info = f"""
            Dataset shape: {self.df.shape}
            Columns: {list(self.df.columns)}
            Data types: {self.df.dtypes.to_dict()}
            Sample data: {self.df.head().to_string()}
            """
            
            # Create prompt for LLM
            prompt = f"""
            Based on the following dataset information:
            {data_info}
            
            User question: {query}
            
            Please provide a detailed analysis and insights about the data.
            """
            
            response = self.llm(prompt)
            return response
            
        except Exception as e:
            return f"Error generating insights: {str(e)}"

class MockLLM:
    """Mock LLM for testing without OpenAI API"""
    
    def __call__(self, prompt: str) -> str:
        return f"Mock LLM response to: {prompt[:100]}..."

class LangChainService:
    """Service for LangChain-based data analysis with orchestrator pattern"""

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

        self.df = None
        self.agent = None
        self.memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True, output_key="output")
        self.sql_db = None
        self.sql_toolkit = None
        self.python_tool = None
        
    def setup_database_connection(self):
        """Setup SQL database connection for SQLDatabaseChain"""
        try:
            # Use SQLite database file
            db_path = "sensor_data.db"
            if os.path.exists(db_path):
                # Create SQLAlchemy engine
                engine = create_engine(f"sqlite:///{db_path}")
                self.sql_db = SQLDatabase(engine)
                self.sql_toolkit = SQLDatabaseToolkit(db=self.sql_db, llm=self.llm)
                logger.info("SQL database connection established")
            else:
                logger.warning("Database file not found, SQL tools will not be available")
        except Exception as e:
            logger.error(f"Error setting up database connection: {str(e)}")
            
    def load_data_from_db(self, db_data: List[Dict]) -> bool:
        """Load data from database records"""
        try:
            if not db_data:
                logger.error("No data provided")
                return False
            
            # Convert to DataFrame
            self.df = pd.DataFrame(db_data)
            
            # Convert timestamp to datetime if it exists
            if 'timestamp' in self.df.columns:
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
            
            logger.info(f"Data loaded successfully. Shape: {self.df.shape}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
    
    def create_agent(self):
        """Create LangChain agent with tools"""
        if self.df is None:
            raise ValueError("No data loaded. Please load data first.")
        
        try:
            # Create tools using @tool decorator
            @tool
            def data_analysis(query: str) -> str:
                """Analyze data using pandas operations. Input should be a pandas operation string."""
                try:
                    result = eval(f"self.df.{query}")
                    return str(result)
                except Exception as e:
                    return f"Error in data analysis: {str(e)}"
            
            @tool
            def create_visualization(query: str) -> str:
                """Create visualizations (line, bar, scatter, histogram). Input format: 'chart_type:column1,column2'"""
                try:
                    chart_type, columns = query.split(':')
                    columns = [col.strip() for col in columns.split(',')]
                    
                    if chart_type.lower() == 'line':
                        fig = px.line(self.df, x=columns[0], y=columns[1], title=f"Line Chart: {columns[0]} vs {columns[1]}")
                    elif chart_type.lower() == 'bar':
                        fig = px.bar(self.df, x=columns[0], y=columns[1], title=f"Bar Chart: {columns[0]} vs {columns[1]}")
                    elif chart_type.lower() == 'scatter':
                        fig = px.scatter(self.df, x=columns[0], y=columns[1], title=f"Scatter Plot: {columns[0]} vs {columns[1]}")
                    elif chart_type.lower() == 'histogram':
                        fig = px.histogram(self.df, x=columns[0], title=f"Histogram: {columns[0]}")
                    else:
                        return "Unsupported chart type. Use: line, bar, scatter, histogram"
                    
                    return f"Visualization created: {chart_type} chart"
                except Exception as e:
                    return f"Error creating visualization: {str(e)}"
            
            @tool
            def data_insights(query: str) -> str:
                """Generate insights about the data using natural language analysis"""
                try:
                    # Get basic statistics
                    numeric_cols = self.df.select_dtypes(include=['number']).columns
                    stats_info = ""
                    if len(numeric_cols) > 0:
                        stats_info = f"\nStatistical Summary:\n{self.df[numeric_cols].describe().to_string()}"
                    
                    # Get data info
                    data_info = f"""
                    Dataset Overview:
                    - Shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns
                    - Columns: {list(self.df.columns)}
                    - Data types: {dict(self.df.dtypes)}
                    - Missing values: {self.df.isnull().sum().to_dict()}
                    
                    Sample Data (first 5 rows):
                    {self.df.head().to_string()}
                    {stats_info}
                    """
                    
                    prompt = f"""
                    You are analyzing sensor data. Here's the dataset information:
                    {data_info}
                    
                    User question: {query}
                    
                    Please provide a detailed analysis and insights about this sensor data. Focus on:
                    1. Data patterns and trends
                    2. Statistical insights
                    3. Any anomalies or interesting observations
                    4. Practical implications of the data
                    
                    Be specific and reference actual values from the data when possible.
                    """
                    
                    response = self.llm.invoke(prompt)
                    return response.content if hasattr(response, 'content') else str(response)
                except Exception as e:
                    return f"Error generating insights: {str(e)}"
            
            # Create agent with better system prompt
            tools = [data_analysis, create_visualization, data_insights]
            
            # Create a more direct approach - use the data_insights tool directly
            # Instead of complex agent, let's create a simpler approach that always uses data_insights
            
            # Create a custom prompt template that includes the data
            data_context = f"""
            You are analyzing sensor data with the following comprehensive information:
            
            Dataset Overview:
            - Shape: {self.df.shape[0]} rows, {self.df.shape[1]} columns
            - Columns: {list(self.df.columns)}
            - Data types: {dict(self.df.dtypes)}
            - Missing values: {self.df.isnull().sum().to_dict()}
            
            Sample Data (first 10 rows):
            {self.df.head(10).to_string()}
            
            Latest Data (last 5 rows):
            {self.df.tail(5).to_string()}
            
            Statistical Summary:
            {self.df.describe().to_string() if len(self.df.select_dtypes(include=['number']).columns) > 0 else 'No numeric columns'}
            
            Sensor Types and Counts:
            {self.df['sensor_type'].value_counts().to_string() if 'sensor_type' in self.df.columns else 'No sensor_type column'}
            
            Value Ranges by Sensor Type:
            {self.df.groupby('sensor_type')['value'].agg(['min', 'max', 'mean', 'count']).to_string() if 'sensor_type' in self.df.columns and 'value' in self.df.columns else 'No sensor_type or value columns'}
            
            Please analyze this data and provide insights based on the user's question.
            """
            
            # Store the data context for use in analysis
            self.data_context = data_context
            
            # Create a simple agent that will use data_insights tool
            self.agent = initialize_agent(
                tools=tools,
                llm=self.llm,
                agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
                memory=self.memory,
                verbose=False,  # Reduce verbosity
                handle_parsing_errors=True,
                max_iterations=3,
                early_stopping_method="generate"
            )
            
            logger.info("LangChain agent created successfully")
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            raise
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """Analyze data based on user query"""
        try:
            if self.df is None:
                return {
                    "success": False,
                    "error": "No data loaded",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # For mock LLM, provide a simple response
            if isinstance(self.llm, MockLLM):
                return {
                    "success": True,
                    "response": f"Mock analysis for query: '{query}'. Data shape: {self.df.shape}. This is a mock response - add your OpenAI API key for real analysis.",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Create comprehensive data context automatically
            data_context = self._create_data_context()
            
            # Create a comprehensive prompt that includes all the data context
            full_prompt = f"""
            {data_context}
            
            سوال کاربر: {query}
            
            شما یک تحلیلگر داده هوشمند هستید که باید به زبان فارسی پاسخ دهید. لطفاً تحلیل دقیق و ساختاریافته از داده‌های سنسور ارائه دهید.
            
            الزامات پاسخ:
            1. حتماً به زبان فارسی پاسخ دهید
            2. پاسخ را با بولت پوینت ساختاریافته ارائه دهید
            3. فقط بر اساس داده‌های واقعی موجود تحلیل کنید
            4. مقادیر دقیق و آمار را ذکر کنید
            5. الگوها و روندها را شناسایی کنید
            6. نتیجه‌گیری عملی ارائه دهید
            
            فرمت پاسخ مورد نظر:
            پاسخ طبیعی و دوستانه ارائه دهید که شامل:
            1. پاسخ طبیعی و گفتگویی درباره داده‌ها
            2. بخش داده‌های ساختاریافته با فرمت:
            ```
            📊 داده‌های سنسور بر اساس بازه زمانی:
            • نام سنسور: میانگین: X.X، حداقل: X.X، حداکثر: X.X (آخرین ساعت)
            • نام سنسور: میانگین: X.X، حداقل: X.X، حداکثر: X.X (آخرین 6 ساعت)
            • نام سنسور: میانگین: X.X، حداقل: X.X، حداکثر: X.X (آخرین 24 ساعت)
            • نام سنسور: میانگین: X.X، حداقل: X.X، حداکثر: X.X (آخرین هفته)
            ```
            3. بخش تحلیل با فرمت:
            ```
            🔍 تحلیل:
            • روند: [توصیف روند - افزایش، کاهش، ثابت]
            • الگو: [شناسایی الگوهای موجود در داده‌ها]
            • اهمیت: [این داده‌ها برای مزرعه چه معنایی دارد]
            • سطح هشدار: [پایین/متوسط/بالا بر اساس داده‌ها]
            ```
            4. بخش توصیه‌ها با فرمت:
            ```
            💡 توصیه‌ها:
            • اقدامات فوری: [چه کاری باید همین الان انجام داد]
            • نظارت: [چه چیزی را باید زیر نظر داشت]
            • بلندمدت: [توصیه‌های استراتژیک برای آینده]
            • منابع: [ابزارها یا روش‌های قابل استفاده]
            ```
            
            فقط بر اساس داده‌های موجود تحلیل کنید و مقادیر دقیق را ذکر کنید.
            """
            
            # Use the LLM directly with the comprehensive prompt
            response = self.llm.invoke(full_prompt)
            
            # Extract the response content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
            
            return {
                "success": True,
                "response": response_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in analysis: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _create_data_context(self) -> str:
        """Create comprehensive data context as JSON for AI analysis"""
        try:
            if self.df is None:
                return "No data available for analysis."
            
            # Convert DataFrame to JSON for comprehensive context
            data_json = self.df.to_json(orient='records', date_format='iso')
            
            # Get comprehensive statistics
            numeric_cols = self.df.select_dtypes(include=['number']).columns
            stats_summary = {}
            if len(numeric_cols) > 0:
                stats_summary = self.df[numeric_cols].describe().to_dict()
            
            # Get sensor-specific analysis
            sensor_analysis = {}
            if 'sensor_type' in self.df.columns and 'value' in self.df.columns:
                sensor_analysis = self.df.groupby('sensor_type')['value'].agg([
                    'count', 'min', 'max', 'mean', 'std'
                ]).to_dict()
            
            # Get latest readings
            latest_readings = self.df.tail(10).to_dict('records') if len(self.df) > 0 else []
            
            # Create comprehensive context
            context = f"""
            CONTEXT تحلیل داده‌های سنسور:
            
            نمای کلی مجموعه داده:
            - تعداد کل رکوردها: {len(self.df)}
            - ستون‌ها: {list(self.df.columns)}
            - انواع داده: {dict(self.df.dtypes)}
            - مقادیر گمشده: {self.df.isnull().sum().to_dict()}
            
            خلاصه آماری:
            {stats_summary}
            
            تحلیل سنسور بر اساس نوع:
            {sensor_analysis}
            
            آخرین 10 قرائت (JSON):
            {latest_readings}
            
            نمونه کامل مجموعه داده (20 رکورد اول):
            {self.df.head(20).to_dict('records')}
            
            این داده‌ها نشان‌دهنده قرائت‌های سنسور در زمان واقعی هستند. لطفاً این مجموعه داده جامع را تحلیل کنید تا به سوالات کاربر با بینش‌های خاص، آمار و الگوها پاسخ دهید.
            """
            
            return context
            
        except Exception as e:
            logger.error(f"Error creating data context: {str(e)}")
            return f"Error creating data context: {str(e)}"
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of loaded data"""
        if self.df is None:
            return {"error": "No data loaded"}
        
        try:
            # Convert numpy dtypes to strings for JSON serialization
            dtypes_dict = {col: str(dtype) for col, dtype in self.df.dtypes.items()}
            
            # Convert numpy statistics to regular Python types
            stats_dict = {}
            for col, stats in self.df.describe().items():
                stats_dict[col] = {stat: float(val) if not pd.isna(val) else None 
                                for stat, val in stats.items()}
            
            summary = {
                "shape": list(self.df.shape),  # Convert tuple to list
                "columns": list(self.df.columns),
                "dtypes": dtypes_dict,
                "sample": self.df.head().to_dict('records'),
                "statistics": stats_dict
            }
            return summary
        except Exception as e:
            return {"error": str(e)}
    
    def create_visualization(self, chart_type: str, columns: List[str]) -> Dict[str, Any]:
        """Create a specific visualization"""
        if self.df is None:
            return {"error": "No data loaded"}
        
        try:
            if chart_type.lower() == 'line':
                fig = px.line(self.df, x=columns[0], y=columns[1], title=f"Line Chart: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'bar':
                fig = px.bar(self.df, x=columns[0], y=columns[1], title=f"Bar Chart: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'scatter':
                fig = px.scatter(self.df, x=columns[0], y=columns[1], title=f"Scatter Plot: {columns[0]} vs {columns[1]}")
            elif chart_type.lower() == 'histogram':
                fig = px.histogram(self.df, x=columns[0], title=f"Histogram: {columns[0]}")
            else:
                return {"error": "Unsupported chart type"}
            
            # Convert to JSON for frontend
            chart_json = fig.to_json()
            return {
                "success": True,
                "chart": chart_json,
                "chart_type": chart_type,
                "columns": columns
            }
            
        except Exception as e:
            return {"error": str(e)}
