# routers/dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set
import models

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# Helper – get actual User + farm_id
def get_farm_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User not assigned to a farm")
    return db_user


# -------------------------------------------------------------
# DASHBOARD STATS (farm-wide)
# -------------------------------------------------------------
@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"dashboard:stats:farm:{farm_id}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    # FARM-WIDE QUERIES
    total_livestock = db.query(models.Livestock).filter(
        models.Livestock.farm_id == farm_id
    ).count()

    total_crops = db.query(models.Crop).filter(
        models.Crop.farm_id == farm_id
    ).count()

    inventory_items = db.query(models.InventoryItem).filter(
        models.InventoryItem.farm_id == farm_id
    ).count()

    active_workers = db.query(models.User).filter(
        models.User.farm_id == farm_id,
        models.User.role.in_(["Manager", "Worker"])
    ).count()

    since = datetime.utcnow() - timedelta(days=30)
    txs = db.query(models.Transaction).filter(
        models.Transaction.farm_id == farm_id,
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
        "monthly_expenses": monthly_expenses,
    }

    await cache_set(cache_key, result, expire_seconds=300)
    return result


# -------------------------------------------------------------
# RECENT ACTIVITIES (farm-wide 2 min cache)
# -------------------------------------------------------------
@router.get("/recent-activities")
async def get_recent_activities(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"dashboard:recent:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    recent = []

    # Latest transactions
    txs = db.query(models.Transaction).filter(
        models.Transaction.farm_id == farm_id
    ).order_by(models.Transaction.date.desc()).limit(5).all()

    for t in txs:
        recent.append({
            "id": f"tx-{t.id}",
            "type": "finance",
            "action": f"{t.type.title()} {t.amount}",
            "timestamp": t.date.isoformat(),
        })

    # Latest notifications
    notifs = db.query(models.Notification).filter(
        models.Notification.farm_id == farm_id
    ).order_by(models.Notification.created_at.desc()).limit(5).all()

    for n in notifs:
        recent.append({
            "id": f"n-{n.id}",
            "type": "notification",
            "action": n.title,
            "timestamp": n.created_at.isoformat(),
        })

    recent_sorted = sorted(recent, key=lambda r: r["timestamp"], reverse=True)[:10]

    await cache_set(cache_key, recent_sorted, expire_seconds=120)
    return recent_sorted


# -------------------------------------------------------------
# ALERTS: Low inventory warnings (farm-wide)
# -------------------------------------------------------------
@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"dashboard:alerts:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    low_stock = db.query(models.InventoryItem).filter(
        models.InventoryItem.farm_id == farm_id,
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
