from sqlalchemy.orm import Session
from models import Notification


def save_notification(
    db: Session,
    farm_id: int,
    title: str,
    message: str,
    notif_type: str = "system",
):
    """
    Save a notification to the database
    """
    notification = Notification(
        farm_id=farm_id,
        title=title,
        message=message,
        type=notif_type,
        read=False,
    )

    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification
