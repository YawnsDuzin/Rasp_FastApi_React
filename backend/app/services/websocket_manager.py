"""
WebSocket Manager
=================

Manages WebSocket connections for real-time data push.
Handles multiple clients and message broadcasting.
"""

import asyncio
import json
from typing import Dict, Any, List, Set, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class ClientInfo:
    """Information about a connected WebSocket client."""
    id: str
    websocket: WebSocket
    connected_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    subscriptions: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "connected_at": self.connected_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "subscriptions": list(self.subscriptions)
        }


class WebSocketManager:
    """
    Manager for WebSocket connections.

    Features:
    - Multiple client connections
    - Topic-based subscriptions
    - Automatic heartbeat/ping
    - Message broadcasting
    - Connection health monitoring
    """

    def __init__(self):
        self._clients: Dict[str, ClientInfo] = {}
        self._client_counter = 0
        self._max_connections = settings.WS_MAX_CONNECTIONS
        self._heartbeat_interval = settings.WS_HEARTBEAT_INTERVAL
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

        # Available topics for subscription
        self._topics = {
            "hardware": True,      # Hardware data updates
            "system": True,        # System metrics updates
            "logs": True,          # System log updates
            "all": True            # All updates
        }

    @property
    def client_count(self) -> int:
        """Get number of connected clients."""
        return len(self._clients)

    @property
    def clients(self) -> List[Dict[str, Any]]:
        """Get list of connected clients."""
        return [client.to_dict() for client in self._clients.values()]

    async def start(self) -> None:
        """Start the WebSocket manager."""
        if self._running:
            return

        self._running = True
        self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        logger.info("WebSocket manager started")

    async def stop(self) -> None:
        """Stop the WebSocket manager."""
        self._running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all connections
        for client_id in list(self._clients.keys()):
            await self.disconnect(client_id)

        logger.info("WebSocket manager stopped")

    async def connect(self, websocket: WebSocket) -> Optional[str]:
        """
        Accept a new WebSocket connection.

        Args:
            websocket: FastAPI WebSocket instance

        Returns:
            Client ID if connected, None if rejected
        """
        if len(self._clients) >= self._max_connections:
            logger.warning("WebSocket connection rejected: max connections reached")
            await websocket.close(code=1013, reason="Max connections reached")
            return None

        await websocket.accept()

        self._client_counter += 1
        client_id = f"client_{self._client_counter}"

        self._clients[client_id] = ClientInfo(
            id=client_id,
            websocket=websocket,
            subscriptions={"all"}  # Default subscription
        )

        logger.info(f"WebSocket client connected: {client_id}")

        # Send welcome message
        await self.send_to_client(client_id, {
            "type": "connected",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        })

        return client_id

    async def disconnect(self, client_id: str) -> None:
        """Disconnect a client."""
        if client_id not in self._clients:
            return

        client = self._clients.pop(client_id)

        try:
            if client.websocket.client_state == WebSocketState.CONNECTED:
                await client.websocket.close()
        except Exception as e:
            logger.debug(f"Error closing websocket: {e}")

        logger.info(f"WebSocket client disconnected: {client_id}")

    async def send_to_client(self, client_id: str, data: Dict[str, Any]) -> bool:
        """
        Send data to a specific client.

        Args:
            client_id: Target client ID
            data: Data to send

        Returns:
            True if sent successfully
        """
        if client_id not in self._clients:
            return False

        client = self._clients[client_id]

        try:
            await client.websocket.send_json(data)
            return True
        except Exception as e:
            logger.error(f"Failed to send to client {client_id}: {e}")
            await self.disconnect(client_id)
            return False

    async def broadcast(self, data: Dict[str, Any], topic: str = "all") -> int:
        """
        Broadcast data to all subscribed clients.

        Args:
            data: Data to broadcast
            topic: Topic for filtering subscribers

        Returns:
            Number of clients that received the message
        """
        sent_count = 0
        data["topic"] = topic
        data["broadcast_time"] = datetime.now().isoformat()

        for client_id, client in list(self._clients.items()):
            # Check if client is subscribed to this topic
            if topic in client.subscriptions or "all" in client.subscriptions:
                if await self.send_to_client(client_id, data):
                    sent_count += 1

        return sent_count

    async def broadcast_hardware_data(self, data: Dict[str, Any]) -> int:
        """Broadcast hardware data update."""
        return await self.broadcast({
            "type": "hardware_update",
            "data": data
        }, topic="hardware")

    async def broadcast_system_metrics(self, metrics: Dict[str, Any]) -> int:
        """Broadcast system metrics update."""
        return await self.broadcast({
            "type": "system_update",
            "data": metrics
        }, topic="system")

    async def broadcast_log(self, log_entry: Dict[str, Any]) -> int:
        """Broadcast log entry."""
        return await self.broadcast({
            "type": "log_update",
            "data": log_entry
        }, topic="logs")

    async def handle_client_message(self, client_id: str, message: str) -> None:
        """
        Handle incoming message from a client.

        Supported commands:
        - subscribe: Subscribe to topics
        - unsubscribe: Unsubscribe from topics
        - ping: Heartbeat ping
        """
        if client_id not in self._clients:
            return

        client = self._clients[client_id]

        try:
            data = json.loads(message)
            msg_type = data.get("type", "")

            if msg_type == "subscribe":
                topics = data.get("topics", [])
                for topic in topics:
                    if topic in self._topics:
                        client.subscriptions.add(topic)
                await self.send_to_client(client_id, {
                    "type": "subscribed",
                    "topics": list(client.subscriptions)
                })

            elif msg_type == "unsubscribe":
                topics = data.get("topics", [])
                for topic in topics:
                    client.subscriptions.discard(topic)
                await self.send_to_client(client_id, {
                    "type": "unsubscribed",
                    "topics": list(client.subscriptions)
                })

            elif msg_type == "ping":
                client.last_heartbeat = datetime.now()
                await self.send_to_client(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })

            else:
                logger.debug(f"Unknown message type from {client_id}: {msg_type}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from client {client_id}")
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")

    async def _heartbeat_loop(self) -> None:
        """Background loop for sending heartbeat pings."""
        while self._running:
            try:
                now = datetime.now()

                for client_id, client in list(self._clients.items()):
                    # Check if client is responsive
                    time_since_heartbeat = (now - client.last_heartbeat).total_seconds()

                    if time_since_heartbeat > self._heartbeat_interval * 2:
                        # Client hasn't responded, disconnect
                        logger.warning(f"Client {client_id} timed out")
                        await self.disconnect(client_id)
                    else:
                        # Send ping
                        await self.send_to_client(client_id, {
                            "type": "ping",
                            "timestamp": now.isoformat()
                        })

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Heartbeat loop error: {e}")

            await asyncio.sleep(self._heartbeat_interval)

    def get_status(self) -> Dict[str, Any]:
        """Get WebSocket manager status."""
        return {
            "running": self._running,
            "client_count": len(self._clients),
            "max_connections": self._max_connections,
            "clients": self.clients,
            "topics": list(self._topics.keys())
        }


# Global instance
ws_manager = WebSocketManager()
