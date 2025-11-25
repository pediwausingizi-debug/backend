from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to load actual SQLAlchemy User
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[schemas.NotificationRead])
def list_notifications(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    notifs = (
        db.query(models.Notification)
        .filter(models.Notification.owner_id == db_user.id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )
    return notifs


@router.post("/", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    notif = models.Notification(
        **payload.dict(),
        created_at=datetime.utcnow(),
        owner_id=db_user.id
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    return notif


@router.put("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.owner_id == db_user.id
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    db.commit()
    db.refresh(notif)

    return notif
