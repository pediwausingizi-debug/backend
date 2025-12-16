from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import SessionLocal
from services.report_service import send_reports_to_admins
import models
import asyncio


async def generate_reports_for_all_farms():
    db = SessionLocal()

    farms = db.query(models.Farm).all()

    for farm in farms:
        farm_id = farm.id

        # Fetch each report by calling the same logic used in API endpoints
        livestock = await get_livestock_data(db, farm_id)
        crops = await get_crops_data(db, farm_id)
        financial = await get_financial_data(db, farm_id)
        inventory = await get_inventory_data(db, farm_id)

        report_data = (livestock, crops, financial, inventory)

        send_reports_to_admins(db, farm_id, farm.name, report_data)

    db.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()

    # Every Monday at 6 AM
    scheduler.add_job(
        generate_reports_for_all_farms,
        "cron",
        day_of_week="mon",
        hour=6,
        minute=0
    )

    # First day of each month at 6 AM
    scheduler.add_job(
        generate_reports_for_all_farms,
        "cron",
        day=1,
        hour=6,
        minute=0
    )

    scheduler.start()
