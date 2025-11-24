from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime, timedelta

from database import get_db
from utils import get_current_user
import models

router = APIRouter()


@router.get("/stats")
def get_dashboard_stats(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)) -> Dict[str, Any]:
    total_livestock = db.query(models.Livestock).filter(models.Livestock.owner_id == current_user.id).count()
    total_crops = db.query(models.Crop).filter(models.Crop.owner_id == current_user.id).count()
    inventory_items = db.query(models.InventoryItem).filter(models.InventoryItem.owner_id == current_user.id).count()
    active_workers = db.query(models.Worker).filter(models.Worker.owner_id == current_user.id).count()

    # Example: aggregate last 30 days
    since = datetime.utcnow() - timedelta(days=30)
    txs = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id, models.Transaction.date >= since).all()

    monthly_revenue = sum(t.amount for t in txs if t.type == "income")
    monthly_expenses = sum(t.amount for t in txs if t.type == "expense")

    return {
        "total_livestock": total_livestock,
        "total_crops": total_crops,
        "inventory_items": inventory_items,
        "active_workers": active_workers,
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses
    }


@router.get("/recent-activities")
def get_recent_activities(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    recent = []
    txs = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).order_by(models.Transaction.date.desc()).limit(5).all()
    for t in txs:
        recent.append({"id": f"tx-{t.id}", "type": "finance", "action": f"{t.type.title()} {t.amount}", "timestamp": t.date.isoformat()})
    notifs = db.query(models.Notification).filter(models.Notification.owner_id == current_user.id).order_by(models.Notification.created_at.desc()).limit(5).all()
    for n in notifs:
        recent.append({"id": f"n-{n.id}", "type": "notification", "action": n.title, "timestamp": n.created_at.isoformat()})
    recent_sorted = sorted(recent, key=lambda r: r["timestamp"], reverse=True)[:10]
    return recent_sorted


@router.get("/alerts")
def get_alerts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Example alert: low-stock items
    low_stock = db.query(models.InventoryItem).filter(models.InventoryItem.owner_id == current_user.id, models.InventoryItem.reorder_level != None, models.InventoryItem.quantity <= models.InventoryItem.reorder_level).all()
    alerts = []
    for i in low_stock:
        alerts.append({"id": f"inv-{i.id}", "title": f"Low stock: {i.name}", "message": f"{i.quantity} remaining (reorder level {i.reorder_level})"})
    return alerts
