from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models
import schemas

router = APIRouter(
    prefix="",
    tags=["notifications"]
)


# ---------------------------------------------------------
# Helper → Load user & ensure they belong to a farm
# ---------------------------------------------------------
def get_farm_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to a farm")

    return db_user


# ---------------------------------------------------------
# Internal helper used by other routers
# Example: workers.py can call create_notification(...)
# ---------------------------------------------------------
def create_notification(
    db: Session,
    title: str,
    message: str,
    user_id: Optional[int] = None,
    type: str = "info",
    notification_type: Optional[str] = None,
    farm_id: Optional[int] = None,
    created_by_id: Optional[int] = None,
):
    """
    Internal helper for creating notifications from other routers.

    Supports:
    - type="worker"
    - notification_type="worker"
    - calls with user_id
    - calls without user_id but with created_by_id
    """

    final_type = notification_type or type or "info"
    final_user_id = user_id or created_by_id

    if final_user_id is None:
        raise ValueError("create_notification requires user_id or created_by_id")

    if farm_id is None:
        user = db.query(models.User).filter(models.User.id == final_user_id).first()
        if user:
            farm_id = user.farm_id

    notif = models.Notification(
        user_id=final_user_id,
        farm_id=farm_id,
        title=title,
        message=message,
        type=final_type,
        read=False,
        created_by_id=created_by_id,
        created_at=datetime.utcnow(),
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    return notif


# ---------------------------------------------------------
# GET /notifications/
# Matches frontend Notification[]
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.NotificationRead])
async def list_notifications(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
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

    serialized = [
        schemas.NotificationRead.model_validate(n).model_dump(mode="json")
        for n in notifications
    ]

    await cache_set(cache_key, serialized, expire_seconds=120)
    return serialized


# ---------------------------------------------------------
# POST /notifications/
# API endpoint for creating notifications manually
# ---------------------------------------------------------
@router.post(
    "/",
    response_model=schemas.NotificationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_notification_endpoint(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    if db_user.role not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin/Manager can create notifications",
        )

    data = payload.model_dump(exclude_unset=True)

    notif = models.Notification(
        **data,
        farm_id=farm_id,
        created_by_id=db_user.id,
        created_at=datetime.utcnow(),
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    await cache_delete(f"notifications:list:farm:{farm_id}")
    await cache_delete(f"dashboard:recent:farm:{farm_id}")

    return schemas.NotificationRead.model_validate(notif)


# ---------------------------------------------------------
# PUT /notifications/{id}/read
# ---------------------------------------------------------
@router.put("/{notification_id}/read", response_model=schemas.NotificationRead)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    notif = (
        db.query(models.Notification)
        .filter(
            models.Notification.id == notification_id,
            models.Notification.farm_id == farm_id,
        )
        .first()
    )

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True

    db.commit()
    db.refresh(notif)

    await cache_delete(f"notifications:list:farm:{farm_id}")
    await cache_delete(f"dashboard:recent:farm:{farm_id}")

    return schemas.NotificationRead.model_validate(notif)