"""
System API Routes
=================

REST API endpoints for system monitoring.
"""

from typing import Dict, Any
from fastapi import APIRouter

from app.services.system_monitor import system_monitor
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/metrics")
async def get_system_metrics() -> Dict[str, Any]:
    """Get current system metrics."""
    metrics = system_monitor.current
    if metrics:
        return metrics.to_dict()
    return {"error": "No metrics available"}


@router.get("/summary")
async def get_system_summary() -> Dict[str, Any]:
    """Get system status summary."""
    return system_monitor.get_summary()


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Get system health status with warnings."""
    return system_monitor.check_health()


@router.get("/platform")
async def get_platform_info() -> Dict[str, Any]:
    """Get platform information."""
    return system_monitor.get_platform_info()


@router.get("/process")
async def get_process_info() -> Dict[str, Any]:
    """Get current process information."""
    return system_monitor.get_process_info()


@router.get("/config")
async def get_config_info() -> Dict[str, Any]:
    """Get application configuration (non-sensitive)."""
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
        "simulation_mode": settings.SIMULATION_MODE,
        "hardware_update_interval": settings.HARDWARE_UPDATE_INTERVAL,
        "data_log_interval": settings.DATA_LOG_INTERVAL,
        "data_retention_days": settings.DATA_RETENTION_DAYS,
        "platform": settings.platform_info
    }
