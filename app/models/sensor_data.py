from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class SensorData(Base):
    __tablename__ = "sensor_data"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    sensor_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    
    def __repr__(self):
        return f"<SensorData(id={self.id}, sensor_type='{self.sensor_type}', value={self.value}, timestamp='{self.timestamp}')>"
