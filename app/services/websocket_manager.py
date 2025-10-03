from fastapi import WebSocket
from typing import List
import json

class WebSocketManager:
    """Manager class for WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection"""
        try:
            print(f"WebSocketManager: Accepting connection from {websocket.client}")
            await websocket.accept()
            self.active_connections.append(websocket)
            print(f"WebSocketManager: Connection accepted. Total connections: {len(self.active_connections)}")
            
            # Only log on first connection or significant changes
            if len(self.active_connections) == 1:
                print("WebSocket server ready")
            print(f"WebSocket connection accepted. Total connections: {len(self.active_connections)}")
        except Exception as e:
            print(f"Error accepting WebSocket connection: {e}")
            import traceback
            print(f"WebSocketManager: Full error traceback: {traceback.format_exc()}")
            raise
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            # Only log when no connections remain
            if len(self.active_connections) == 0:
                print("All WebSocket connections closed")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, data: dict):
        """Broadcast data to all connected WebSocket clients"""
        if not self.active_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error broadcasting to connection: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
        
        print(f"Broadcasted message to {len(self.active_connections)} connections")
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all connected clients"""
        await self.broadcast(data)
    
    def get_connection_count(self) -> int:
        """Get the number of active connections"""
        return len(self.active_connections)
