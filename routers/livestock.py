from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to load actual SQLAlchemy user
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[schemas.LivestockRead])
def list_livestock(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    items = db.query(models.Livestock).filter(
        models.Livestock.owner_id == db_user.id
    ).all()

    return items


@router.post("/", response_model=schemas.LivestockRead, status_code=status.HTTP_201_CREATED)
def create_livestock(
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = models.Livestock(
        **payload.dict(),
        created_at=datetime.utcnow(),
        owner_id=db_user.id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get("/{item_id}", response_model=schemas.LivestockRead)
def get_livestock_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.put("/{item_id}", response_model=schemas.LivestockRead)
def update_livestock(
    item_id: int,
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for k, v in payload.dict().items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_livestock(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return None


@router.get("/{item_id}/feed")
def get_livestock_feed(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"feed_records": []}


@router.get("/{item_id}/health")
def get_livestock_health(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"health_records": []}


@router.get("/{item_id}/production")
def get_livestock_production(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return {"production_records": []}
