"""
API Routes
==========

FastAPI router definitions for the HMI API.
"""

from fastapi import APIRouter

from .hardware import router as hardware_router
from .system import router as system_router
from .data import router as data_router
from .websocket import router as websocket_router

# Main API router
api_router = APIRouter()

# Include sub-routers
api_router.include_router(hardware_router, prefix="/hardware", tags=["Hardware"])
api_router.include_router(system_router, prefix="/system", tags=["System"])
api_router.include_router(data_router, prefix="/data", tags=["Data"])
api_router.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])

__all__ = ["api_router"]
