# routers/livestock.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="", tags=["livestock"])


# =========================================================
# HELPER
# =========================================================
def get_farm_user(user_data, db: Session) -> models.User:
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User not assigned to farm")

    return db_user


# =========================================================
# ================= LIVESTOCK GROUP ========================
# =========================================================

@router.get("/", response_model=List[schemas.LivestockRead])
async def list_livestock(db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_user = get_farm_user(user, db)

    animals = db.query(models.Livestock).filter(
        models.Livestock.farm_id == db_user.farm_id
    ).all()

    return animals


@router.post("/", response_model=schemas.LivestockRead)
async def create_livestock(
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    obj = models.Livestock(
        **payload.model_dump(exclude_unset=True),
        farm_id=db_user.farm_id,
        created_by_id=db_user.id,
    )

    db.add(obj)
    db.commit()
    db.refresh(obj)

    return obj


# =========================================================
# ===================== ANIMALS ============================
# =========================================================

@router.post("/animals", response_model=schemas.AnimalRead)
async def create_animal(
    payload: schemas.AnimalCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    animal = models.Animal(
        **payload.model_dump(exclude_unset=True),
        farm_id=db_user.farm_id,
        created_by_id=db_user.id,
        created_at=datetime.utcnow(),
    )

    db.add(animal)
    db.commit()
    db.refresh(animal)

    return animal


@router.get("/animals", response_model=List[schemas.AnimalRead])
async def list_animals(db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_user = get_farm_user(user, db)

    return db.query(models.Animal).filter(
        models.Animal.farm_id == db_user.farm_id
    ).all()


@router.get("/animals/{animal_id}", response_model=schemas.AnimalRead)
async def get_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    animal = db.query(models.Animal).filter(
        models.Animal.id == animal_id,
        models.Animal.farm_id == db_user.farm_id
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    return animal


@router.put("/animals/{animal_id}", response_model=schemas.AnimalRead)
async def update_animal(
    animal_id: int,
    payload: schemas.AnimalUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    animal = db.query(models.Animal).filter(
        models.Animal.id == animal_id,
        models.Animal.farm_id == db_user.farm_id
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(animal, k, v)

    db.commit()
    db.refresh(animal)

    return animal


@router.delete("/animals/{animal_id}")
async def delete_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    animal = db.query(models.Animal).filter(
        models.Animal.id == animal_id,
        models.Animal.farm_id == db_user.farm_id
    ).first()

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    db.delete(animal)
    db.commit()

    return {"message": "Animal deleted"}


# =========================================================
# ================= PRODUCTION =============================
# =========================================================

@router.post("/animals/{animal_id}/production")
async def add_production(
    animal_id: int,
    payload: schemas.AnimalProductionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    get_farm_user(user, db)

    record = models.AnimalProduction(
        animal_id=animal_id,
        **payload.model_dump(exclude_unset=True),
        date=datetime.utcnow()
    )

    db.add(record)
    db.commit()

    return {"message": "Production added"}


@router.get("/animals/{animal_id}/production")
async def get_production(animal_id: int, db: Session = Depends(get_db)):
    return db.query(models.AnimalProduction).filter(
        models.AnimalProduction.animal_id == animal_id
    ).all()


# =========================================================
# ================= EXPENSES ===============================
# =========================================================

@router.post("/animals/{animal_id}/expenses")
async def add_expense(
    animal_id: int,
    payload: schemas.AnimalExpenseCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    get_farm_user(user, db)

    expense = models.AnimalExpense(
        animal_id=animal_id,
        **payload.model_dump(exclude_unset=True),
        date=datetime.utcnow()
    )

    db.add(expense)
    db.commit()

    return {"message": "Expense added"}


@router.get("/animals/{animal_id}/expenses")
async def get_expenses(animal_id: int, db: Session = Depends(get_db)):
    return db.query(models.AnimalExpense).filter(
        models.AnimalExpense.animal_id == animal_id
    ).all()


# =========================================================
# ================= INCOME ================================
# =========================================================

@router.post("/animals/{animal_id}/income")
async def add_income(
    animal_id: int,
    payload: schemas.AnimalIncomeCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    get_farm_user(user, db)

    income = models.AnimalIncome(
        animal_id=animal_id,
        **payload.model_dump(exclude_unset=True),
        date=datetime.utcnow()
    )

    db.add(income)
    db.commit()

    return {"message": "Income added"}


@router.get("/animals/{animal_id}/income")
async def get_income(animal_id: int, db: Session = Depends(get_db)):
    return db.query(models.AnimalIncome).filter(
        models.AnimalIncome.animal_id == animal_id
    ).all()


# =========================================================
# ================= PROFIT SUMMARY ========================
# =========================================================

@router.get("/animals/{animal_id}/profit-summary", response_model=schemas.AnimalProfitSummary)
async def get_profit_summary(
    animal_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    get_farm_user(user, db)

    total_income = db.query(func.sum(models.AnimalIncome.amount)).filter(
        models.AnimalIncome.animal_id == animal_id
    ).scalar() or 0

    total_expenses = db.query(func.sum(models.AnimalExpense.amount)).filter(
        models.AnimalExpense.animal_id == animal_id
    ).scalar() or 0

    return schemas.AnimalProfitSummary(
        animal_id=animal_id,
        total_income=total_income,
        total_expenses=total_expenses,
        net_profit=total_income - total_expenses
    )