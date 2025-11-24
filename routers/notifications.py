from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.NotificationRead])
def list_notifications(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    notifs = db.query(models.Notification).filter(models.Notification.owner_id == current_user.id).order_by(models.Notification.created_at.desc()).all()
    return notifs


@router.post("/", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(payload: schemas.NotificationCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    notif = models.Notification(**payload.dict(), created_at=datetime.utcnow(), owner_id=current_user.id)
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif


@router.put("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_as_read(notification_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id, models.Notification.owner_id == current_user.id).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    notif.read = True
    db.commit()
    db.refresh(notif)
    return notif
