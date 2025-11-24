from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


@router.get("/transactions", response_model=List[schemas.TransactionRead])
def get_transactions(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    txs = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).order_by(models.Transaction.date.desc()).all()
    return txs


@router.post("/transactions", response_model=schemas.TransactionRead, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    tx_data = payload.dict()
    if not tx_data.get("date"):
        tx_data["date"] = datetime.utcnow()
    tx = models.Transaction(**tx_data, owner_id=current_user.id)
    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx


@router.get("/summary")
def get_financial_summary(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    txs = db.query(models.Transaction).filter(models.Transaction.owner_id == current_user.id).all()
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
