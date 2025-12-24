"""
Data Logger Service
===================

Handles persistent data logging to SQLite.
Logs sensor data at configurable intervals.
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging_config import get_logger
from app.models.database import async_session
from app.models.sensor_data import SensorData
from app.models.system_log import SystemLog, LogLevel
from app.models.device_state import DeviceState
from app.hardware.manager import HardwareData

logger = get_logger(__name__)


class DataLogger:
    """
    Service for logging data to SQLite database.

    Features:
    - Automatic sensor data logging at intervals
    - System event logging
    - Device state history
    - Data retrieval for trends
    """

    def __init__(self):
        self._log_interval = settings.DATA_LOG_INTERVAL
        self._log_task: Optional[asyncio.Task] = None
        self._running = False
        self._last_data: Optional[HardwareData] = None

    async def start(self) -> None:
        """Start the data logging loop."""
        if self._running:
            return

        self._running = True
        logger.info(f"Data logger started (interval: {self._log_interval}s)")

    async def stop(self) -> None:
        """Stop the data logging loop."""
        self._running = False

        if self._log_task:
            self._log_task.cancel()
            try:
                await self._log_task
            except asyncio.CancelledError:
                pass
            self._log_task = None

        logger.info("Data logger stopped")

    async def log_hardware_data(self, data: HardwareData) -> None:
        """
        Log hardware data to database.

        Called by hardware manager callback.
        """
        self._last_data = data

        if not self._running:
            return

        try:
            async with async_session() as session:
                sensor_data = SensorData(
                    sensor_type="all",
                    temperature=data.temperature,
                    humidity=data.humidity,
                    pressure=data.pressure,
                    altitude=data.altitude,
                    distance=data.distance,
                    light_level=data.light_level,
                    soil_moisture=data.soil_moisture,
                    motion=1 if data.motion else 0,
                    adc_values={
                        "i2c": data.adc_values,
                        "spi": data.spi_adc_values
                    }
                )
                session.add(sensor_data)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log sensor data: {e}")

    async def log_system_event(
        self,
        level: LogLevel,
        source: str,
        message: str,
        details: Dict[str, Any] = None,
        user_action: bool = False
    ) -> None:
        """Log a system event."""
        try:
            async with async_session() as session:
                log_entry = SystemLog.create_log(
                    level=level,
                    source=source,
                    message=message,
                    details=details,
                    user_action=user_action
                )
                session.add(log_entry)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log system event: {e}")

    async def log_device_change(
        self,
        device_type: str,
        device_id: str,
        new_state: Dict[str, Any],
        previous_state: Dict[str, Any] = None,
        changed_by: str = "system"
    ) -> None:
        """Log a device state change."""
        try:
            async with async_session() as session:
                state_record = DeviceState.record_change(
                    device_type=device_type,
                    device_id=device_id,
                    new_state=new_state,
                    previous_state=previous_state,
                    changed_by=changed_by
                )
                session.add(state_record)
                await session.commit()

        except Exception as e:
            logger.error(f"Failed to log device change: {e}")

    # ==================== Data Retrieval ====================

    async def get_sensor_history(
        self,
        sensor_type: str = "all",
        hours: int = 24,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Get sensor data history.

        Args:
            sensor_type: Filter by sensor type
            hours: Hours of history to retrieve
            limit: Maximum number of records

        Returns:
            List of sensor data dictionaries
        """
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(SensorData).where(
                    SensorData.timestamp > cutoff
                )

                if sensor_type != "all":
                    query = query.where(SensorData.sensor_type == sensor_type)

                query = query.order_by(desc(SensorData.timestamp)).limit(limit)

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get sensor history: {e}")
            return []

    async def get_temperature_trend(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get temperature trend data."""
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(
                    SensorData.timestamp,
                    SensorData.temperature
                ).where(
                    SensorData.timestamp > cutoff,
                    SensorData.temperature.isnot(None)
                ).order_by(SensorData.timestamp)

                result = await session.execute(query)
                records = result.all()

                return [
                    {"timestamp": r.timestamp.isoformat(), "value": r.temperature}
                    for r in records
                ]

        except Exception as e:
            logger.error(f"Failed to get temperature trend: {e}")
            return []

    async def get_system_logs(
        self,
        level: str = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system logs."""
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(SystemLog).where(
                    SystemLog.timestamp > cutoff
                )

                if level:
                    query = query.where(SystemLog.level == level)

                query = query.order_by(desc(SystemLog.timestamp)).limit(limit)

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get system logs: {e}")
            return []

    async def get_device_history(
        self,
        device_type: str = None,
        device_id: str = None,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get device state history."""
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                query = select(DeviceState).where(
                    DeviceState.timestamp > cutoff
                )

                if device_type:
                    query = query.where(DeviceState.device_type == device_type)
                if device_id:
                    query = query.where(DeviceState.device_id == device_id)

                query = query.order_by(desc(DeviceState.timestamp))

                result = await session.execute(query)
                records = result.scalars().all()

                return [record.to_dict() for record in records]

        except Exception as e:
            logger.error(f"Failed to get device history: {e}")
            return []

    async def get_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get data statistics for the specified period."""
        try:
            async with async_session() as session:
                cutoff = datetime.now() - timedelta(hours=hours)

                # Sensor data count
                sensor_count = await session.execute(
                    select(func.count(SensorData.id)).where(
                        SensorData.timestamp > cutoff
                    )
                )

                # Temperature statistics
                temp_stats = await session.execute(
                    select(
                        func.min(SensorData.temperature),
                        func.max(SensorData.temperature),
                        func.avg(SensorData.temperature)
                    ).where(
                        SensorData.timestamp > cutoff,
                        SensorData.temperature.isnot(None)
                    )
                )
                temp_min, temp_max, temp_avg = temp_stats.one()

                # System log counts by level
                log_counts = await session.execute(
                    select(
                        SystemLog.level,
                        func.count(SystemLog.id)
                    ).where(
                        SystemLog.timestamp > cutoff
                    ).group_by(SystemLog.level)
                )

                return {
                    "period_hours": hours,
                    "sensor_readings": sensor_count.scalar() or 0,
                    "temperature": {
                        "min": round(temp_min, 1) if temp_min else None,
                        "max": round(temp_max, 1) if temp_max else None,
                        "avg": round(temp_avg, 1) if temp_avg else None
                    },
                    "log_counts": {level: count for level, count in log_counts.all()}
                }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Global instance
data_logger = DataLogger()
