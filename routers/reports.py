from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils import get_current_user
import models

router = APIRouter()


# Helper → fetch SQL user instance
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# -------------------------------------------------------------
# LIVESTOCK REPORT  (cached)
# -------------------------------------------------------------
@router.get("/livestock")
async def get_livestock_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"report:livestock:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items = db.query(models.Livestock).filter(
        models.Livestock.owner_id == uid
    ).all()

    total_count = sum(i.quantity for i in items)
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
        "health_summary": health_summary
    }

    # cache for 5min
    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# CROPS REPORT  (cached)
# -------------------------------------------------------------
@router.get("/crops")
async def get_crops_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"report:crops:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crops = db.query(models.Crop).filter(
        models.Crop.owner_id == uid
    ).all()

    total_area = sum(c.area_hectares or 0 for c in crops)
    by_crop = {}
    harvest_summary = {"completed": 0, "pending": 0}

    for crop in crops:
        area = crop.area_hectares or 0
        by_crop[crop.name] = by_crop.get(crop.name, 0) + area

        if (crop.status or "").lower() == "completed":
            harvest_summary["completed"] += 1
        else:
            harvest_summary["pending"] += 1

    payload = {
        "total_area": total_area,
        "by_crop": by_crop,
        "harvest_summary": harvest_summary
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# FINANCIAL REPORT  (cached)
# -------------------------------------------------------------
@router.get("/financial")
async def get_financial_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"report:financial:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    transactions = db.query(models.Transaction).filter(
        models.Transaction.owner_id == uid
    ).all()

    total_income = sum(t.amount for t in transactions if t.type == "income")
    total_expenses = sum(t.amount for t in transactions if t.type == "expense")
    net_profit = total_income - total_expenses

    by_category = {}
    for t in transactions:
        key = t.category or "uncategorized"
        by_category[key] = by_category.get(key, 0) + (t.amount or 0)

    payload = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "by_category": by_category
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# INVENTORY REPORT  (cached)
# -------------------------------------------------------------
@router.get("/inventory")
async def get_inventory_report(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"report:inventory:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.owner_id == uid
    ).all()

    total_items = len(items)

    low_stock_items = len([
        i for i in items
        if i.reorder_level is not None and i.quantity <= (i.reorder_level or 0)
    ])

    out_of_stock = len([i for i in items if (i.quantity or 0) == 0])

    total_value = sum((i.quantity or 0) for i in items)  # add price later

    payload = {
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,
        "total_value": total_value
    }

    await cache_set(cache_key, payload, 300)
    return payload
