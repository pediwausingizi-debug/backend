from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# ---------------------------------------------------------
# Helper → Load actual SQL User
# ---------------------------------------------------------
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# ---------------------------------------------------------
# GET /notifications  (uses Redis cache)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.NotificationRead])
async def list_notifications(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"notifications:list:{uid}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    notifs = (
        db.query(models.Notification)
        .filter(models.Notification.owner_id == uid)
        .order_by(models.Notification.created_at.desc())
        .all()
    )

    payload = [schemas.NotificationRead.model_validate(n).model_dump() for n in notifs]

    # Cache for 2 minutes (notifications change often)
    await cache_set(cache_key, payload, expire_seconds=120)

    return payload


# ---------------------------------------------------------
# POST /notifications  (invalidate caches)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
async def create_notification(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    notif = models.Notification(
        **payload.dict(),
        created_at=datetime.utcnow(),
        owner_id=uid
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    # Clear cache
    await cache_delete(f"notifications:list:{uid}")
    await cache_delete(f"dashboard:recent:{uid}")

    return notif


# ---------------------------------------------------------
# PUT /notifications/{id}/read  (invalidate caches)
# ---------------------------------------------------------
@router.put("/{notification_id}/read", response_model=schemas.NotificationRead)
async def mark_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    notif = db.query(models.Notification).filter(
        models.Notification.id == notification_id,
        models.Notification.owner_id == uid
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    notif.read = True
    db.commit()
    db.refresh(notif)

    # Invalidate caches
    await cache_delete(f"notifications:list:{uid}")
    await cache_delete(f"dashboard:recent:{uid}")

    return notif
