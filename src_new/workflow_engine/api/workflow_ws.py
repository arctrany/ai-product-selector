"""WebSocket connection management for workflow events."""

import json
from typing import Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from .dependencies import engine_dependency
from ..core.engine import WorkflowEngine
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for workflow events."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, thread_id: str):
        """Accept WebSocket connection and store it."""
        await websocket.accept()
        self.active_connections[thread_id] = websocket
        logger.info(f"WebSocket connected for thread: {thread_id}")
    
    def disconnect(self, thread_id: str):
        """Remove WebSocket connection."""
        if thread_id in self.active_connections:
            del self.active_connections[thread_id]
            logger.info(f"WebSocket disconnected for thread: {thread_id}")
    
    async def send_message(self, thread_id: str, message: Dict[str, Any]):
        """Send message to specific WebSocket connection."""
        if thread_id in self.active_connections:
            try:
                await self.active_connections[thread_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
                self.disconnect(thread_id)
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all active connections."""
        disconnected = []
        for thread_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to {thread_id}: {e}")
                disconnected.append(thread_id)
        
        # Clean up disconnected connections
        for thread_id in disconnected:
            self.disconnect(thread_id)
    
    def get_connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.active_connections)
    
    def get_connected_threads(self) -> list:
        """Get list of connected thread IDs."""
        return list(self.active_connections.keys())

# Global connection manager instance
connection_manager = ConnectionManager()

def create_websocket_router() -> APIRouter:
    """Create WebSocket routes."""
    router = APIRouter(tags=["websocket"])

    @router.websocket("/runs/{thread_id}/events")
    async def workflow_events(
        websocket: WebSocket,
        thread_id: str,
        engine: WorkflowEngine = Depends(engine_dependency)
    ):
        """WebSocket endpoint for real-time workflow events."""
        await connection_manager.connect(websocket, thread_id)
        
        try:
            # Send initial connection confirmation
            await connection_manager.send_message(thread_id, {
                "type": "connection",
                "status": "connected",
                "thread_id": thread_id,
                "timestamp": "2025-10-23T13:54:00Z"
            })
            
            # Send current workflow status if available
            try:
                status = engine.get_workflow_status(thread_id)
                if status:
                    await connection_manager.send_message(thread_id, {
                        "type": "status",
                        "data": status,
                        "timestamp": "2025-10-23T13:54:00Z"
                    })
            except Exception as e:
                logger.warning(f"Could not get initial status for {thread_id}: {e}")
            
            # Keep connection alive and listen for messages
            while True:
                try:
                    data = await websocket.receive_text()
                    
                    # Parse client message
                    try:
                        client_message = json.loads(data)
                        message_type = client_message.get("type", "unknown")
                        
                        # Handle different message types
                        if message_type == "ping":
                            await connection_manager.send_message(thread_id, {
                                "type": "pong",
                                "timestamp": "2025-10-23T13:54:00Z"
                            })
                        elif message_type == "status_request":
                            try:
                                status = engine.get_workflow_status(thread_id)
                                await connection_manager.send_message(thread_id, {
                                    "type": "status",
                                    "data": status,
                                    "timestamp": "2025-10-23T13:54:00Z"
                                })
                            except Exception as e:
                                await connection_manager.send_message(thread_id, {
                                    "type": "error",
                                    "message": f"Failed to get status: {str(e)}",
                                    "timestamp": "2025-10-23T13:54:00Z"
                                })
                        else:
                            # Echo back unknown messages
                            await connection_manager.send_message(thread_id, {
                                "type": "echo",
                                "data": client_message,
                                "timestamp": "2025-10-23T13:54:00Z"
                            })
                    
                    except json.JSONDecodeError:
                        await connection_manager.send_message(thread_id, {
                            "type": "error",
                            "message": "Invalid JSON message",
                            "timestamp": "2025-10-23T13:54:00Z"
                        })
                
                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"WebSocket error for {thread_id}: {e}")
                    break
        
        except Exception as e:
            logger.error(f"WebSocket connection error for {thread_id}: {e}")
        finally:
            connection_manager.disconnect(thread_id)

    @router.get("/ws/stats")
    async def websocket_stats():
        """Get WebSocket connection statistics."""
        return {
            "active_connections": connection_manager.get_connection_count(),
            "connected_threads": connection_manager.get_connected_threads()
        }

    return router

def get_connection_manager() -> ConnectionManager:
    """Get the global connection manager instance."""
    return connection_manager