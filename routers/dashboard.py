from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set
import models

router = APIRouter(
    prefix="",
    tags=["dashboard"]
)


# -------------------------------------------------------------
# Helper: return validated farm user
# -------------------------------------------------------------
def get_farm_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User not assigned to a farm")

    return db_user


# -------------------------------------------------------------
# GET /dashboard/stats
# Matches frontend DashboardStats
# NOTE:
# total_livestock now counts INDIVIDUAL animals for consistency
# with the AI dashboard summary
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

    total_livestock = (
        db.query(models.Animal)
        .filter(models.Animal.farm_id == farm_id)
        .count()
    )

    total_crops = (
        db.query(models.Crop)
        .filter(models.Crop.farm_id == farm_id)
        .count()
    )

    inventory_items = (
        db.query(models.InventoryItem)
        .filter(models.InventoryItem.farm_id == farm_id)
        .count()
    )

    active_workers = (
        db.query(models.User)
        .filter(
            models.User.farm_id == farm_id,
            models.User.role.in_(["Manager", "Worker"])
        )
        .count()
    )

    since = datetime.utcnow() - timedelta(days=30)

    txs = (
        db.query(models.Transaction)
        .filter(
            models.Transaction.farm_id == farm_id,
            models.Transaction.date >= since
        )
        .all()
    )

    monthly_revenue = sum(
        float(t.amount or 0)
        for t in txs
        if (t.type or "").lower() == "income"
    )

    monthly_expenses = sum(
        float(t.amount or 0)
        for t in txs
        if (t.type or "").lower() == "expense"
    )

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
# GET /dashboard/recent-activities
# Matches frontend ActivityItem
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

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .order_by(models.Transaction.date.desc())
        .limit(5)
        .all()
    )

    for t in txs:
        recent.append({
            "id": f"tx-{t.id}",
            "type": "finance",
            "action": f"{(t.type or 'transaction').title()} {float(t.amount or 0):.2f}",
            "timestamp": t.date.isoformat() if t.date else datetime.utcnow().isoformat(),
        })

    notifs = (
        db.query(models.Notification)
        .filter(models.Notification.farm_id == farm_id)
        .order_by(models.Notification.created_at.desc())
        .limit(5)
        .all()
    )

    for n in notifs:
        recent.append({
            "id": f"n-{n.id}",
            "type": "notification",
            "action": n.title,
            "timestamp": n.created_at.isoformat() if n.created_at else datetime.utcnow().isoformat(),
        })

    sorted_recent = sorted(
        recent,
        key=lambda r: r["timestamp"],
        reverse=True
    )[:10]

    await cache_set(cache_key, sorted_recent)
    return sorted_recent


# -------------------------------------------------------------
# GET /dashboard/alerts
# Matches frontend AlertItem:
# { id, title, subtitle?, type? }
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

    alerts: List[dict] = []

    # ---------------------------------------------------------
    # Inventory low-stock alerts
    # ---------------------------------------------------------
    low_stock = (
        db.query(models.InventoryItem)
        .filter(
            models.InventoryItem.farm_id == farm_id,
            models.InventoryItem.reorder_level.isnot(None),
            models.InventoryItem.quantity <= models.InventoryItem.reorder_level
        )
        .all()
    )

    for item in low_stock:
        alerts.append({
            "id": f"inv-{item.id}",
            "title": f"Low stock: {item.name}",
            "subtitle": f"{item.quantity} remaining (reorder level {item.reorder_level})",
            "type": "inventory",
        })

    # ---------------------------------------------------------
    # Individual animal health alerts
    # ---------------------------------------------------------
    animals = (
        db.query(models.Animal)
        .filter(models.Animal.farm_id == farm_id)
        .all()
    )

    for animal in animals:
        status = (animal.health_status or "").strip().lower()
        if status and status not in ["healthy", "normal"]:
            display_name = animal.name or animal.tag_number or animal.type or f"Animal #{animal.id}"
            alerts.append({
                "id": f"animal-{animal.id}",
                "title": f"Animal health attention: {display_name}",
                "subtitle": f"Current health status is '{animal.health_status}'",
                "type": "livestock",
            })

    # ---------------------------------------------------------
    # Crop alerts from base crop records nearing expected harvest
    # ---------------------------------------------------------
    upcoming_days = 7
    now = datetime.utcnow()

    crops = (
        db.query(models.Crop)
        .filter(models.Crop.farm_id == farm_id)
        .all()
    )

    for crop in crops:
        if crop.expected_harvest:
            delta_days = (crop.expected_harvest - now).days
            if 0 <= delta_days <= upcoming_days:
                alerts.append({
                    "id": f"crop-{crop.id}",
                    "title": f"Harvest approaching: {crop.name}",
                    "subtitle": f"Expected harvest in {delta_days} day(s)",
                    "type": "crop",
                })

    await cache_set(cache_key, alerts)
    return alerts