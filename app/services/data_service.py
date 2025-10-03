from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Optional
from app.models.sensor_data import SensorData
from app.models.schemas import SensorDataCreate, SensorDataResponse, StatsResponse
from datetime import datetime

class DataService:
    """Service class for sensor data operations"""
    
    def create_sensor_data(self, db: Session, data: SensorDataCreate) -> SensorDataResponse:
        """Create a new sensor data record"""
        db_sensor_data = SensorData(
            sensor_type=data.sensor_type,
            value=data.value
        )
        db.add(db_sensor_data)
        db.commit()
        db.refresh(db_sensor_data)
        return SensorDataResponse.from_orm(db_sensor_data)
    
    def get_latest_data(
        self, 
        db: Session, 
        limit: int = 10, 
        sensor_type: Optional[str] = None
    ) -> List[SensorDataResponse]:
        """Get latest sensor data records"""
        query = db.query(SensorData)
        
        if sensor_type:
            query = query.filter(SensorData.sensor_type == sensor_type)
        
        records = query.order_by(desc(SensorData.timestamp)).limit(limit).all()
        return [SensorDataResponse.from_orm(record) for record in records]
    
    def get_data_stats(self, db: Session) -> Dict[str, StatsResponse]:
        """Get statistical analysis for each sensor type"""
        # Get all unique sensor types
        sensor_types = db.query(SensorData.sensor_type).distinct().all()
        sensor_types = [sensor_type[0] for sensor_type in sensor_types]
        
        stats = {}
        for sensor_type in sensor_types:
            # Calculate statistics for each sensor type
            result = db.query(
                func.count(SensorData.id).label('count'),
                func.avg(SensorData.value).label('average'),
                func.min(SensorData.value).label('min_value'),
                func.max(SensorData.value).label('max_value'),
                func.max(SensorData.timestamp).label('latest_timestamp')
            ).filter(SensorData.sensor_type == sensor_type).first()
            
            if result:
                stats[sensor_type] = StatsResponse(
                    count=result.count,
                    average=round(result.average, 2),
                    min_value=result.min_value,
                    max_value=result.max_value,
                    latest_timestamp=result.latest_timestamp
                )
        
        return stats
    
    def get_sensor_types(self, db: Session) -> List[str]:
        """Get all available sensor types"""
        sensor_types = db.query(SensorData.sensor_type).distinct().all()
        return [sensor_type[0] for sensor_type in sensor_types]
    
    def get_data_by_time_range(
        self, 
        db: Session, 
        start_time: datetime, 
        end_time: datetime,
        sensor_type: Optional[str] = None
    ) -> List[SensorDataResponse]:
        """Get sensor data within a time range"""
        query = db.query(SensorData).filter(
            SensorData.timestamp >= start_time,
            SensorData.timestamp <= end_time
        )
        
        if sensor_type:
            query = query.filter(SensorData.sensor_type == sensor_type)
        
        records = query.order_by(desc(SensorData.timestamp)).all()
        return [SensorDataResponse.from_orm(record) for record in records]
