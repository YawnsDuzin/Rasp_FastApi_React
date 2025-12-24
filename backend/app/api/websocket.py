"""
WebSocket API Routes
====================

WebSocket endpoints for real-time communication.
"""

from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.websocket_manager import ws_manager
from app.core.logging_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """
    Main WebSocket endpoint for real-time data.

    Supports:
    - Real-time hardware data updates
    - System metrics updates
    - Log updates
    - Topic-based subscriptions
    """
    client_id = await ws_manager.connect(websocket)

    if not client_id:
        return

    try:
        while True:
            # Wait for messages from client
            message = await websocket.receive_text()
            await ws_manager.handle_client_message(client_id, message)

    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        await ws_manager.disconnect(client_id)


@router.get("/status")
async def get_websocket_status() -> Dict[str, Any]:
    """Get WebSocket manager status."""
    return ws_manager.get_status()


@router.get("/clients")
async def get_websocket_clients() -> Dict[str, Any]:
    """Get list of connected WebSocket clients."""
    return {
        "count": ws_manager.client_count,
        "clients": ws_manager.clients
    }
