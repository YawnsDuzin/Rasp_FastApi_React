"""
Data API Routes
===============

REST API endpoints for data history and logging.
"""

from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Query

from app.services.data_logger import data_logger
from app.models.database import cleanup_old_data
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/sensors")
async def get_sensor_history(
    sensor_type: str = Query("all", description="Sensor type filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records")
) -> List[Dict[str, Any]]:
    """Get sensor data history."""
    return await data_logger.get_sensor_history(
        sensor_type=sensor_type,
        hours=hours,
        limit=limit
    )


@router.get("/temperature")
async def get_temperature_trend(
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
) -> List[Dict[str, Any]]:
    """Get temperature trend data for charts."""
    return await data_logger.get_temperature_trend(hours=hours)


@router.get("/logs")
async def get_system_logs(
    level: Optional[str] = Query(None, description="Log level filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records")
) -> List[Dict[str, Any]]:
    """Get system logs."""
    return await data_logger.get_system_logs(
        level=level,
        hours=hours,
        limit=limit
    )


@router.get("/devices")
async def get_device_history(
    device_type: Optional[str] = Query(None, description="Device type filter"),
    device_id: Optional[str] = Query(None, description="Device ID filter"),
    hours: int = Query(24, ge=1, le=168, description="Hours of history")
) -> List[Dict[str, Any]]:
    """Get device state history."""
    return await data_logger.get_device_history(
        device_type=device_type,
        device_id=device_id,
        hours=hours
    )


@router.get("/statistics")
async def get_statistics(
    hours: int = Query(24, ge=1, le=168, description="Hours for statistics")
) -> Dict[str, Any]:
    """Get data statistics."""
    return await data_logger.get_statistics(hours=hours)


@router.post("/cleanup")
async def cleanup_data(
    retention_days: int = Query(30, ge=1, le=365, description="Retention period in days")
) -> Dict[str, Any]:
    """Clean up old data."""
    deleted = await cleanup_old_data(retention_days=retention_days)
    return {
        "success": True,
        "deleted_records": deleted,
        "retention_days": retention_days
    }
