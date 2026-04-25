from datetime import datetime
from sqlalchemy.orm import Session
import models


def safe_num(value):
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def month_key(dt: datetime) -> str:
    return f"{dt.year}-{dt.month:02d}"


def average(values):
    if not values:
        return 0.0
    return sum(values) / len(values)


def predict_monthly_finance(db: Session, farm_id: int):
    transactions = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .all()
    )

    monthly_income = {}
    monthly_expenses = {}

    for tx in transactions:
        if not tx.date:
            continue

        key = month_key(tx.date)
        tx_type = (tx.type or "").lower()
        amount = abs(safe_num(tx.amount))

        if tx_type == "income":
            monthly_income[key] = monthly_income.get(key, 0.0) + amount
        elif tx_type == "expense":
            monthly_expenses[key] = monthly_expenses.get(key, 0.0) + amount

    sorted_income = [monthly_income[k] for k in sorted(monthly_income.keys())][-3:]
    sorted_expenses = [monthly_expenses[k] for k in sorted(monthly_expenses.keys())][-3:]

    predicted_income = average(sorted_income)
    predicted_expenses = average(sorted_expenses)

    return {
        "predicted_monthly_revenue": round(predicted_income, 2),
        "predicted_monthly_expenses": round(predicted_expenses, 2),
        "predicted_net_profit": round(predicted_income - predicted_expenses, 2),
        "method": "3-month moving average",
    }


def predict_animal_income(db: Session, farm_id: int):
    animals = (
        db.query(models.Animal)
        .filter(models.Animal.farm_id == farm_id)
        .all()
    )

    results = []

    for animal in animals:
        incomes = (
            db.query(models.AnimalIncome)
            .filter(models.AnimalIncome.animal_id == animal.id)
            .all()
        )

        monthly = {}
        for inc in incomes:
            if not inc.date:
                continue
            key = month_key(inc.date)
            monthly[key] = monthly.get(key, 0.0) + safe_num(inc.amount)

        recent = [monthly[k] for k in sorted(monthly.keys())][-3:]
        prediction = average(recent)

        results.append({
            "animal_id": animal.id,
            "tag_number": animal.tag_number,
            "name": animal.name,
            "predicted_monthly_income": round(prediction, 2),
        })

    results.sort(key=lambda x: x["predicted_monthly_income"], reverse=True)
    return results


def predict_crop_cycle_income(db: Session, farm_id: int):
    cycles = (
        db.query(models.CropCycle)
        .filter(models.CropCycle.farm_id == farm_id)
        .all()
    )

    results = []

    for cycle in cycles:
        incomes = (
            db.query(models.CropCycleIncome)
            .filter(models.CropCycleIncome.crop_cycle_id == cycle.id)
            .all()
        )

        monthly = {}
        for inc in incomes:
            if not inc.date:
                continue
            key = month_key(inc.date)
            monthly[key] = monthly.get(key, 0.0) + safe_num(inc.amount)

        recent = [monthly[k] for k in sorted(monthly.keys())][-3:]
        prediction = average(recent)

        results.append({
            "crop_cycle_id": cycle.id,
            "crop_name": cycle.crop.name if cycle.crop else None,
            "plot_name": cycle.plot.name if cycle.plot else None,
            "predicted_cycle_income": round(prediction, 2),
        })

    results.sort(key=lambda x: x["predicted_cycle_income"], reverse=True)
    return results


def build_predictions(db: Session, farm_id: int):
    finance = predict_monthly_finance(db, farm_id)
    animals = predict_animal_income(db, farm_id)
    crops = predict_crop_cycle_income(db, farm_id)

    return {
        "finance": finance,
        "animals": animals[:10],
        "crops": crops[:10],
    }