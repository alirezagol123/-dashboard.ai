from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class SensorDataCreate(BaseModel):
    """Schema for creating sensor data"""
    sensor_type: str = Field(..., min_length=1, max_length=50, description="Type of sensor (e.g., temperature, humidity)")
    value: float = Field(..., description="Sensor reading value")
    
    class Config:
        json_schema_extra = {
            "example": {
                "sensor_type": "temperature",
                "value": 25.5
            }
        }

class SensorDataResponse(BaseModel):
    """Schema for sensor data response"""
    id: int
    timestamp: datetime
    sensor_type: str
    value: float
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "timestamp": "2024-01-15T10:30:00Z",
                "sensor_type": "temperature",
                "value": 25.5
            }
        }

class StatsResponse(BaseModel):
    """Schema for statistical data response"""
    count: int
    average: float
    min_value: float
    max_value: float
    latest_timestamp: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "count": 100,
                "average": 24.8,
                "min_value": 18.2,
                "max_value": 32.1,
                "latest_timestamp": "2024-01-15T10:30:00Z"
            }
        }

class WebSocketMessage(BaseModel):
    """Schema for WebSocket messages"""
    timestamp: str
    sensor_type: str
    value: float
    id: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-15T10:30:00Z",
                "sensor_type": "temperature",
                "value": 25.5,
                "id": 1
            }
        }

class AnalysisRequest(BaseModel):
    """Schema for LangChain analysis requests"""
    query: str = Field(..., min_length=1, description="Natural language query about the data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the trends in temperature over time?"
            }
        }

class AnalysisResponse(BaseModel):
    """Schema for LangChain analysis responses"""
    success: bool
    response: Optional[str] = None
    error: Optional[str] = None
    timestamp: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "response": "The temperature shows an upward trend over the past 24 hours...",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

class VisualizationRequest(BaseModel):
    """Schema for visualization requests"""
    chart_type: str = Field(..., description="Type of chart (line, bar, scatter, histogram)")
    columns: list[str] = Field(..., min_items=1, max_items=2, description="Columns to visualize")
    
    class Config:
        json_schema_extra = {
            "example": {
                "chart_type": "line",
                "columns": ["timestamp", "temperature"]
            }
        }

class VisualizationResponse(BaseModel):
    """Schema for visualization responses"""
    success: bool
    chart: Optional[str] = None
    chart_type: Optional[str] = None
    columns: Optional[list[str]] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "chart": "{'data': [...], 'layout': {...}}",
                "chart_type": "line",
                "columns": ["timestamp", "temperature"]
            }
        }
