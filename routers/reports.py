from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models

router = APIRouter()


@router.get("/livestock")
def get_livestock_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.Livestock).filter(models.Livestock.owner_id == current_user.id).all()
    total_count = sum(i.quantity for i in items)
    by_type = {}
    health_summary = {"healthy": 0, "sick": 0, "treatment": 0}

    for livestock in items:
        by_type[livestock.type] = by_type.get(livestock.type, 0) + (livestock.quantity or 0)
        status = (livestock.health_status or "").lower()
        if status == "healthy":
            health_summary["healthy"] += (livestock.quantity or 0)
        elif status == "sick":
            health_summary["sick"] += (livestock.quantity or 0)
        else:
            health_summary["treatment"] += (livestock.quantity or 0)

    return {
        "total_count": total_count,
        "by_type": by_type,
        "health_summary": health_summary
    }


@router.get("/crops")
def get_crops_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    crops = db.query(models.Crop).filter(models.Crop.owner_id == current_user.id).all()
    total_area = sum((crop.area_hectares or 0) for crop in crops)
    by_crop = {}
    harvest_summary = {"completed": 0, "pending": 0}

    for crop in crops:
        by_crop[crop.name] = by_crop.get(crop.name, 0) + (crop.area_hectares or 0)
        if crop.status == "completed":
            harvest_summary["completed"] += 1
        else:
            harvest_summary["pending"] += 1

    return {
        "total_area": total_area,
        "by_crop": by_crop,
        "harvest_summary": harvest_summary
    }


@router.get("/financial")
def get_financial_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    transactions = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).all()
    total_income = sum([t.amount for t in transactions if t.type == "income"])
    total_expenses = sum([t.amount for t in transactions if t.type == "expense"])
    net_profit = total_income - total_expenses

    by_category = {}
    for t in transactions:
        key = t.category or "uncategorized"
        by_category[key] = by_category.get(key, 0) + (t.amount or 0)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "by_category": by_category
    }


@router.get("/inventory")
def get_inventory_report(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.InventoryItem).filter(models.InventoryItem.owner_id == current_user.id).all()
    total_items = len(items)
    low_stock_items = len([i for i in items if i.reorder_level is not None and i.quantity <= (i.reorder_level or 0)])
    out_of_stock = len([i for i in items if (i.quantity or 0) == 0])
    total_value = sum([(i.quantity or 0) for i in items])  # multiply by price if you add unit price later

    return {
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,
        "total_value": total_value
    }
