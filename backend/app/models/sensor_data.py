"""
Sensor Data Model
=================

Stores historical sensor readings for trend analysis.
"""

from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import Column, Integer, Float, String, DateTime, JSON, Index
from sqlalchemy.orm import Mapped

from .database import Base


class SensorData(Base):
    """
    Model for storing sensor data readings.

    Attributes:
        id: Primary key
        timestamp: When the reading was taken
        sensor_type: Type of sensor (dht, bmp280, ultrasonic, etc.)
        temperature: Temperature in Celsius
        humidity: Relative humidity percentage
        pressure: Atmospheric pressure in hPa
        altitude: Altitude in meters
        distance: Distance measurement in cm
        light_level: Light level (0-1023)
        soil_moisture: Soil moisture (0-1023)
        motion: Motion detection status
        adc_values: JSON object with ADC channel readings
        extra_data: Additional sensor-specific data
    """

    __tablename__ = "sensor_data"

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = Column(DateTime, default=datetime.now, nullable=False, index=True)
    sensor_type: Mapped[str] = Column(String(50), nullable=False, index=True)

    # Environmental sensors
    temperature: Mapped[Optional[float]] = Column(Float, nullable=True)
    humidity: Mapped[Optional[float]] = Column(Float, nullable=True)
    pressure: Mapped[Optional[float]] = Column(Float, nullable=True)
    altitude: Mapped[Optional[float]] = Column(Float, nullable=True)

    # Distance sensor
    distance: Mapped[Optional[float]] = Column(Float, nullable=True)

    # Analog sensors
    light_level: Mapped[Optional[int]] = Column(Integer, nullable=True)
    soil_moisture: Mapped[Optional[int]] = Column(Integer, nullable=True)

    # Motion sensor
    motion: Mapped[Optional[bool]] = Column(Integer, nullable=True)  # SQLite doesn't have bool

    # ADC readings as JSON
    adc_values: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # Extra data for flexibility
    extra_data: Mapped[Optional[Dict]] = Column(JSON, nullable=True)

    # Indexes for common queries
    __table_args__ = (
        Index('idx_sensor_timestamp', 'sensor_type', 'timestamp'),
        Index('idx_temperature_time', 'temperature', 'timestamp'),
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "sensor_type": self.sensor_type,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "pressure": self.pressure,
            "altitude": self.altitude,
            "distance": self.distance,
            "light_level": self.light_level,
            "soil_moisture": self.soil_moisture,
            "motion": bool(self.motion) if self.motion is not None else None,
            "adc_values": self.adc_values,
            "extra_data": self.extra_data
        }

    @classmethod
    def from_hardware_data(cls, data: Dict[str, Any]) -> "SensorData":
        """Create SensorData from hardware data dict."""
        return cls(
            sensor_type="all",
            temperature=data.get("temperature"),
            humidity=data.get("humidity"),
            pressure=data.get("pressure"),
            altitude=data.get("altitude"),
            distance=data.get("distance"),
            light_level=data.get("light_level"),
            soil_moisture=data.get("soil_moisture"),
            motion=1 if data.get("motion") else 0,
            adc_values=data.get("adc_values"),
            extra_data=data.get("extra_data")
        )
