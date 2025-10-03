from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

from app.services.ai_assistant import AIAssistant

logger = logging.getLogger(__name__)

# Initialize AI Assistant
ai_assistant = AIAssistant()

# Pydantic models
class FeatureQueryRequest(BaseModel):
    """Schema for feature-specific queries"""
    feature: str = Field(..., description="Feature context (irrigation, environment, pest, dashboard)")
    query: str = Field(..., min_length=1, description="Natural language query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature": "irrigation",
                "query": "وضعیت آبیاری فعلی چیست؟"
            }
        }

class FeatureQueryResponse(BaseModel):
    """Schema for feature query responses"""
    success: bool
    answer: Optional[str] = None
    feature: Optional[str] = None
    entity: Optional[str] = None
    chart: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "وضعیت آبیاری فعلی مطلوب است",
                "feature": "irrigation",
                "entity": "Smart Irrigation Management",
                "chart": None,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

# Create router
router = APIRouter()

@router.post("/ai/feature-query", response_model=FeatureQueryResponse)
async def feature_query(request: FeatureQueryRequest):
    """
    Feature-aware AI Assistant query endpoint
    
    This endpoint processes natural language queries with feature context
    and returns intelligent responses in Persian.
    """
    try:
        logger.info(f"🔍 AI Assistant: Processing {request.feature} query: '{request.query}'")
        
        result = ai_assistant.process_query(request.feature, request.query)
        
        if result["success"]:
            logger.info(f"✅ AI Assistant: Query processed successfully")
            return FeatureQueryResponse(**result)
        else:
            logger.error(f"❌ AI Assistant: Query failed - {result.get('error', 'Unknown error')}")
            return FeatureQueryResponse(
                success=False,
                error=result.get("error", "Unknown error"),
                feature=request.feature
            )
            
    except Exception as e:
        logger.error(f"❌ AI Assistant Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing feature query: {str(e)}"
        )

@router.get("/ai/features")
async def get_available_features():
    """Get list of available features"""
    try:
        features = ai_assistant.get_available_features()
        return features
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        raise HTTPException(status_code=500, detail="Failed to get features")

@router.get("/ai/features/{feature}")
async def get_feature_info(feature: str):
    """Get information about a specific feature"""
    try:
        info = ai_assistant.get_feature_info(feature)
        if not info:
            raise HTTPException(status_code=404, detail="Feature not found")
        return info
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feature info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feature info")

@router.get("/ai/features/{feature}/sample-queries")
async def get_feature_sample_queries(feature: str):
    """Get sample queries for a specific feature"""
    try:
        queries = ai_assistant.get_sample_queries(feature)
        return queries
    except Exception as e:
        logger.error(f"Error getting sample queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample queries")

@router.get("/ai/health")
async def ai_assistant_health():
    """Health check for AI Assistant"""
    try:
        # Test basic functionality
        test_result = ai_assistant.process_query("dashboard", "test query")
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "llm_available": hasattr(ai_assistant.llm, 'openai_api_key'),
            "features_available": len(ai_assistant.get_available_features()),
            "test_query_success": test_result["success"]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
