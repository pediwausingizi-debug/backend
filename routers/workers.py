# routers/workers.py

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from utils.notification_utils import create_notification
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(
    prefix="",         
    tags=["Workers"]
)

# Helper: real DB user + farm validation
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User is not assigned to any farm")

    return db_user


# -------------------------------------------------------------------
# GET workers (JSON-safe)
# -------------------------------------------------------------------
@router.get("/", response_model=List[schemas.WorkerRead])
async def get_workers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    workers = db.query(models.Worker).filter(
        models.Worker.farm_id == db_user.farm_id
    ).all()

    return [
        schemas.WorkerRead.model_validate(w).model_dump()
        for w in workers
    ]


# -------------------------------------------------------------------
# CREATE worker
# -------------------------------------------------------------------
@router.post("/", response_model=schemas.WorkerRead, status_code=status.HTTP_201_CREATED)
async def create_worker(
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

    return schemas.WorkerRead.model_validate(db_worker)


# -------------------------------------------------------------------
# GET worker by ID
# -------------------------------------------------------------------
@router.get("/{worker_id}", response_model=schemas.WorkerRead)
async def get_worker(
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
        raise HTTPException(404, "Worker not found")

    return schemas.WorkerRead.model_validate(worker)


# -------------------------------------------------------------------
# UPDATE worker
# -------------------------------------------------------------------
@router.put("/{worker_id}", response_model=schemas.WorkerRead)
async def update_worker(
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
        raise HTTPException(404, "Worker not found")

    for k, v in updated_worker.dict().items():
        setattr(worker, k, v)

    db.commit()
    db.refresh(worker)

    return schemas.WorkerRead.model_validate(worker)


# -------------------------------------------------------------------
# DELETE worker
# -------------------------------------------------------------------
@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    auth_user=Depends(get_current_user),
):
    if auth_user["role"] != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    worker = (
        db.query(models.Worker)
        .filter(
            models.Worker.id == worker_id,
            models.Worker.farm_id == auth_user["farm_id"]
        )
        .first()
    )

    if not worker:
        raise HTTPException(404, "Worker not found")

    #  Find matching user by email
    user = (
        db.query(models.User)
        .filter(
            models.User.email == worker.email,
            models.User.farm_id == auth_user["farm_id"]
        )
        .first()
    )

    # Delete worker
    db.delete(worker)

    # Delete user account if exists
    if user:
        db.delete(user)

    db.commit()

    return None
