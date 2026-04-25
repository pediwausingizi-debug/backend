from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Dict, Any

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set, cache_delete
import models, schemas

router = APIRouter(
    prefix="",
    tags=["finance"]
)


# ---------------------------------------------------------
# Helper – get actual User + farm_id
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# GET /transactions
# Matches frontend Transaction table
# ---------------------------------------------------------
@router.get("/transactions", response_model=List[schemas.TransactionRead])
async def get_transactions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"finance:txs:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .order_by(models.Transaction.date.desc())
        .all()
    )

    serialized = [
        schemas.TransactionRead.model_validate(t).model_dump(mode="json")
        for t in txs
    ]

    await cache_set(cache_key, serialized)
    return serialized


# ---------------------------------------------------------
# POST /transactions
# Matches new finance frontend payload:
# type, category, amount, description, payment_method, date
# ---------------------------------------------------------
@router.post(
    "/transactions",
    response_model=schemas.TransactionRead,
    status_code=status.HTTP_201_CREATED
)
async def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    tx_data = payload.model_dump(exclude_unset=True)

    tx_type = (tx_data.get("type") or "").strip().lower()
    if tx_type not in ["income", "expense"]:
        raise HTTPException(
            status_code=400,
            detail="Transaction type must be either 'income' or 'expense'"
        )

    amount = float(tx_data.get("amount") or 0)
    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Transaction amount must be greater than 0"
        )

    tx_data["type"] = tx_type
    tx_data["amount"] = amount

    if not tx_data.get("date"):
        tx_data["date"] = datetime.utcnow()

    tx = models.Transaction(
        **tx_data,
        farm_id=farm_id,
        created_by_id=db_user.id
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)

    # invalidate caches used by finance + dashboard
    await cache_delete(f"finance:txs:farm:{farm_id}")
    await cache_delete(f"finance:summary:farm:{farm_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")
    await cache_delete(f"dashboard:recent:farm:{farm_id}")

    return schemas.TransactionRead.model_validate(tx)


# ---------------------------------------------------------
# GET /summary
# Matches frontend summary cards
# ---------------------------------------------------------
@router.get("/summary")
async def get_financial_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
) -> Dict[str, Any]:
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"finance:summary:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.farm_id == farm_id)
        .all()
    )

    total_income = sum(
        float(t.amount or 0)
        for t in txs
        if (t.type or "").lower() == "income"
    )

    total_expenses = sum(
        float(t.amount or 0)
        for t in txs
        if (t.type or "").lower() == "expense"
    )

    net_profit = total_income - total_expenses
    profit_margin = (net_profit / total_income * 100) if total_income else 0

    summary = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": round(profit_margin, 2),
    }

    await cache_set(cache_key, summary)
    return summary