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


# -------------------------------------------------------------------
# Helper: real DB user + farm validation
# -------------------------------------------------------------------
def get_db_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to any farm")

    return db_user


def ensure_admin_or_manager(db_user: models.User):
    if db_user.role not in ["Admin", "Manager"]:
        raise HTTPException(
            status_code=403,
            detail="Only Admin or Manager can manage workers"
        )


# -------------------------------------------------------------------
# GET workers
# -------------------------------------------------------------------
@router.get("/", response_model=List[schemas.WorkerRead])
async def get_workers(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    workers = (
        db.query(models.Worker)
        .filter(models.Worker.farm_id == db_user.farm_id)
        .order_by(models.Worker.id.desc())
        .all()
    )

    return [
        schemas.WorkerRead.model_validate(w).model_dump(mode="json")
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
    ensure_admin_or_manager(db_user)

    payload = worker.model_dump(exclude_unset=True)

    if not payload.get("name"):
        raise HTTPException(status_code=400, detail="Worker name is required")

    if payload.get("salary") is not None and float(payload["salary"]) < 0:
        raise HTTPException(status_code=400, detail="Salary cannot be negative")

    db_worker = models.Worker(
        **payload,
        farm_id=db_user.farm_id,
        created_by_id=db_user.id
    )

    db.add(db_worker)
    db.commit()
    db.refresh(db_worker)

    create_notification(
        db=db,
        farm_id=db_user.farm_id,
        title="Worker added",
        message=f"{db_worker.name} was added to the workers list.",
        type="worker",
        created_by_id=db_user.id,
    )
    db.commit()

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

    worker = (
        db.query(models.Worker)
        .filter(
            models.Worker.id == worker_id,
            models.Worker.farm_id == db_user.farm_id
        )
        .first()
    )

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

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
    ensure_admin_or_manager(db_user)

    worker = (
        db.query(models.Worker)
        .filter(
            models.Worker.id == worker_id,
            models.Worker.farm_id == db_user.farm_id
        )
        .first()
    )

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    update_data = updated_worker.model_dump(exclude_unset=True)

    if "name" in update_data and not str(update_data["name"]).strip():
        raise HTTPException(status_code=400, detail="Worker name is required")

    if "salary" in update_data and update_data["salary"] is not None:
        if float(update_data["salary"]) < 0:
            raise HTTPException(status_code=400, detail="Salary cannot be negative")

    for k, v in update_data.items():
        setattr(worker, k, v)

    db.commit()
    db.refresh(worker)

    create_notification(
        db=db,
        farm_id=db_user.farm_id,
        title="Worker updated",
        message=f"{worker.name}'s details were updated.",
        type="worker",
        created_by_id=db_user.id,
    )
    db.commit()

    return schemas.WorkerRead.model_validate(worker)


# -------------------------------------------------------------------
# DELETE worker
# -------------------------------------------------------------------
@router.delete("/{worker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_worker(
    worker_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    if db_user.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Admins only"
        )

    worker = (
        db.query(models.Worker)
        .filter(
            models.Worker.id == worker_id,
            models.Worker.farm_id == db_user.farm_id
        )
        .first()
    )

    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")

    worker_name = worker.name

    # Find matching user by email
    matched_user = None
    if worker.email:
        matched_user = (
            db.query(models.User)
            .filter(
                models.User.email == worker.email,
                models.User.farm_id == db_user.farm_id
            )
            .first()
        )

    db.delete(worker)

    if matched_user:
        db.delete(matched_user)

    db.commit()

    create_notification(
        db=db,
        farm_id=db_user.farm_id,
        title="Worker removed",
        message=f"{worker_name} was removed from the workers list.",
        type="worker",
        created_by_id=db_user.id,
    )
    db.commit()

    return None