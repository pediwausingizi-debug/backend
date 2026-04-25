from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(
    prefix="",
    tags=["marketplace-chat"]
)


def get_db_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


def user_in_conversation(user_id: int, conversation_id: int, db: Session) -> bool:
    return db.query(models.MarketplaceConversationParticipant).filter(
        models.MarketplaceConversationParticipant.conversation_id == conversation_id,
        models.MarketplaceConversationParticipant.user_id == user_id
    ).first() is not None


# ---------------------------------------------------------
# LIST MY CONVERSATIONS
# ---------------------------------------------------------
@router.get("/conversations", response_model=List[schemas.MarketplaceConversationRead])
async def list_my_conversations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    conversations = (
        db.query(models.MarketplaceConversation)
        .join(
            models.MarketplaceConversationParticipant,
            models.MarketplaceConversationParticipant.conversation_id == models.MarketplaceConversation.id
        )
        .filter(models.MarketplaceConversationParticipant.user_id == db_user.id)
        .order_by(models.MarketplaceConversation.updated_at.desc())
        .all()
    )

    return [schemas.MarketplaceConversationRead.model_validate(c) for c in conversations]


# ---------------------------------------------------------
# CREATE OR FETCH CONVERSATION
# ---------------------------------------------------------
@router.post("/conversations/bootstrap", response_model=schemas.MarketplaceConversationRead)
async def bootstrap_conversation(
    payload: schemas.MarketplaceChatBootstrap,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    if not payload.participant_user_id:
        raise HTTPException(status_code=400, detail="participant_user_id is required")

    if payload.participant_user_id == db_user.id:
        raise HTTPException(status_code=400, detail="Cannot create conversation with yourself")

    # try existing conversation for listing + same two users
    if payload.listing_id:
        existing = (
            db.query(models.MarketplaceConversation)
            .filter(
                models.MarketplaceConversation.listing_id == payload.listing_id,
                models.MarketplaceConversation.conversation_type == "listing"
            )
            .all()
        )

        for conv in existing:
            participant_ids = {
                p.user_id for p in conv.participants
            }
            if {db_user.id, payload.participant_user_id}.issubset(participant_ids):
                return schemas.MarketplaceConversationRead.model_validate(conv)

    conversation = models.MarketplaceConversation(
        conversation_type="listing" if payload.listing_id else "request" if payload.request_id else "direct",
        title=payload.title,
        listing_id=payload.listing_id,
        request_id=payload.request_id,
        created_by_id=db_user.id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    participants = [
        models.MarketplaceConversationParticipant(
            conversation_id=conversation.id,
            user_id=db_user.id,
        ),
        models.MarketplaceConversationParticipant(
            conversation_id=conversation.id,
            user_id=payload.participant_user_id,
        )
    ]

    db.add_all(participants)
    db.commit()
    db.refresh(conversation)

    return schemas.MarketplaceConversationRead.model_validate(conversation)


# ---------------------------------------------------------
# GET CONVERSATION MESSAGES
# ---------------------------------------------------------
@router.get("/conversations/{conversation_id}/messages", response_model=List[schemas.MarketplaceMessageRead])
async def get_conversation_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    if not user_in_conversation(db_user.id, conversation_id, db):
        raise HTTPException(status_code=403, detail="Not allowed in this conversation")

    messages = (
        db.query(models.MarketplaceMessage)
        .filter(models.MarketplaceMessage.conversation_id == conversation_id)
        .order_by(models.MarketplaceMessage.created_at.asc())
        .all()
    )

    return [schemas.MarketplaceMessageRead.model_validate(m) for m in messages]


# ---------------------------------------------------------
# SEND MESSAGE (HTTP fallback / history persistence)
# ---------------------------------------------------------
@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=schemas.MarketplaceMessageRead,
    status_code=status.HTTP_201_CREATED
)
async def send_message(
    conversation_id: int,
    payload: schemas.MarketplaceMessageCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    if not user_in_conversation(db_user.id, conversation_id, db):
        raise HTTPException(status_code=403, detail="Not allowed in this conversation")

    message = models.MarketplaceMessage(
        conversation_id=conversation_id,
        sender_id=db_user.id,
        message_type=payload.message_type or "text",
        content=payload.content,
        image_url=payload.image_url,
        image_public_id=payload.image_public_id,
    )

    db.add(message)

    conversation = db.query(models.MarketplaceConversation).filter(
        models.MarketplaceConversation.id == conversation_id
    ).first()

    if conversation:
        conversation.updated_at = message.created_at

    db.commit()
    db.refresh(message)

    return schemas.MarketplaceMessageRead.model_validate(message)