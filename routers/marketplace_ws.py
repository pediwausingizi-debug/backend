from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from collections import defaultdict
from datetime import datetime

from database import get_db
import models

router = APIRouter(tags=["marketplace-ws"])


class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(list)

    async def connect(self, conversation_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: int, websocket: WebSocket):
        if conversation_id in self.active_connections:
            if websocket in self.active_connections[conversation_id]:
                self.active_connections[conversation_id].remove(websocket)

            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]

    async def broadcast(self, conversation_id: int, message: dict):
        disconnected = []

        for connection in self.active_connections.get(conversation_id, []):
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(conversation_id, connection)


manager = ConnectionManager()


def user_in_conversation(user_id: int, conversation_id: int, db: Session) -> bool:
    return db.query(models.MarketplaceConversationParticipant).filter(
        models.MarketplaceConversationParticipant.conversation_id == conversation_id,
        models.MarketplaceConversationParticipant.user_id == user_id,
    ).first() is not None


@router.websocket("/ws/marketplace/chat/{conversation_id}/{user_id}")
async def marketplace_chat_socket(
    websocket: WebSocket,
    conversation_id: int,
    user_id: int,
    db: Session = Depends(get_db),
):
    if not user_in_conversation(user_id, conversation_id, db):
        await websocket.close(code=1008)
        return

    await manager.connect(conversation_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            content = (data.get("content") or "").strip()
            message_type = data.get("message_type") or "text"
            image_url = data.get("image_url")
            image_public_id = data.get("image_public_id")

            if not content and not image_url:
                continue

            message = models.MarketplaceMessage(
                conversation_id=conversation_id,
                sender_id=user_id,
                message_type=message_type,
                content=content,
                image_url=image_url,
                image_public_id=image_public_id,
            )

            db.add(message)

            conversation = db.query(models.MarketplaceConversation).filter(
                models.MarketplaceConversation.id == conversation_id
            ).first()

            if conversation:
                conversation.updated_at = datetime.utcnow()

            db.commit()
            db.refresh(message)

            payload = {
                "id": message.id,
                "conversation_id": message.conversation_id,
                "sender_id": message.sender_id,
                "content": message.content,
                "message_type": message.message_type,
                "image_url": message.image_url,
                "image_public_id": message.image_public_id,
                "created_at": message.created_at.isoformat() if message.created_at else None,
            }

            await manager.broadcast(conversation_id, payload)

    except WebSocketDisconnect:
        manager.disconnect(conversation_id, websocket)