# routers/dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set, cache_delete
import models

router = APIRouter()


# Helper
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# -------------------------------------------------------------
# OPTIMIZED: /stats (5min caching)
# -------------------------------------------------------------
@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:

    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"dashboard:stats:{uid}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    # DB queries
    total_livestock = db.query(models.Livestock).filter(
        models.Livestock.owner_id == uid
    ).count()

    total_crops = db.query(models.Crop).filter(
        models.Crop.owner_id == uid
    ).count()

    inventory_items = db.query(models.InventoryItem).filter(
        models.InventoryItem.owner_id == uid
    ).count()

    active_workers = db.query(models.Worker).filter(
        models.Worker.owner_id == uid
    ).count()

    since = datetime.utcnow() - timedelta(days=30)
    txs = db.query(models.Transaction).filter(
        models.Transaction.owner_id == uid,
        models.Transaction.date >= since
    ).all()

    monthly_revenue = sum(t.amount for t in txs if t.type == "income")
    monthly_expenses = sum(t.amount for t in txs if t.type == "expense")

    result = {
        "total_livestock": total_livestock,
        "total_crops": total_crops,
        "inventory_items": inventory_items,
        "active_workers": active_workers,
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses
    }

    await cache_set(cache_key, result, expire_seconds=300)
    return result


# -------------------------------------------------------------
# OPTIMIZED: Recent activities (2min caching)
# -------------------------------------------------------------
@router.get("/recent-activities")
async def get_recent_activities(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"dashboard:recent:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    recent = []

    txs = db.query(models.Transaction).filter(
        models.Transaction.owner_id == uid
    ).order_by(models.Transaction.date.desc()).limit(5).all()

    for t in txs:
        recent.append({
            "id": f"tx-{t.id}",
            "type": "finance",
            "action": f"{t.type.title()} {t.amount}",
            "timestamp": t.date.isoformat()
        })

    notifs = db.query(models.Notification).filter(
        models.Notification.owner_id == uid
    ).order_by(models.Notification.created_at.desc()).limit(5).all()

    for n in notifs:
        recent.append({
            "id": f"n-{n.id}",
            "type": "notification",
            "action": n.title,
            "timestamp": n.created_at.isoformat()
        })

    recent_sorted = sorted(recent, key=lambda r: r["timestamp"], reverse=True)[:10]

    await cache_set(cache_key, recent_sorted, expire_seconds=120)
    return recent_sorted


# -------------------------------------------------------------
# OPTIMIZED: Alerts (2min caching)
# -------------------------------------------------------------
@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"dashboard:alerts:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    low_stock = db.query(models.InventoryItem).filter(
        models.InventoryItem.owner_id == uid,
        models.InventoryItem.reorder_level != None,
        models.InventoryItem.quantity <= models.InventoryItem.reorder_level
    ).all()

    alerts = [{
        "id": f"inv-{i.id}",
        "title": f"Low stock: {i.name}",
        "message": f"{i.quantity} remaining (reorder level {i.reorder_level})"
    } for i in low_stock]

    await cache_set(cache_key, alerts, expire_seconds=120)
    return alerts
