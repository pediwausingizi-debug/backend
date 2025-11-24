from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.WorkerRead])
def get_workers(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    workers = db.query(models.Worker).filter(models.Worker.owner_id == current_user.id).all()
    return workers


@router.post("/", response_model=schemas.WorkerRead, status_code=status.HTTP_201_CREATED)
def create_worker(worker: schemas.WorkerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_worker = models.Worker(**worker.dict(), owner_id=current_user.id)
    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)
    return db_worker


@router.get("/{worker_id}", response_model=schemas.WorkerRead)
def get_worker(worker_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id, models.Worker.owner_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return worker


@router.put("/{worker_id}", response_model=schemas.WorkerRead)
def update_worker(worker_id: int, updated_worker: schemas.WorkerCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id, models.Worker.owner_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    for key, value in updated_worker.dict().items():
        setattr(worker, key, value)

    db.commit()
    db.refresh(worker)
    return worker


@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_worker(worker_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    worker = db.query(models.Worker).filter(models.Worker.id == worker_id, models.Worker.owner_id == current_user.id).first()
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    db.delete(worker)
    db.commit()
    return None
