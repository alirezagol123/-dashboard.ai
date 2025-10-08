# Force UTF-8 encoding globally (Windows safe fix)
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
import uvicorn
import os
import asyncio
from datetime import datetime
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging with UTF-8 encoding
logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler()],
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

from app.db.database import get_db, engine
from app.models.sensor_data import SensorData
from app.models.schemas import SensorDataCreate, SensorDataResponse, StatsResponse, AnalysisRequest, AnalysisResponse, VisualizationRequest, VisualizationResponse
from app.services.data_service import DataService
from app.services.websocket_manager import WebSocketManager
from app.services.langchain_service import LangChainService
from app.services.intent_router_layer import IntentRouterLayer
from app.services.unified_semantic_service import UnifiedSemanticQueryService
from app.services.ai_assistant import AIAssistant
from app.ai_assistant_api import router as ai_assistant_router

# Create database tables
from app.db.database import Base
Base.metadata.create_all(bind=engine)

# Initialize PostgreSQL database on Liara
if os.getenv("LIARA_APP_ID"):
    try:
        from init_postgresql import init_postgresql_database
        init_postgresql_database()
    except Exception as e:
        logger.warning(f"PostgreSQL initialization failed: {e}")

app = FastAPI(
    title="Smart Data Dashboard API",
    description="Backend API for Smart Data Dashboard MVP",
    version="1.0.0"
)

# CORS middleware - Allow all development origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:5173",  # Vite default port
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize services
data_service = DataService()
websocket_manager = WebSocketManager()
langchain_service = LangChainService()
intent_router_layer = IntentRouterLayer()
# unified_semantic_service will be initialized lazily
ai_assistant = AIAssistant()

def get_unified_semantic_service():
    """Get unified semantic service instance (lazy initialization)"""
    if not hasattr(get_unified_semantic_service, '_instance'):
        get_unified_semantic_service._instance = UnifiedSemanticQueryService()
    return get_unified_semantic_service._instance

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Smart Data Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "websocket": "/ws/data"
    }

@app.post("/data", response_model=SensorDataResponse)
async def create_sensor_data(
    data: SensorDataCreate,
    db: Session = Depends(get_db)
):
    """Create new sensor data entry"""
    try:
        # Create sensor data record
        sensor_record = data_service.create_sensor_data(db, data)
        
        # Broadcast to WebSocket clients
        await websocket_manager.broadcast({
            "timestamp": sensor_record.timestamp.isoformat(),
            "sensor_type": sensor_record.sensor_type,
            "value": sensor_record.value,
            "id": sensor_record.id
        })
        
        return sensor_record
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data/latest", response_model=List[SensorDataResponse])
async def get_latest_data(
    limit: int = 10,
    sensor_type: str = None,
    db: Session = Depends(get_db)
):
    """Get latest sensor data records"""
    try:
        # Debug: Check database session
        print(f"DEBUG: Database session: {db}")
        print(f"DEBUG: Limit: {limit}, Sensor type: {sensor_type}")
        
        # Debug: Check if database has data
        from sqlalchemy import text
        result = db.execute(text("SELECT COUNT(*) FROM sensor_data"))
        count = result.fetchone()[0]
        print(f"DEBUG: Database has {count} records")
        
        # Get data using service
        data = data_service.get_latest_data(db, limit, sensor_type)
        print(f"DEBUG: Service returned {len(data)} records")
        
        return data
    except Exception as e:
        print(f"DEBUG: Error in get_latest_data: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data/stats", response_model=Dict[str, StatsResponse])
async def get_data_stats(db: Session = Depends(get_db)):
    """Get statistical analysis of sensor data"""
    try:
        return data_service.get_data_stats(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/data/types")
async def get_sensor_types(db: Session = Depends(get_db)):
    """Get all available sensor types"""
    try:
        return data_service.get_sensor_types(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.websocket("/ws/data")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data updates"""
    print(f"WebSocket endpoint: New connection attempt from {websocket.client}")
    
    try:
        print("WebSocket endpoint: Attempting to accept connection...")
        await websocket.accept()
        print(f"WebSocket endpoint: Connection accepted successfully")
        
        # Add to WebSocket manager
        websocket_manager.active_connections.append(websocket)
        print(f"WebSocketManager: Added connection. Total: {len(websocket_manager.active_connections)}")
        
        # Send initial welcome message
        try:
            await websocket.send_text("welcome")
            print("WebSocket: Sent welcome message")
        except Exception as welcome_error:
            print(f"WebSocket: Error sending welcome: {welcome_error}")
        
        # Simple message loop
        while True:
            try:
                # Wait for any message from client or timeout
                print("WebSocket: Waiting for message or timeout...")
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                print(f"WebSocket: Received data: {data}")
                
                # Handle ping/pong messages
                if data == "ping":
                    await websocket.send_text("pong")
                    print("WebSocket: Sent pong response")
                elif data == "pong":
                    print("WebSocket: Received pong from client")
                else:
                    print(f"WebSocket: Received other message: {data}")
                    
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                try:
                    print("WebSocket: Timeout reached, sending ping...")
                    await websocket.send_text("ping")
                    print("WebSocket: Sent ping to keep connection alive")
                except Exception as ping_error:
                    print(f"WebSocket: Error sending ping: {ping_error}")
                    break
            except WebSocketDisconnect:
                print("WebSocket: Client disconnected")
                break
            except Exception as e:
                print(f"WebSocket: Error in message handling: {e}")
                break
                
    except WebSocketDisconnect:
        print("WebSocket: Connection disconnected")
    except Exception as e:
        print(f"WebSocket: Endpoint error: {e}")
        import traceback
        print(f"WebSocket: Full error traceback: {traceback.format_exc()}")
    finally:
        if websocket in websocket_manager.active_connections:
            websocket_manager.active_connections.remove(websocket)
        print("WebSocket: Connection cleaned up")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

# LangChain Analysis Endpoints
@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_data(
    request: AnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze data using LangChain AI"""
    try:
        # Get recent data for analysis
        recent_data = data_service.get_latest_data(db, limit=100)
        
        # Convert to dict format for LangChain
        data_dicts = [
            {
                "id": item.id,
                "timestamp": item.timestamp.isoformat(),
                "sensor_type": item.sensor_type,
                "value": item.value
            }
            for item in recent_data
        ]
        
        # Load data into LangChain service
        langchain_service.load_data_from_db(data_dicts)
        
        # Perform analysis
        result = langchain_service.analyze(request.query)
        
        return AnalysisResponse(**result)
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        return AnalysisResponse(
            success=False,
            error=str(e),
            timestamp=datetime.utcnow().isoformat()
        )

@app.post("/visualize", response_model=VisualizationResponse)
async def create_visualization(
    request: VisualizationRequest,
    db: Session = Depends(get_db)
):
    """Create data visualization"""
    try:
        # Get recent data for visualization
        recent_data = data_service.get_latest_data(db, limit=100)
        
        # Convert to dict format for LangChain
        data_dicts = [
            {
                "id": item.id,
                "timestamp": item.timestamp.isoformat(),
                "sensor_type": item.sensor_type,
                "value": item.value
            }
            for item in recent_data
        ]
        
        # Load data into LangChain service
        langchain_service.load_data_from_db(data_dicts)
        
        # Create visualization
        result = langchain_service.create_visualization(request.chart_type, request.columns)
        
        return VisualizationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error creating visualization: {str(e)}")
        return VisualizationResponse(
            success=False,
            error=str(e)
        )

@app.get("/data/summary")
async def get_data_summary(db: Session = Depends(get_db)):
    """Get comprehensive data summary for LangChain analysis"""
    try:
        # Get recent data
        recent_data = data_service.get_latest_data(db, limit=100)
        
        # Convert to dict format
        data_dicts = [
            {
                "id": item.id,
                "timestamp": item.timestamp.isoformat(),
                "sensor_type": item.sensor_type,
                "value": item.value
            }
            for item in recent_data
        ]
        
        # Load data into LangChain service
        langchain_service.load_data_from_db(data_dicts)
        
        # Get summary
        summary = langchain_service.get_data_summary()
        
        return summary
        
    except Exception as e:
        logger.error(f"Error getting data summary: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ai/query")
async def ai_query(request: AnalysisRequest):
    """AI Query endpoint for natural conversation - Chat tab"""
    try:
        logger.info(f" Chat Mode: Received query: '{request.query}'")
        
        # Use AI Assistant for natural conversation
        result = ai_assistant.process_query("dashboard", request.query)
        
        logger.info(f" Chat Mode: Response generated successfully")
        
        # Return in required format: { "input": "...", "output": "..." }
        if result.get("success"):
            # Return the full structured response for chat mode
            return {
                "input": request.query,
                "output": result  # Return the full result object
            }
        else:
            return {
                "input": request.query,
                "output": f"Sorry, I encountered an error: {result.get('error', 'Unknown error')}"
            }
        
    except Exception as e:
        logger.error(f" Chat Mode Error: {str(e)}")
        
        return {
            "input": request.query,
            "output": f"Sorry, I'm having trouble processing your request. Please try again."
        }

# Unified Semantic Service Endpoints
@app.post("/semantic/query")
async def semantic_query(request: AnalysisRequest):
    """Process natural language queries using unified semantic service"""
    try:
        logger.info(f" Unified Service: Processing query: '{request.query}'")
        
        result = get_unified_semantic_service().process_query(request.query)
        
        return {
            "input": request.query,
            "output": result.get("summary", "No response generated"),
            "success": result.get("success", False),
            "summary": result.get("summary", ""),
            "metrics": result.get("metrics", {}),
            "raw_data": result.get("raw_data", []),
            "chart": result.get("chart", None),
            "chart_type": result.get("chart_type", None),
            "chart_metadata": result.get("chart_metadata", None),
            "sql": result.get("sql", ""),
            "language": result.get("language", "unknown"),
            "feature_context": result.get("feature_context", "dashboard"),
            "timestamp": result.get("timestamp"),
            "validation": result.get("validation", {"query_valid": False, "execution_success": False})
        }
        
    except Exception as e:
        logger.error(f" Unified Service Error: {str(e)}")
        return {
            "input": request.query,
            "output": f"Error processing query: {str(e)}",
            "success": False
        }

@app.post("/semantic/verify-query")
async def verify_query(request: AnalysisRequest):
    """Verify if a query will generate valid SQL without executing it"""
    try:
        logger.info(f" Query Verification: '{request.query}'")
        
        # Get the service
        service = get_unified_semantic_service()
        
        # Generate SQL without executing
        english_query = request.query
        if service.translator.detect_language(request.query) == 'fa':
            english_query = service.translator.translate_query_to_english(request.query)
        
        sql_query = service._generate_simple_sql(english_query)
        validation_result = service._validate_sql_query(sql_query)
        
        return {
            "query": request.query,
            "translated_query": english_query,
            "generated_sql": sql_query,
            "validation": validation_result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f" Query Verification Error: {str(e)}")
        return {
            "query": request.query,
            "error": str(e),
            "validation": {"valid": False, "message": f"Verification error: {str(e)}"}
        }

@app.get("/semantic/sample-queries")
async def get_semantic_sample_queries():
    """Get sample queries for each semantic entity"""
    try:
        return get_unified_semantic_service().get_sample_queries()
    except Exception as e:
        logger.error(f"Error fetching sample queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sample queries")

@app.get("/semantic/ontology")
async def get_semantic_ontology():
    """Get the semantic layer ontology"""
    try:
        return get_unified_semantic_service().get_ontology()
    except Exception as e:
        logger.error(f"Error fetching ontology: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch ontology")

@app.get("/semantic/debug")
async def semantic_debug():
    """Debug endpoint to inspect unified semantic service"""
    try:
        # Test with sample queries
        test_queries = [
            "سلام آبیاری امروز کمه یا نه",
            "What is the current temperature?",
            "وضعیت آفات چطوره؟"
        ]
        
        results = []
        for query in test_queries:
            result = get_unified_semantic_service().process_query(query)
            results.append({
                "query": query,
                "success": result.get("success", False),
                "language": result.get("language", "unknown"),
                "data_points": result.get("data_points", 0),
                "llm_type": result.get("llm_type", "unknown"),
                "context_length": result.get("context_length", 0),
                "response_preview": result.get("response", "")[:100] + "..." if len(result.get("response", "")) > 100 else result.get("response", "")
            })
        
        return {
            "service_status": "active",
            "test_results": results,
            "ontology_entities": len(get_unified_semantic_service().get_ontology()["entities"]),
            "sample_queries_available": len(get_unified_semantic_service().get_sample_queries())
        }
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {e}")
        return {"error": str(e)}

@app.post("/chat")
async def chat_with_history(request: dict):
    """Chat endpoint with conversation history"""
    try:
        query = request.get("query", "")
        session_id = request.get("session_id", "default")
        feature_context = request.get("feature_context", "dashboard")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        logger.info(f" Chat request: session={session_id}, query='{query[:50]}...'")
        
        # Process query with conversation history
        result = get_unified_semantic_service().process_query(
            query=query,
            feature_context=feature_context,
            session_id=session_id
        )
        
        return {
            "success": True,
            "session_id": session_id,
            "query": query,
            "response": result.get("summary", "No response generated"),
            "data": result.get("raw_data", []),
            "sql": result.get("sql", ""),
            "translated_query": result.get("translated_query", query),
            "feature_context": feature_context,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")

@app.post("/ask")
async def ask_with_intent_routing(request: dict):
    """Smart intent routing endpoint - main entry point for AI Assistant"""
    try:
        print(f"\n{'='*100}")
        print(f" API ENDPOINT /ask - NEW REQUEST RECEIVED")
        print(f"{'='*100}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"{'='*100}")
        
        query = request.get("query", "")
        session_id = request.get("session_id", "default")
        feature_context = request.get("feature_context", "dashboard")
        
        print(f"\n EXTRACTED PARAMETERS:")
        print(f"    Query length: {len(query)} characters")
        print(f"   Session ID: {session_id}")
        print(f"    Feature Context: {feature_context}")
        
        if not query:
            print(f"\n ERROR: Query is required but not provided")
            raise HTTPException(status_code=400, detail="Query is required")
        
        print(f"\n CALLING INTENT ROUTER LAYER...")
        logger.info(f" Intent Router: Processing query: '{query[:50]}...' for session: {session_id}")
        
        # Process query with intent routing
        result = intent_router_layer.process_query(
            query=query,
            session_id=session_id,
            feature_context=feature_context
        )
        
        print(f"\n INTENT ROUTER RESULT:")
        print(f"    Success: {result.get('success', False)}")
        print(f"    Response Length: {len(result.get('response', ''))}")
        print(f"    Language: {result.get('detected_language', 'unknown')}")
        print(f"    Intent: {result.get('detected_intent', 'unknown')}")
        print(f"    Data Points: {len(result.get('data', []))}")
        print(f"    SQL Generated: {'Yes' if result.get('sql') else 'No'}")
        
        # Log the complete flow for debugging
        logger.info(f" Intent Router Result:")
        logger.info(f"   - Intent: {result.get('detected_intent', 'unknown')}")
        logger.info(f"   - Language: {result.get('detected_language', 'unknown')}")
        logger.info(f"   - Success: {result.get('success', False)}")
        logger.info(f"   - SQL Generated: {'Yes' if result.get('sql') else 'No'}")
        logger.info(f"   - Data Points: {len(result.get('data', []))}")
        
        # Prepare response
        response_data = {
            "success": True,
            "session_id": session_id,
            "query": query,
            "response": result.get("response", "No response generated"),
            "data": result.get("data", []),
            "chart": result.get("chart", None),
            "chart_type": result.get("chart_type", None),
            "chart_metadata": result.get("chart_metadata", None),
            "sql": result.get("sql", ""),
            "metrics": result.get("metrics", {}),
            "detected_intent": result.get("detected_intent", "unknown"),
            "detected_language": result.get("detected_language", "unknown"),
            "english_query": result.get("english_query", query),
            "feature_context": feature_context,
            "validation": result.get("validation", {}),
            "timestamp": result.get("timestamp", datetime.utcnow().isoformat()),
            "conversation_context_length": result.get("conversation_context_length", 0)
        }
        
        print(f"\n SENDING RESPONSE TO CLIENT:")
        print(f"    Success: {response_data['success']}")
        try:
            print(f"    Response: {response_data['response'][:100]}...")
        except UnicodeEncodeError:
            print(f"    Response: [Text with special characters - encoding safe]")
        print(f"    Language: {response_data['detected_language']}")
        print(f"    Intent: {response_data['detected_intent']}")
        print(f"    Data Points: {len(response_data['data'])}")
        print(f"{'='*100}")
        print(f" API REQUEST COMPLETED SUCCESSFULLY")
        print(f"{'='*100}\n")
        
        return response_data
        
    except Exception as e:
        print(f"\n ERROR IN API ENDPOINT /ask:")
        print(f"   Error: {str(e)}")
        print(f"   Request: {request}")
        print(f"{'='*100}\n")
        
        logger.error(f"Intent Router endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Intent routing failed: {str(e)}")

@app.post("/ask/stream")
async def ask_with_streaming(request: dict):
    """Streaming version of the ask endpoint for real-time AI responses with REAL DATA"""
    try:
        print(f"\n{'='*100}")
        print(f" STREAMING ENDPOINT /ask/stream - NEW REQUEST RECEIVED")
        print(f"{'='*100}")
        # Avoid printing request body with Persian text
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print(f"{'='*100}")
        
        query = request.get("query", "")
        session_id = request.get("session_id", "default")
        feature_context = request.get("feature_context", "dashboard")
        
        # Debug: Print query info without Persian text
        print(f" Query length: {len(query)} characters")
        print(f" Session ID: {session_id}")
        print(f" Feature context: {feature_context}")
        
        if not query:
            raise HTTPException(status_code=400, detail="Query is required")
        
        print(f"\n STARTING STREAMING PROCESSING...")
        logger.info(f" Streaming: Processing query: '{query[:50]}...' for session: {session_id}")
        
        # STEP 1: Process query through intent router layer (SAME AS REGULAR ENDPOINT)
        print(f" STEP 1: Processing query through intent router layer...")
        logger.info(f" Streaming: Processing query through intent router: {query}")
        
        try:
            # Call intent router layer synchronously (same as regular endpoint)
            result = intent_router_layer.process_query(
                query=query,
                session_id=session_id,
                feature_context=feature_context
            )
            
            print(f" STEP 1 RESULT - Intent Router:")
            print(f"    Success: {result.get('success', False)}")
            print(f"    Data Points: {len(result.get('data', []))}")
            print(f"    SQL Generated: {'Yes' if result.get('sql') else 'No'}")
            print(f"    Intent: {result.get('detected_intent', 'unknown')}")
            print(f"    Language: {result.get('detected_language', 'unknown')}")
            
            # Log the complete result for debugging
            logger.info(f" Intent Router Complete Result: {result}")
            
            # Verify we have real data
            if result.get('data'):
                print(f" REAL DATA RETRIEVED: {len(result['data'])} data points")
                for i, data_point in enumerate(result['data']):
                    print(f"    Data Point {i+1}: {data_point}")
            else:
                print(f" NO DATA RETRIEVED from intent router!")
            
        except Exception as e:
            print(f" ERROR in intent router processing: {e}")
            logger.error(f" Intent router error in streaming: {e}")
            # Create a fallback result
            result = {
                'success': False,
                'data': [],
                'sql': '',
                'detected_intent': 'error',
                'detected_language': 'unknown',
                'response': f'Error processing query: {str(e)}'
            }
        
        # STEP 2: Create streaming generator with REAL DATA
        async def generate_stream():
            """Generator function for streaming response with REAL DATA from intent router"""
            try:
                # Check if this is an alert management query
                detected_intent = result.get('detected_intent', 'unknown')
                
                if detected_intent == 'alert_management':
                    # For alert queries, return the response directly without AI analysis
                    print(f" ALERT QUERY DETECTED - Returning direct response")
                    yield f"data: {json.dumps({'step': 1, 'message': 'Processing alert request...', 'progress': 50}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.1)
                    
                    # Send the final complete result for alert queries
                    final_result = {
                        'success': result.get('success', True),
                        'response': result.get('response', ''),
                        'data': result.get('data', []),
                        'sql': result.get('sql', ''),
                        'metrics': result.get('metrics', {}),
                        'validation': result.get('validation', {'query_valid': True, 'execution_success': True}),
                        'detected_intent': result.get('detected_intent', 'unknown'),
                        'detected_language': result.get('detected_language', 'unknown'),
                        'english_query': result.get('english_query', query),
                        'feature_context': feature_context,
                        'timestamp': result.get('timestamp', datetime.utcnow().isoformat()),
                        'conversation_context_length': result.get('conversation_context_length', 0),
                        'chart': result.get('chart', None),
                        'chart_type': result.get('chart_type', None)
                    }
                    
                    print(f" ALERT FINAL RESULT: {final_result}")
                    yield f"data: {json.dumps({'step': 'complete', 'result': final_result, 'progress': 100}, ensure_ascii=False)}\n\n"
                    
                    # Send completion signal
                    yield f"data: [DONE]\n\n"
                    return
                
                # For data queries, proceed with normal AI analysis
                # Step 1: Language detection and translation
                yield f"data: {json.dumps({'step': 1, 'message': 'Language detection and translation...', 'progress': 20}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 2: Intent detection
                yield f"data: {json.dumps({'step': 2, 'message': 'Intent detection...', 'progress': 40}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 3: SQL execution (already completed)
                yield f"data: {json.dumps({'step': 3, 'message': 'Executing SQL query...', 'progress': 60}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)
                
                # Step 4: Start AI response generation with REAL DATA
                yield f"data: {json.dumps({'step': 4, 'message': 'Generating AI response...', 'progress': 80, 'streaming_start': True}, ensure_ascii=False)}\n\n"
                
                # Get the unified semantic service for streaming
                unified_service = get_unified_semantic_service()
                
                # Create streaming prompt with REAL DATA from intent router
                print(f" STEP 2: Creating streaming prompt with REAL DATA...")
                print(f" DEBUG: result variable: {result}")
                print(f" DEBUG: result.get('data'): {result.get('data')}")
                print(f" DEBUG: len(result.get('data', [])): {len(result.get('data', []))}")
                
                real_data_text = ""
                if result.get('data'):
                    real_data_text = "\n\n## ACTUAL SENSOR DATA FROM DATABASE:\n"
                    for data_point in result['data']:
                        sensor_type = data_point.get('sensor_type', 'unknown')
                        # Handle both raw data (value) and aggregated data (avg_value)
                        if 'avg_value' in data_point:
                            # Aggregated data (time-aware queries)
                            avg_value = data_point.get('avg_value', 0)
                            min_value = data_point.get('min_value', 0)
                            max_value = data_point.get('max_value', 0)
                            time_period = data_point.get('time_period', 'N/A')
                            data_points = data_point.get('data_points', 0)
                            real_data_text += f"- {sensor_type}: {avg_value:.2f} (avg), {min_value:.2f} (min), {max_value:.2f} (max) - {time_period} ({data_points} points)\n"
                        else:
                            # Raw data (legacy)
                            value = data_point.get('value', 'N/A')
                            timestamp = data_point.get('timestamp', 'N/A')
                            real_data_text += f"- {sensor_type}: {value} (measured at {timestamp})\n"
                    print(f" REAL DATA TEXT CREATED: {real_data_text}")
                else:
                    print(f" NO DATA AVAILABLE - real_data_text will be empty")
                
                # Create the streaming prompt with REAL DATA and proper language detection
                detected_language = result.get('detected_language', 'unknown')
                language_instruction = ""
                
                if detected_language == 'fa':
                    language_instruction = "IMPORTANT: The user query is in Persian (Farsi). You MUST respond in Persian (Farsi) with proper Persian text."
                else:
                    language_instruction = "The user query is in English. Respond in English."
                
                streaming_prompt = f"""You are an expert agricultural AI assistant. Provide concise, helpful responses.

RESPONSE STRUCTURE:
1. **Brief Summary** - 2 sentences maximum about the current situation
2. **Clean Data Section** - Show the actual data in a readable format

GUIDELINES:
- Keep it short and to the point (2 sentences max)
- Give quick insights about what the data shows
- {language_instruction}
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

IMPORTANT: Use the actual sensor data values provided below. Be specific and helpful.

User Query: {query}
Detected Language: {detected_language}
Feature Context: {feature_context}

ACTUAL DATA FROM DATABASE:
{real_data_text}

Provide an intelligent, helpful response with a clean data section using the actual values above."""
                
                print(f" STEP 3: Starting LLM streaming with REAL DATA...")
                logger.info(f" Starting LLM streaming for query: {query}")
                
                # Stream the LLM response token by token
                accumulated_response = ""
                token_count = 0
                print(f"🚀 Starting LLM streaming...")
                async for token in unified_service.translator.stream_response(streaming_prompt):
                    token_count += 1
                    accumulated_response += token
                    yield f"data: {json.dumps({'step': 4, 'token': token, 'accumulated': accumulated_response, 'progress': 85}, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(0.01)  # Small delay between tokens
                
                print(f"✅ Streaming completed. Total tokens: {token_count}")
                logger.info(f" Streaming completed. Total tokens: {token_count}")
                
                # Step 5: Final formatting
                yield f"data: {json.dumps({'step': 5, 'message': 'Finalizing response...', 'progress': 90}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0.1)
                
                # Send the final complete result with REAL DATA
                final_result = {
                    'success': result.get('success', True),
                    'response': accumulated_response,
                    'data': result.get('data', []),  # REAL DATA from intent router
                    'sql': result.get('sql', ''),   # REAL SQL from intent router
                    'metrics': result.get('metrics', {}),
                    'validation': result.get('validation', {'query_valid': True, 'execution_success': True}),
                    'detected_intent': result.get('detected_intent', 'unknown'),
                    'detected_language': result.get('detected_language', 'unknown'),
                    'english_query': result.get('english_query', query),
                    'feature_context': feature_context,
                    'timestamp': result.get('timestamp', datetime.utcnow().isoformat()),
                    'conversation_context_length': result.get('conversation_context_length', 0),
                    'chart': result.get('chart', None),  # Chart data
                    'chart_type': result.get('chart_type', None)  # Chart type
                }
                
                print(f" FINAL RESULT: {final_result}")
                yield f"data: {json.dumps({'step': 'complete', 'result': final_result, 'progress': 100}, ensure_ascii=False)}\n\n"
                
                # Send completion signal
                yield f"data: [DONE]\n\n"
                
            except Exception as e:
                print(f" ERROR in streaming generator: {e}")
                logger.error(f"Streaming error: {e}")
                yield f"data: {json.dumps({'error': str(e), 'step': 'error'}, ensure_ascii=False)}\n\n"
                yield f"data: [DONE]\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*",
            }
        )
        
    except Exception as e:
        print(f" ERROR in streaming endpoint: {e}")
        logger.error(f"Streaming endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Streaming failed: {str(e)}")

@app.get("/ask/health")
async def intent_router_health():
    """Health check for Intent Router Layer"""
    try:
        return intent_router_layer.get_health_status()
    except Exception as e:
        logger.error(f"Intent Router health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Include AI Assistant router
app.include_router(ai_assistant_router, prefix="/api", tags=["AI Assistant"])

# NEW: Alert Management API Endpoints
@app.get("/api/alerts")
async def get_user_alerts(session_id: str = "default"):
    """Get all alerts for a user"""
    try:
        from app.services.alert_manager import AlertManager
        alert_manager = AlertManager()
        alerts = alert_manager.get_user_alerts(session_id)
        return {"success": True, "alerts": alerts}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/alerts")
async def create_alert(alert_data: dict, session_id: str = "default"):
    """Create a new alert"""
    try:
        from app.services.alert_manager import AlertManager
        alert_manager = AlertManager()
        result = alert_manager.create_alert_from_natural_language(
            alert_data.get("query", ""), session_id
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/alerts/{alert_id}")
async def delete_alert(alert_id: str, session_id: str = "default"):
    """Delete an alert"""
    try:
        from app.services.alert_manager import AlertManager
        alert_manager = AlertManager()
        success = alert_manager.delete_alert(alert_id, session_id)
        return {"success": success, "message": "Alert deleted" if success else "Alert not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/alerts/monitor")
async def monitor_alerts(session_id: str = "default"):
    """Monitor current sensor data against alerts"""
    try:
        from app.services.alert_monitor import AlertMonitor
        from app.services.unified_semantic_service import UnifiedSemanticQueryService
        
        # Get current sensor data
        service = UnifiedSemanticQueryService()
        live_data = service._get_live_sensor_data()
        
        # Monitor alerts
        monitor = AlertMonitor()
        triggered_alerts = monitor.monitor_sensor_data(live_data, session_id)
        
        return {
            "success": True,
            "triggered_alerts": triggered_alerts,
            "data_points": len(live_data)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/alerts/actions")
async def get_action_logs(session_id: str = "default"):
    """Get action logs for alerts"""
    try:
        import sqlite3
        import json
        
        # Connect to database - use PostgreSQL on Liara, SQLite locally
        if os.getenv("LIARA_APP_ID"):
            # Use PostgreSQL on Liara
            import psycopg2
            from urllib.parse import urlparse
            db_url = os.getenv("DATABASE_URL")
            parsed = urlparse(db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
        else:
            # Use SQLite locally
            conn = sqlite3.connect("smart_dashboard.db")
        cursor = conn.cursor()
        
        # Create action_logs table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id TEXT PRIMARY KEY,
                alert_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                timestamp TEXT NOT NULL,
                completed_at TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Get action logs for this session
        cursor.execute('''
            SELECT * FROM action_logs 
            WHERE session_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 50
        ''', (session_id,))
        
        logs = cursor.fetchall()
        
        # Convert to list of dictionaries
        action_logs = []
        for log in logs:
            action_logs.append({
                "id": log[0],
                "alert_id": log[1],
                "action_type": log[2],
                "status": log[3],
                "message": log[4],
                "timestamp": log[5],
                "completed_at": log[6],
                "session_id": log[7],
                "created_at": log[8]
            })
        
        conn.close()
        
        return {
            "success": True,
            "action_logs": action_logs,
            "total_logs": len(action_logs)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/alerts/actions")
async def create_action_log(action_data: dict):
    """Create a new action log entry"""
    try:
        import sqlite3
        import json
        from datetime import datetime
        
        # Connect to database - use PostgreSQL on Liara, SQLite locally
        if os.getenv("LIARA_APP_ID"):
            # Use PostgreSQL on Liara
            import psycopg2
            from urllib.parse import urlparse
            db_url = os.getenv("DATABASE_URL")
            parsed = urlparse(db_url)
            conn = psycopg2.connect(
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path[1:],  # Remove leading slash
                user=parsed.username,
                password=parsed.password
            )
        else:
            # Use SQLite locally
            conn = sqlite3.connect("smart_dashboard.db")
        cursor = conn.cursor()
        
        # Create action_logs table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS action_logs (
                id TEXT PRIMARY KEY,
                alert_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                timestamp TEXT NOT NULL,
                completed_at TEXT,
                session_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert new action log
        log_id = f"log_{int(datetime.now().timestamp() * 1000)}"
        cursor.execute('''
            INSERT INTO action_logs (id, alert_id, action_type, status, message, timestamp, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            log_id,
            action_data.get("alert_id"),
            action_data.get("action_type"),
            action_data.get("status", "executing"),
            action_data.get("message"),
            action_data.get("timestamp"),
            action_data.get("session_id")
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "log_id": log_id,
            "message": "Action log created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
