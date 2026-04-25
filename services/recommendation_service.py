from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
import models


def safe_num(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def get_livestock_recommendations(db: Session, farm_id: int):
    recommendations = []

    animals = (
        db.query(models.Animal)
        .filter(models.Animal.farm_id == farm_id)
        .all()
    )

    now = datetime.utcnow()
    overdue_days = 30

    for animal in animals:
        total_income = (
            db.query(func.sum(models.AnimalIncome.amount))
            .filter(models.AnimalIncome.animal_id == animal.id)
            .scalar()
            or 0.0
        )

        total_expenses = (
            db.query(func.sum(models.AnimalExpense.amount))
            .filter(models.AnimalExpense.animal_id == animal.id)
            .scalar()
            or 0.0
        )

        if total_expenses > total_income and (total_income > 0 or total_expenses > 0):
            recommendations.append({
                "type": "livestock",
                "severity": "warning",
                "title": f"Animal {animal.tag_number} is loss-making",
                "message": (
                    f"{animal.name or animal.type} has expenses of {total_expenses:.2f} "
                    f"and income of {total_income:.2f}. Review feed, treatment, and output."
                ),
                "entity_id": animal.id,
            })

        if animal.health_status and animal.health_status.lower() not in ["healthy", "normal"]:
            recommendations.append({
                "type": "livestock",
                "severity": "warning",
                "title": f"Animal {animal.tag_number} health needs attention",
                "message": (
                    f"{animal.name or animal.type} is marked as '{animal.health_status}'. "
                    f"Consider inspection or treatment follow-up."
                ),
                "entity_id": animal.id,
            })

        if animal.last_checkup:
            if animal.last_checkup < now - timedelta(days=overdue_days):
                recommendations.append({
                    "type": "livestock",
                    "severity": "info",
                    "title": f"Animal {animal.tag_number} checkup overdue",
                    "message": (
                        f"{animal.name or animal.type} has not been checked in over {overdue_days} days."
                    ),
                    "entity_id": animal.id,
                })

        recent_production_count = (
            db.query(models.AnimalProduction)
            .filter(
                models.AnimalProduction.animal_id == animal.id,
                models.AnimalProduction.date >= now - timedelta(days=30),
            )
            .count()
        )

        if recent_production_count == 0 and animal.status == "active":
            recommendations.append({
                "type": "livestock",
                "severity": "info",
                "title": f"No recent production for {animal.tag_number}",
                "message": (
                    f"{animal.name or animal.type} has no production records in the last 30 days."
                ),
                "entity_id": animal.id,
            })

    return recommendations


def get_crop_recommendations(db: Session, farm_id: int):
    recommendations = []

    cycles = (
        db.query(models.CropCycle)
        .filter(models.CropCycle.farm_id == farm_id)
        .all()
    )

    now = datetime.utcnow()

    for cycle in cycles:
        crop_name = cycle.crop.name if cycle.crop else "Crop"
        plot_name = cycle.plot.name if cycle.plot else "Unknown Plot"

        total_income = (
            db.query(func.sum(models.CropCycleIncome.amount))
            .filter(models.CropCycleIncome.crop_cycle_id == cycle.id)
            .scalar()
            or 0.0
        )

        total_expenses = (
            db.query(func.sum(models.CropCycleExpense.amount))
            .filter(models.CropCycleExpense.crop_cycle_id == cycle.id)
            .scalar()
            or 0.0
        )

        if total_expenses > total_income and (total_income > 0 or total_expenses > 0):
            recommendations.append({
                "type": "crop",
                "severity": "warning",
                "title": f"{crop_name} in {plot_name} is loss-making",
                "message": (
                    f"This crop cycle has expenses of {total_expenses:.2f} and income of {total_income:.2f}. "
                    f"Review inputs, pricing, or yield."
                ),
                "entity_id": cycle.id,
            })

        if cycle.expected_harvest_date and cycle.status in ["active", "growing", "planted"]:
            days_to_harvest = (cycle.expected_harvest_date - now).days
            if 0 <= days_to_harvest <= 7:
                recommendations.append({
                    "type": "crop",
                    "severity": "info",
                    "title": f"{crop_name} in {plot_name} nearing harvest",
                    "message": f"Expected harvest is in {days_to_harvest} day(s). Prepare harvest and sale planning.",
                    "entity_id": cycle.id,
                })

        if cycle.planting_date and cycle.status in ["active", "growing", "planted"]:
            days_active = (now - cycle.planting_date).days
            if days_active > 180 and not cycle.actual_harvest_date:
                recommendations.append({
                    "type": "crop",
                    "severity": "warning",
                    "title": f"{crop_name} in {plot_name} may be overdue",
                    "message": (
                        f"This crop cycle has been active for {days_active} days without harvest recorded."
                    ),
                    "entity_id": cycle.id,
                })

    return recommendations


def get_finance_recommendations(db: Session, farm_id: int):
    recommendations = []

    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .all()
    )

    revenue = 0.0
    expenses = 0.0

    for tx in transactions:
        tx_type = (tx.type or "").lower()
        amount = abs(safe_num(tx.amount))

        if tx_type == "income":
            revenue += amount
        elif tx_type == "expense":
            expenses += amount

    if expenses > revenue and (revenue > 0 or expenses > 0):
        recommendations.append({
            "type": "finance",
            "severity": "warning",
            "title": "Farm expenses exceed income",
            "message": (
                f"Total recorded expenses are {expenses:.2f} while income is {revenue:.2f}. "
                f"Review high-cost operations and low-performing units."
            ),
            "entity_id": None,
        })

    if revenue > expenses and revenue > 0:
        recommendations.append({
            "type": "finance",
            "severity": "success",
            "title": "Farm is currently profitable",
            "message": (
                f"Recorded income is {revenue:.2f} and expenses are {expenses:.2f}. "
                f"Maintain the current profitable activities."
            ),
            "entity_id": None,
        })

    return recommendations


def build_recommendations(db: Session, farm_id: int):
    livestock = get_livestock_recommendations(db, farm_id)
    crops = get_crop_recommendations(db, farm_id)
    finance = get_finance_recommendations(db, farm_id)

    all_items = livestock + crops + finance

    severity_order = {"warning": 0, "info": 1, "success": 2}
    all_items.sort(key=lambda x: severity_order.get(x["severity"], 99))

    return {
        "livestock": livestock,
        "crops": crops,
        "finance": finance,
        "all": all_items,
        "total": len(all_items),
    }