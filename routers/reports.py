# routers/reports.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.email_utils import send_email
from utils.notification_utils import create_notification
from utils.cache import cache_get, cache_set
from database import get_db
from utils.auth_utils import get_current_user
import models
import csv
from io import StringIO
from fastapi.responses import Response

from datetime import datetime, time
from typing import Optional


router = APIRouter(
    prefix="",
    tags=["reports"]
)


# -------------------------------------------------------------
# Helper → fetch full SQL user + farm
# -------------------------------------------------------------
def get_db_user(user_data, db: Session):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User is not assigned to a farm")

    return db_user


# -------------------------------------------------------------
# Helper → parse YYYY-MM-DD date range
# end is inclusive (end-of-day)
# -------------------------------------------------------------
def parse_date_range(start: Optional[str], end: Optional[str]):
    if not start and not end:
        return None, None

    if not start or not end:
        raise HTTPException(status_code=400, detail="Provide both start and end (YYYY-MM-DD)")

    try:
        start_d = datetime.strptime(start, "%Y-%m-%d").date()
        end_d = datetime.strptime(end, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    if end_d < start_d:
        raise HTTPException(status_code=400, detail="end must be >= start")

    start_dt = datetime.combine(start_d, time.min)
    end_dt = datetime.combine(end_d, time.max)
    return start_dt, end_dt


# -------------------------------------------------------------
# LIVESTOCK REPORT  →  /api/reports/livestock?start=YYYY-MM-DD&end=YYYY-MM-DD
# Filters by Livestock.created_at if start/end provided
# -------------------------------------------------------------
@router.get("/livestock")
async def get_livestock_report(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    start_dt, end_dt = parse_date_range(start, end)

    cache_key = f"report:livestock:farm:{farm_id}:{start or 'all'}:{end or 'all'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    q = db.query(models.Livestock).filter(models.Livestock.farm_id == farm_id)

    # Optional date filtering (created_at exists in your Livestock model)
    if start_dt and end_dt:
        q = q.filter(
            models.Livestock.created_at >= start_dt,
            models.Livestock.created_at <= end_dt,
        )

    items = q.all()

    total_count = sum((i.quantity or 0) for i in items)

    by_type = {}
    health_summary = {"healthy": 0, "sick": 0, "treatment": 0}

    for livestock in items:
        qty = livestock.quantity or 0

        t = livestock.type or "Unknown"
        by_type[t] = by_type.get(t, 0) + qty

        status = (livestock.health_status or "").lower().strip()
        if status == "healthy":
            health_summary["healthy"] += qty
        elif status == "sick":
            health_summary["sick"] += qty
        else:
            health_summary["treatment"] += qty

    payload = {
        "range": {"start": start, "end": end},
        "total_count": total_count,
        "by_type": by_type,
        "health_summary": health_summary,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# CROPS REPORT  →  /api/reports/crops?start=YYYY-MM-DD&end=YYYY-MM-DD
# Filters by planting_date if start/end provided
# -------------------------------------------------------------
@router.get("/crops")
async def get_crops_report(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    start_dt, end_dt = parse_date_range(start, end)

    cache_key = f"report:crops:farm:{farm_id}:{start or 'all'}:{end or 'all'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    q = db.query(models.Crop).filter(models.Crop.farm_id == farm_id)

    # Optional date filtering by planting_date
    if start_dt and end_dt:
        q = q.filter(models.Crop.planting_date != None)
        q = q.filter(
            models.Crop.planting_date >= start_dt,
            models.Crop.planting_date <= end_dt,
        )

    crops = q.all()

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

    payload = {
        "range": {"start": start, "end": end},
        "total_area": total_area,
        "by_crop": by_crop,
        "harvest_summary": harvest_summary,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# FINANCIAL REPORT  →  /api/reports/financial?start=YYYY-MM-DD&end=YYYY-MM-DD
# Filters by Transaction.date if start/end provided
# -------------------------------------------------------------
@router.get("/financial")
async def get_financial_report(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    start_dt, end_dt = parse_date_range(start, end)

    cache_key = f"report:financial:farm:{farm_id}:{start or 'all'}:{end or 'all'}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    q = db.query(models.Transaction).filter(models.Transaction.farm_id == farm_id)

    if start_dt and end_dt:
        q = q.filter(
            models.Transaction.date >= start_dt,
            models.Transaction.date <= end_dt,
        )

    transactions = q.all()

    total_income = sum(float(t.amount or 0) for t in transactions if (t.type or "").lower() == "income")
    total_expenses = sum(float(t.amount or 0) for t in transactions if (t.type or "").lower() == "expense")
    net_profit = total_income - total_expenses

    by_category = {}
    for t in transactions:
        cat = (t.category or "uncategorized").strip() or "uncategorized"
        by_category[cat] = by_category.get(cat, 0) + float(t.amount or 0)

    payload = {
        "range": {"start": start, "end": end},
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "by_category": by_category,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# INVENTORY REPORT  →  /api/reports/inventory
# (Date range accepted for API consistency but inventory has no timestamp field in your model)
# -------------------------------------------------------------
@router.get("/inventory")
async def get_inventory_report(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    # Inventory is point-in-time; still separate cache by range to match UI expectations
    cache_key = f"report:inventory:farm:{farm_id}:{start or 'all'}:{end or 'all'}"
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

    # NOTE: your previous "total_value" was summing quantities; keeping same behavior to avoid breaking UI
    total_value = sum((i.quantity or 0) for i in items)

    payload = {
        "range": {"start": start, "end": end},
        "total_items": total_items,
        "low_stock_items": low_stock_items,
        "out_of_stock": out_of_stock,
        "total_value": total_value,
    }

    await cache_set(cache_key, payload, 300)
    return payload


# -------------------------------------------------------------
# Report Notifications + Email helpers
# -------------------------------------------------------------
def send_weekly_report(db, farm, user, pdf_path=None):
    title = "Weekly Farm Report"
    message = "Your weekly farm performance report has been generated."

    # Save notification (ALWAYS)
    create_notification(
        db=db,
        farm_id=farm.id,
        title=title,
        message=message,
        type="weekly_report",
        created_by_id=None,  # system-generated
    )

    # Send email only if enabled
    if user.email_notifications and user.weekly_reports:
        send_email(
            to=user.email,
            subject=title,
            body=(
                f"Hello {user.name},\n\n"
                "Your weekly farm report is ready.\n"
                "Please find the summary attached.\n\n"
                "— FarmXpat"
            ),
            # attachment logic later
        )


def send_monthly_report(db, farm, user):
    title = "Monthly Farm Report"
    message = "Your monthly farm summary report is now available."

    create_notification(
        db=db,
        farm_id=farm.id,
        title=title,
        message=message,
        type="monthly_report",
        created_by_id=None,
    )

    if user.email_notifications:
        send_email(
            to=user.email,
            subject=title,
            body="Your monthly farm report is ready."
        )
# -------------------------------------------------------------
# CSV helpers
# -------------------------------------------------------------
def _csv_response(filename: str, rows: list[list], headers: list[str] | None = None) -> Response:
    sio = StringIO()
    writer = csv.writer(sio)

    if headers:
        writer.writerow(headers)

    for r in rows:
        writer.writerow(r)

    csv_text = sio.getvalue()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# -------------------------------------------------------------
# LIVESTOCK REPORT CSV  →  /api/reports/livestock.csv
# -------------------------------------------------------------
@router.get("/livestock.csv")
async def get_livestock_report_csv(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await get_livestock_report(start=start, end=end, db=db, user=user)

    rows = []
    rows.append(["range_start", payload["range"]["start"] or ""])
    rows.append(["range_end", payload["range"]["end"] or ""])
    rows.append([])
    rows.append(["metric", "value"])
    rows.append(["total_count", payload["total_count"]])
    rows.append([])

    # by_type
    rows.append(["by_type", "quantity"])
    for k, v in (payload.get("by_type") or {}).items():
        rows.append([k, v])

    rows.append([])

    # health_summary
    rows.append(["health_summary", "quantity"])
    for k, v in (payload.get("health_summary") or {}).items():
        rows.append([k, v])

    return _csv_response("livestock_report.csv", rows)


# -------------------------------------------------------------
# CROPS REPORT CSV  →  /api/reports/crops.csv
# -------------------------------------------------------------
@router.get("/crops.csv")
async def get_crops_report_csv(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await get_crops_report(start=start, end=end, db=db, user=user)

    rows = []
    rows.append(["range_start", payload["range"]["start"] or ""])
    rows.append(["range_end", payload["range"]["end"] or ""])
    rows.append([])
    rows.append(["metric", "value"])
    rows.append(["total_area", payload["total_area"]])
    rows.append([])

    # by_crop
    rows.append(["by_crop", "area_hectares"])
    for k, v in (payload.get("by_crop") or {}).items():
        rows.append([k, v])

    rows.append([])

    # harvest_summary
    rows.append(["harvest_summary", "count"])
    for k, v in (payload.get("harvest_summary") or {}).items():
        rows.append([k, v])

    return _csv_response("crops_report.csv", rows)


# -------------------------------------------------------------
# FINANCIAL REPORT CSV  →  /api/reports/financial.csv
# -------------------------------------------------------------
@router.get("/financial.csv")
async def get_financial_report_csv(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await get_financial_report(start=start, end=end, db=db, user=user)

    rows = []
    rows.append(["range_start", payload["range"]["start"] or ""])
    rows.append(["range_end", payload["range"]["end"] or ""])
    rows.append([])
    rows.append(["metric", "value"])
    rows.append(["total_income", payload["total_income"]])
    rows.append(["total_expenses", payload["total_expenses"]])
    rows.append(["net_profit", payload["net_profit"]])
    rows.append([])

    rows.append(["category", "amount"])
    for k, v in (payload.get("by_category") or {}).items():
        rows.append([k, v])

    return _csv_response("financial_report.csv", rows)


# -------------------------------------------------------------
# INVENTORY REPORT CSV  →  /api/reports/inventory.csv
# -------------------------------------------------------------
@router.get("/inventory.csv")
async def get_inventory_report_csv(
    start: Optional[str] = None,
    end: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    payload = await get_inventory_report(start=start, end=end, db=db, user=user)

    rows = [
        ["range_start", payload["range"]["start"] or ""],
        ["range_end", payload["range"]["end"] or ""],
        [],
        ["metric", "value"],
        ["total_items", payload["total_items"]],
        ["low_stock_items", payload["low_stock_items"]],
        ["out_of_stock", payload["out_of_stock"]],
        ["total_value", payload["total_value"]],
    ]

    return _csv_response("inventory_report.csv", rows)
