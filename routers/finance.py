# routers/finance.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from utils.auth_utils import get_current_user
from utils.cache import cache_get, cache_set, cache_delete
import models, schemas

router = APIRouter()


# Helper to load actual SQL user from JWT payload
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ---------------------------------------------------------
# GET /transactions  (cached)
# ---------------------------------------------------------
@router.get("/transactions", response_model=List[schemas.TransactionRead])
async def get_transactions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"finance:txs:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.owner_id == uid)
        .order_by(models.Transaction.date.desc())
        .all()
    )

    # Convert SQLAlchemy objects → dict for Redis storage
    txs_serialized = [schemas.TransactionRead.model_validate(t).model_dump() for t in txs]

    await cache_set(cache_key, txs_serialized, expire_seconds=300)
    return txs


# ---------------------------------------------------------
# POST /transactions (invalidate all caches)
# ---------------------------------------------------------
@router.post("/transactions", response_model=schemas.TransactionRead,
             status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    tx_data = payload.dict()
    if not tx_data.get("date"):
        tx_data["date"] = datetime.utcnow()

    tx = models.Transaction(**tx_data, owner_id=uid)

    db.add(tx)
    db.commit()
    db.refresh(tx)

    # Invalidate finance-related & dashboard caches
    await cache_delete(f"finance:txs:{uid}")
    await cache_delete(f"finance:summary:{uid}")

    await cache_delete(f"dashboard:stats:{uid}")
    await cache_delete(f"dashboard:recent:{uid}")

    return tx


# ---------------------------------------------------------
# GET /summary  (cached)
# ---------------------------------------------------------
@router.get("/summary")
async def get_financial_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"finance:summary:{uid}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    txs = db.query(models.Transaction).filter(
        models.Transaction.owner_id == uid
    ).all()

    total_income = sum(t.amount for t in txs if t.type == "income")
    total_expenses = sum(t.amount for t in txs if t.type == "expense")
    net_profit = total_income - total_expenses
    profit_margin = (net_profit / total_income * 100) if total_income else 0

    summary = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": round(profit_margin, 2)
    }

    await cache_set(cache_key, summary, expire_seconds=300)
    return summary
