from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to load actual SQL user from JWT payload
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/transactions", response_model=List[schemas.TransactionRead])
def get_transactions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.owner_id == db_user.id)
        .order_by(models.Transaction.date.desc())
        .all()
    )
    return txs


@router.post("/transactions", response_model=schemas.TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    tx_data = payload.dict()
    if not tx_data.get("date"):
        tx_data["date"] = datetime.utcnow()

    tx = models.Transaction(**tx_data, owner_id=db_user.id)

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/summary")
def get_financial_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    txs = db.query(models.Transaction).filter(models.Transaction.owner_id == db_user.id).all()

    total_income = sum(t.amount for t in txs if t.type == "income")
    total_expenses = sum(t.amount for t in txs if t.type == "expense")
    net_profit = total_income - total_expenses
    profit_margin = (net_profit / total_income * 100) if total_income else 0.0

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": round(profit_margin, 2)
    }
