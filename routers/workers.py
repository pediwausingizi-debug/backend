from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter()


# Helper: convert JWT payload → real database User
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[schemas.WorkerRead])
def get_workers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    workers = db.query(models.Worker).filter(
        models.Worker.owner_id == db_user.id
    ).all()

    return workers


@router.post("/", response_model=schemas.WorkerRead, status_code=status.HTTP_201_CREATED)
def create_worker(
    worker: schemas.WorkerCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    db_worker = models.Worker(**worker.dict(), owner_id=db_user.id)

    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    return db_worker


@router.get("/{worker_id}", response_model=schemas.WorkerRead)
def get_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id,
        models.Worker.owner_id == db_user.id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    return worker


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
        models.Worker.owner_id == db_user.id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    for key, value in updated_worker.dict().items():
        setattr(worker, key, value)

    db.commit()
    db.refresh(worker)

    return worker


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    worker = db.query(models.Worker).filter(
        models.Worker.id == worker_id,
        models.Worker.owner_id == db_user.id
    ).first()

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    db.delete(worker)
    db.commit()

    return None
