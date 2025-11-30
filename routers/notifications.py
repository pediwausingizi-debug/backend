# routers/notifications.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# ---------------------------------------------------------
# Helper → Load user & ensure they belong to a farm
# ---------------------------------------------------------
def get_farm_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to a farm")

    return db_user


# ---------------------------------------------------------
# GET /notifications (farm-wide, cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.NotificationRead])
async def list_notifications(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"notifications:list:farm:{farm_id}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    notifications = (
        db.query(models.Notification)
        .filter(models.Notification.farm_id == farm_id)
        .order_by(models.Notification.created_at.desc())
        .all()
    )

    payload = [
        schemas.NotificationRead.model_validate(n).model_dump()
        for n in notifications
    ]

    await cache_set(cache_key, payload, expire_seconds=120)
    return notifications


# ---------------------------------------------------------
# POST /notifications (Admin or Manager)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    if db_user.role not in ["Admin", "Manager"]:
        raise HTTPException(status_code=403, detail="Only Admin/Manager can create notifications")

    notif = models.Notification(
        **payload.dict(),
        farm_id=farm_id,
        created_by=db_user.id,
        created_at=datetime.utcnow(),
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    await cache_delete(f"notifications:list:farm:{farm_id}")
    await cache_delete(f"dashboard:recent:farm:{farm_id}")

    return notif


# ---------------------------------------------------------
# PUT /notifications/{id}/read
# (Each user marks as read individually → per-user table needed)
# ---------------------------------------------------------

@router.put("/{notification_id}/read", response_model=schemas.NotificationRead)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    IMPORTANT NOTE:
    If notifications are shared farm-wide,
    and you want INDIVIDUAL users to mark as read,
    you need a NotificationReadStatus table.

    For now this marks the base record, meaning:
        "when one user marks as read, everyone sees it as read."
    """

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.farm_id == farm_id
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    db.commit()
    db.refresh(notif)

    await cache_delete(f"notifications:list:farm:{farm_id}")
    await cache_delete(f"dashboard:recent:farm:{farm_id}")

    return notif
