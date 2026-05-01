from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import SessionLocal
from services.report_service import send_reports_to_admins
import models


def get_livestock_data(db, farm_id: int):
    items = (
        db.query(models.Livestock)
        .filter(models.Livestock.farm_id == farm_id)
        .all()
    )

    total_count = sum((i.quantity or 0) for i in items)

    by_type = {}
    health_summary = {"healthy": 0, "sick": 0, "treatment": 0}

    for livestock in items:
        qty = livestock.quantity or 0

        livestock_type = livestock.type or "Unknown"
        by_type[livestock_type] = by_type.get(livestock_type, 0) + qty

        status = (livestock.health_status or "").lower().strip()
        if status == "healthy":
            health_summary["healthy"] += qty
        elif status == "sick":
            health_summary["sick"] += qty
        else:
            health_summary["treatment"] += qty

    return {
        "total_count": total_count,
        "by_type": by_type,
        "health_summary": health_summary,
    }


def get_crops_data(db, farm_id: int):
    crops = (
        db.query(models.Crop)
        .filter(models.Crop.farm_id == farm_id)
        .all()
    )

    total_area = sum((c.area_hectares or 0) for c in crops)

    by_crop = {}
    harvest_summary = {"completed": 0, "pending": 0}

    for crop in crops:
        area = crop.area_hectares or 0
        name = crop.name or "Unknown"

        by_crop[name] = by_crop.get(name, 0) + area

        status = (crop.status or "").lower().strip()
        if status == "completed":
            harvest_summary["completed"] += 1
        else:
            harvest_summary["pending"] += 1

    return {
        "total_area": total_area,
        "by_crop": by_crop,
        "harvest_summary": harvest_summary,
    }


def get_financial_data(db, farm_id: int):
    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .all()
    )

    total_income = sum(
        float(t.amount or 0)
        for t in transactions
        if (t.type or "").lower() == "income"
    )

    total_expenses = sum(
        float(t.amount or 0)
        for t in transactions
        if (t.type or "").lower() == "expense"
    )

    by_category = {}

    for transaction in transactions:
        category = (transaction.category or "uncategorized").strip() or "uncategorized"
        by_category[category] = by_category.get(category, 0) + float(transaction.amount or 0)

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": total_income - total_expenses,
        "by_category": by_category,
    }


def get_inventory_data(db, farm_id: int):
    items = (
        db.query(models.InventoryItem)
        .filter(models.InventoryItem.farm_id == farm_id)
        .all()
    )

    total_items = len(items)

    low_stock_items = len(
        [
            item for item in items
            if item.reorder_level is not None
            and (item.quantity or 0) <= (item.reorder_level or 0)
        ]
    )

    out_of_stock = len(
        [
            item for item in items
            if (item.quantity or 0) == 0
        ]
    )

    total_value = sum(
        (item.quantity or 0) * (item.price or 0)
        for item in items
    )

    by_category = {}

    for item in items:
        category = (item.category or "uncategorized").strip() or "uncategorized"
        by_category[category] = by_category.get(category, 0) + (item.quantity or 0)

    return {
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,
        "total_value": total_value,
        "by_category": by_category,
    }


async def generate_reports_for_all_farms():
    db = SessionLocal()

    try:
        farms = db.query(models.Farm).all()

        for farm in farms:
            farm_id = farm.id

            livestock = get_livestock_data(db, farm_id)
            crops = get_crops_data(db, farm_id)
            financial = get_financial_data(db, farm_id)
            inventory = get_inventory_data(db, farm_id)

            report_data = (livestock, crops, financial, inventory)

            send_reports_to_admins(db, farm_id, farm.name, report_data)

    finally:
        db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        generate_reports_for_all_farms,
        "cron",
        day_of_week="mon",
        hour=6,
        minute=0,
    )

    scheduler.add_job(
        generate_reports_for_all_farms,
        "cron",
        day=1,
        hour=6,
        minute=0,
    )

    scheduler.start()