from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from utils.auth_utils import get_current_user
from utils.plan_limits import get_subscription_status
import models
import schemas

router = APIRouter(
    prefix="",
    tags=["subscriptions"]
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


@router.get("/status", response_model=schemas.SubscriptionStatusRead)
async def subscription_status(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    # Auto-expire Pro if date has passed
    if (
        db_user.plan == "pro"
        and db_user.subscription_status == "active"
        and db_user.subscription_expires_at
        and db_user.subscription_expires_at < datetime.utcnow()
    ):
        db_user.plan = "free"
        db_user.subscription_status = "expired"
        db.commit()
        db.refresh(db_user)

    return get_subscription_status(db_user)