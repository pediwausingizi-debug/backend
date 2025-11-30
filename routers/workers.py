from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter()


# Helper: load real database user and ensure they belong to a farm
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to any farm")

    return db_user


# ---------------------------------------------------------
# GET workers (farm-scoped)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.WorkerRead])
def get_workers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    workers = db.query(models.Worker).filter(
        models.Worker.farm_id == db_user.farm_id
    ).all()

    return workers


# ---------------------------------------------------------
# CREATE worker (farm-scoped)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.WorkerRead, status_code=status.HTTP_201_CREATED)
def create_worker(
    worker: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    db_worker = models.Worker(
        **worker.dict(),
        farm_id=db_user.farm_id,
        created_by_id=db_user.id
    )

    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    return db_worker


# ---------------------------------------------------------
# GET worker by ID (farm-scoped)
# ---------------------------------------------------------
@router.get("/{worker_id}", response_model=schemas.WorkerRead)
def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id,
        models.Worker.farm_id == db_user.farm_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return worker


# ---------------------------------------------------------
# UPDATE worker (farm-scoped)
# ---------------------------------------------------------
@router.put("/{worker_id}", response_model=schemas.WorkerRead)
def update_worker(
    worker_id: int,
    updated_worker: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id,
        models.Worker.farm_id == db_user.farm_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    for key, value in updated_worker.dict().items():
        setattr(worker, key, value)

    db.commit()
    db.refresh(worker)

    return worker


# ---------------------------------------------------------
# DELETE worker (farm-scoped)
# ---------------------------------------------------------
@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id,
        models.Worker.farm_id == db_user.farm_id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    db.delete(worker)
    db.commit()

    return None
