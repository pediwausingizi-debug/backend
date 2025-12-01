# routers/dashboard.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set
import models

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


# -------------------------------------------------------------
# Helper: return validated farm user
# -------------------------------------------------------------
def get_farm_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User not assigned to a farm")

    return db_user


# -------------------------------------------------------------
# GET /dashboard/stats  (Always returns valid JSON)
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

    # ---- Counts (0 if empty) ----
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

    # ---- Finance (last 30 days) ----
    since = datetime.utcnow() - timedelta(days=30)

    txs = db.query(models.Transaction).filter(
        models.Transaction.farm_id == farm_id,
        models.Transaction.date >= since
    ).all()

    monthly_revenue = sum(float(t.amount) for t in txs if t.type == "income")
    monthly_expenses = sum(float(t.amount) for t in txs if t.type == "expense")

    result = {
        "total_livestock": total_livestock,
        "total_crops": total_crops,
        "inventory_items": inventory_items,
        "active_workers": active_workers,
        "monthly_revenue": monthly_revenue,
        "monthly_expenses": monthly_expenses,
    }

    await cache_set(cache_key, result)
    return result


# -------------------------------------------------------------
# GET /dashboard/recent-activities  (safe, even if empty)
# -------------------------------------------------------------
@router.get("/recent-activities")
async def get_recent_activities(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[dict]:

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"dashboard:recent:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    recent: List[dict] = []

    # ---- Recent Transactions ----
    txs = db.query(models.Transaction).filter(
        models.Transaction.farm_id == farm_id
    ).order_by(models.Transaction.date.desc()).limit(5).all()

    for t in txs:
        recent.append({
            "id": f"tx-{t.id}",
            "type": "finance",
            "action": f"{t.type.title()} {float(t.amount)}",
            "timestamp": t.date.isoformat(),
        })

    # ---- Recent Notifications ----
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

    # Sort by most recent
    sorted_recent = sorted(
        recent,
        key=lambda r: r["timestamp"],
        reverse=True
    )[:10]

    await cache_set(cache_key, sorted_recent)
    return sorted_recent


# -------------------------------------------------------------
# GET /dashboard/alerts  (safe JSON, empty array if none)
# -------------------------------------------------------------
@router.get("/alerts")
async def get_alerts(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> List[dict]:

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"dashboard:alerts:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    low_stock_items = db.query(models.InventoryItem).filter(
        models.InventoryItem.farm_id == farm_id,
        models.InventoryItem.reorder_level != None,
        models.InventoryItem.quantity <= models.InventoryItem.reorder_level
    ).all()

    alerts = [{
        "id": f"inv-{i.id}",
        "title": f"Low stock: {i.name}",
        "message": f"{i.quantity} remaining (reorder level {i.reorder_level})"
    } for i in low_stock_items]

    await cache_set(cache_key, alerts)
    return alerts
