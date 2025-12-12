from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set
from database import get_db
from utils.auth_utils import get_current_user
import models

# ✅ FIX — Add prefix="" so the main include_router prefix works
router = APIRouter(
    prefix="",
    tags=["reports"]
)


# -------------------------------------------------------------
# Helper → fetch full SQL user + farm
# -------------------------------------------------------------
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User is not assigned to a farm")

    return db_user


# -------------------------------------------------------------
# LIVESTOCK REPORT  →  /api/reports/livestock
# -------------------------------------------------------------
@router.get("/livestock")
async def get_livestock_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"report:livestock:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items = db.query(models.Livestock).filter(
        models.Livestock.farm_id == farm_id
    ).all()

    total_count = sum((i.quantity or 0) for i in items)

    by_type = {}
    health_summary = {"healthy": 0, "sick": 0, "treatment": 0}

    for livestock in items:
        qty = livestock.quantity or 0
        by_type[livestock.type] = by_type.get(livestock.type, 0) + qty

        status = (livestock.health_status or "").lower()
        if status == "healthy":
            health_summary["healthy"] += qty
        elif status == "sick":
            health_summary["sick"] += qty
        else:
            health_summary["treatment"] += qty

    payload = {
        "total_count": total_count,
        "by_type": by_type,
        "health_summary": health_summary,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# CROPS REPORT  →  /api/reports/crops
# -------------------------------------------------------------
@router.get("/crops")
async def get_crops_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"report:crops:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crops = db.query(models.Crop).filter(
        models.Crop.farm_id == farm_id
    ).all()

    total_area = sum((c.area_hectares or 0) for c in crops)

    by_crop = {}
    harvest_summary = {"completed": 0, "pending": 0}

    for crop in crops:
        area = crop.area_hectares or 0
        by_crop[crop.name] = by_crop.get(crop.name, 0) + area

        status = (crop.status or "").lower()
        if status == "completed":
            harvest_summary["completed"] += 1
        else:
            harvest_summary["pending"] += 1

    payload = {
        "total_area": total_area,
        "by_crop": by_crop,
        "harvest_summary": harvest_summary,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# FINANCIAL REPORT  →  /api/reports/financial
# -------------------------------------------------------------
@router.get("/financial")
async def get_financial_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"report:financial:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    transactions = db.query(models.Transaction).filter(
        models.Transaction.farm_id == farm_id
    ).all()

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expenses = sum(t.amount for t in transactions if t.type == "expense")
    net_profit = total_income - total_expenses

    by_category = {}
    for t in transactions:
        cat = t.category or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + (t.amount or 0)

    payload = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "by_category": by_category,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# INVENTORY REPORT  →  /api/reports/inventory
# -------------------------------------------------------------
@router.get("/inventory")
async def get_inventory_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"report:inventory:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.farm_id == farm_id
    ).all()

    total_items = len(items)
    low_stock_items = len([
        i for i in items
        if i.reorder_level is not None and (i.quantity or 0) <= (i.reorder_level or 0)
    ])
    out_of_stock = len([i for i in items if (i.quantity or 0) == 0])
    total_value = sum((i.quantity or 0) for i in items)

    payload = {
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,
        "total_value": total_value,
    }

    await cache_set(cache_key, payload, 300)
    return payload
