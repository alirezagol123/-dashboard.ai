"""
FastAPI Semantic Layer Endpoints
Provides REST API for IrrigationEvent, EnvironmentControl, and PestDetection entities
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field
import asyncio
import logging

from app.services.semantic_layer import SemanticLayer, IrrigationEvent, EnvironmentControl, PestDetection, IrrigationMethod, IrrigationStatus, PestSeverity, DetectionMethod

logger = logging.getLogger(__name__)

# Pydantic models for API requests/responses
class IrrigationEventCreate(BaseModel):
    water_amount_liters: float = Field(..., gt=0, description="Amount of water in liters")
    irrigation_method: IrrigationMethod = Field(..., description="Method of irrigation")
    irrigation_duration_minutes: int = Field(..., gt=0, description="Duration in minutes")
    status: IrrigationStatus = Field(..., description="Status of irrigation")

class IrrigationEventResponse(BaseModel):
    event_id: str
    timestamp: datetime
    water_amount_liters: float
    irrigation_method: str
    irrigation_duration_minutes: int
    status: str

class EnvironmentControlCreate(BaseModel):
    temperature_celsius: float = Field(..., ge=-50, le=100, description="Temperature in Celsius")
    humidity_percent: float = Field(..., ge=0, le=100, description="Humidity percentage")
    co2_ppm: int = Field(..., ge=0, le=10000, description="CO2 level in ppm")
    light_lux: int = Field(..., ge=0, description="Light level in lux")
    fan_status: bool = Field(default=False, description="Fan status")
    heater_status: bool = Field(default=False, description="Heater status")

class EnvironmentControlResponse(BaseModel):
    control_id: str
    timestamp: datetime
    temperature_celsius: float
    humidity_percent: float
    co2_ppm: int
    light_lux: int
    fan_status: bool
    heater_status: bool

class PestDetectionCreate(BaseModel):
    pest_or_disease_type: str = Field(..., description="Type of pest or disease")
    severity_level: PestSeverity = Field(..., description="Severity level")
    detected_by: DetectionMethod = Field(..., description="Detection method")
    recommended_action: str = Field(..., description="Recommended action")

class PestDetectionResponse(BaseModel):
    detection_id: str
    timestamp: datetime
    pest_or_disease_type: str
    severity_level: str
    detected_by: str
    recommended_action: str

class NaturalLanguageQuery(BaseModel):
    query: str = Field(..., description="Natural language query")

class QueryResponse(BaseModel):
    parsed_query: Dict[str, Any]
    sql: Optional[str] = None
    entity: Optional[str] = None
    valid: bool
    message: Optional[str] = None
    suggestions: Optional[List[str]] = None

# Initialize FastAPI app
app = FastAPI(
    title="Agriculture Semantic Layer API",
    description="Semantic layer for agriculture and greenhouse management",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize semantic layer
semantic_layer = SemanticLayer()

# Mock database (replace with actual database connection)
irrigation_events_db: List[IrrigationEvent] = []
environment_controls_db: List[EnvironmentControl] = []
pest_detections_db: List[PestDetection] = []

# Irrigation Events Endpoints
@app.post("/api/irrigation-events", response_model=IrrigationEventResponse)
async def create_irrigation_event(event: IrrigationEventCreate):
    """Create a new irrigation event"""
    try:
        new_event = IrrigationEvent(
            event_id=f"irr_{len(irrigation_events_db) + 1}",
            timestamp=datetime.now(),
            water_amount_liters=event.water_amount_liters,
            irrigation_method=event.irrigation_method,
            irrigation_duration_minutes=event.irrigation_duration_minutes,
            status=event.status
        )
        irrigation_events_db.append(new_event)
        return IrrigationEventResponse(**new_event.to_dict())
    except Exception as e:
        logger.error(f"Error creating irrigation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create irrigation event")

@app.get("/api/irrigation-events", response_model=List[IrrigationEventResponse])
async def get_irrigation_events(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[IrrigationStatus] = None
):
    """Get irrigation events with optional filtering"""
    try:
        events = irrigation_events_db.copy()
        
        if status:
            events = [e for e in events if e.status == status]
        
        events = events[offset:offset + limit]
        return [IrrigationEventResponse(**event.to_dict()) for event in events]
    except Exception as e:
        logger.error(f"Error fetching irrigation events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch irrigation events")

@app.get("/api/irrigation-events/latest", response_model=IrrigationEventResponse)
async def get_latest_irrigation_event():
    """Get the latest irrigation event"""
    try:
        if not irrigation_events_db:
            raise HTTPException(status_code=404, detail="No irrigation events found")
        
        latest_event = max(irrigation_events_db, key=lambda x: x.timestamp)
        return IrrigationEventResponse(**latest_event.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest irrigation event: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest irrigation event")

@app.get("/api/irrigation-events/today")
async def get_today_irrigation_events():
    """Get irrigation events from today"""
    try:
        today = date.today()
        today_events = [
            e for e in irrigation_events_db 
            if e.timestamp.date() == today
        ]
        return [IrrigationEventResponse(**event.to_dict()) for event in today_events]
    except Exception as e:
        logger.error(f"Error fetching today's irrigation events: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch today's irrigation events")

# Environment Controls Endpoints
@app.post("/api/environment-controls", response_model=EnvironmentControlResponse)
async def create_environment_control(control: EnvironmentControlCreate):
    """Create a new environment control record"""
    try:
        new_control = EnvironmentControl(
            control_id=f"env_{len(environment_controls_db) + 1}",
            timestamp=datetime.now(),
            temperature_celsius=control.temperature_celsius,
            humidity_percent=control.humidity_percent,
            co2_ppm=control.co2_ppm,
            light_lux=control.light_lux,
            fan_status=control.fan_status,
            heater_status=control.heater_status
        )
        environment_controls_db.append(new_control)
        return EnvironmentControlResponse(**new_control.to_dict())
    except Exception as e:
        logger.error(f"Error creating environment control: {e}")
        raise HTTPException(status_code=500, detail="Failed to create environment control")

@app.get("/api/environment-controls", response_model=List[EnvironmentControlResponse])
async def get_environment_controls(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get environment control records"""
    try:
        controls = environment_controls_db[offset:offset + limit]
        return [EnvironmentControlResponse(**control.to_dict()) for control in controls]
    except Exception as e:
        logger.error(f"Error fetching environment controls: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch environment controls")

@app.get("/api/environment-controls/latest", response_model=EnvironmentControlResponse)
async def get_latest_environment_control():
    """Get the latest environment control record"""
    try:
        if not environment_controls_db:
            raise HTTPException(status_code=404, detail="No environment controls found")
        
        latest_control = max(environment_controls_db, key=lambda x: x.timestamp)
        return EnvironmentControlResponse(**latest_control.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest environment control: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest environment control")

@app.get("/api/environment-controls/current-humidity")
async def get_current_humidity():
    """Get current humidity level"""
    try:
        if not environment_controls_db:
            raise HTTPException(status_code=404, detail="No environment controls found")
        
        latest_control = max(environment_controls_db, key=lambda x: x.timestamp)
        return {"humidity_percent": latest_control.humidity_percent}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current humidity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch current humidity")

@app.get("/api/environment-controls/current-temperature")
async def get_current_temperature():
    """Get current temperature"""
    try:
        if not environment_controls_db:
            raise HTTPException(status_code=404, detail="No environment controls found")
        
        latest_control = max(environment_controls_db, key=lambda x: x.timestamp)
        return {"temperature_celsius": latest_control.temperature_celsius}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching current temperature: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch current temperature")

# Pest Detection Endpoints
@app.post("/api/pest-detections", response_model=PestDetectionResponse)
async def create_pest_detection(detection: PestDetectionCreate):
    """Create a new pest detection record"""
    try:
        new_detection = PestDetection(
            detection_id=f"pest_{len(pest_detections_db) + 1}",
            timestamp=datetime.now(),
            pest_or_disease_type=detection.pest_or_disease_type,
            severity_level=detection.severity_level,
            detected_by=detection.detected_by,
            recommended_action=detection.recommended_action
        )
        pest_detections_db.append(new_detection)
        return PestDetectionResponse(**new_detection.to_dict())
    except Exception as e:
        logger.error(f"Error creating pest detection: {e}")
        raise HTTPException(status_code=500, detail="Failed to create pest detection")

@app.get("/api/pest-detections", response_model=List[PestDetectionResponse])
async def get_pest_detections(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    severity: Optional[PestSeverity] = None
):
    """Get pest detection records with optional filtering"""
    try:
        detections = pest_detections_db.copy()
        
        if severity:
            detections = [d for d in detections if d.severity_level == severity]
        
        detections = detections[offset:offset + limit]
        return [PestDetectionResponse(**detection.to_dict()) for detection in detections]
    except Exception as e:
        logger.error(f"Error fetching pest detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch pest detections")

@app.get("/api/pest-detections/today")
async def get_today_pest_detections():
    """Get pest detections from today"""
    try:
        today = date.today()
        today_detections = [
            d for d in pest_detections_db 
            if d.timestamp.date() == today
        ]
        return [PestDetectionResponse(**detection.to_dict()) for detection in today_detections]
    except Exception as e:
        logger.error(f"Error fetching today's pest detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch today's pest detections")

@app.get("/api/pest-detections/high-severity")
async def get_high_severity_pest_detections():
    """Get high severity pest detections"""
    try:
        high_severity_detections = [
            d for d in pest_detections_db 
            if d.severity_level in [PestSeverity.HIGH, PestSeverity.CRITICAL]
        ]
        return [PestDetectionResponse(**detection.to_dict()) for detection in high_severity_detections]
    except Exception as e:
        logger.error(f"Error fetching high severity pest detections: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch high severity pest detections")

# Natural Language Query Endpoint
@app.post("/api/query", response_model=QueryResponse)
async def process_natural_language_query(query: NaturalLanguageQuery):
    """Process natural language queries using semantic layer"""
    try:
        result = semantic_layer.parse_natural_language_query(query.query)
        validation = semantic_layer.validate_query(query.query)
        
        return QueryResponse(
            parsed_query=result,
            sql=result.get("sql"),
            entity=result.get("entity"),
            valid=validation["valid"],
            message=validation.get("message"),
            suggestions=validation.get("suggestions")
        )
    except Exception as e:
        logger.error(f"Error processing natural language query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process query")

# Sample Queries Endpoint
@app.get("/api/sample-queries")
async def get_sample_queries():
    """Get sample queries for each entity"""
    try:
        return semantic_layer.get_sample_queries()
    except Exception as e:
        logger.error(f"Error fetching sample queries: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sample queries")

# Health Check
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "entities": {
            "irrigation_events": len(irrigation_events_db),
            "environment_controls": len(environment_controls_db),
            "pest_detections": len(pest_detections_db)
        }
    }

# Initialize with sample data
@app.on_event("startup")
async def startup_event():
    """Initialize with sample data"""
    try:
        # Add sample irrigation events
        sample_irrigation = [
            IrrigationEvent(
                event_id="irr_sample_1",
                timestamp=datetime.now(),
                water_amount_liters=25.5,
                irrigation_method=IrrigationMethod.DRIP,
                irrigation_duration_minutes=30,
                status=IrrigationStatus.COMPLETED
            ),
            IrrigationEvent(
                event_id="irr_sample_2",
                timestamp=datetime.now(),
                water_amount_liters=15.0,
                irrigation_method=IrrigationMethod.SPRINKLER,
                irrigation_duration_minutes=20,
                status=IrrigationStatus.COMPLETED
            )
        ]
        irrigation_events_db.extend(sample_irrigation)
        
        # Add sample environment controls
        sample_environment = [
            EnvironmentControl(
                control_id="env_sample_1",
                timestamp=datetime.now(),
                temperature_celsius=24.5,
                humidity_percent=65.2,
                co2_ppm=420,
                light_lux=850,
                fan_status=True,
                heater_status=False
            ),
            EnvironmentControl(
                control_id="env_sample_2",
                timestamp=datetime.now(),
                temperature_celsius=25.1,
                humidity_percent=68.5,
                co2_ppm=435,
                light_lux=920,
                fan_status=True,
                heater_status=False
            )
        ]
        environment_controls_db.extend(sample_environment)
        
        # Add sample pest detections
        sample_pest = [
            PestDetection(
                detection_id="pest_sample_1",
                timestamp=datetime.now(),
                pest_or_disease_type="Aphids",
                severity_level=PestSeverity.HIGH,
                detected_by=DetectionMethod.CAMERA,
                recommended_action="Apply neem oil spray immediately"
            ),
            PestDetection(
                detection_id="pest_sample_2",
                timestamp=datetime.now(),
                pest_or_disease_type="Leaf Spot",
                severity_level=PestSeverity.MEDIUM,
                detected_by=DetectionMethod.SENSOR,
                recommended_action="Increase air circulation and reduce humidity"
            )
        ]
        pest_detections_db.extend(sample_pest)
        
        logger.info("Sample data initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing sample data: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
