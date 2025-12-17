from sqlalchemy.orm import Session
from models import Notification

def create_notification(
    db: Session,
    farm_id: int,
    title: str,
    message: str,
    type: str,
    created_by_id: int | None = None,
):
    notification = Notification(
        farm_id=farm_id,
        title=title,
        message=message,
        type=type,
        read=False,
        created_by_id=created_by_id,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return notification
