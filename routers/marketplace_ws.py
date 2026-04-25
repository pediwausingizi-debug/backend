from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from collections import defaultdict

from database import get_db
import models

router = APIRouter(tags=["marketplace-ws"])


class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(list)  # {conversation_id: [websocket, ...]}

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)

    async def broadcast(self, conversation_id: int, message: dict):
        for connection in self.active_connections[conversation_id]:
            await connection.send_json(message)


manager = ConnectionManager()


@router.websocket("/ws/marketplace/chat/{conversation_id}/{user_id}")
async def marketplace_chat_socket(
    websocket: WebSocket,
    conversation_id: int,
    user_id: int,
):
    await manager.connect(conversation_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            payload = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "content": data.get("content", ""),
                "message_type": data.get("message_type", "text"),
                "image_url": data.get("image_url"),
                "created_at": data.get("created_at"),
            }

            await manager.broadcast(conversation_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)