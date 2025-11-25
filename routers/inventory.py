from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to get real user from DB
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[schemas.InventoryRead])
def list_inventory(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.owner_id == db_user.id
    ).all()

    return items


@router.post("/", response_model=schemas.InventoryRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = models.InventoryItem(**payload.dict(), owner_id=db_user.id)

    db.add(item)
    db.commit()
    db.refresh(item)

    return item


@router.get("/{item_id}", response_model=schemas.InventoryRead)
def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return item


@router.put("/{item_id}", response_model=schemas.InventoryRead)
def update_inventory_item(
    item_id: int,
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for k, v in payload.dict().items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == db_user.id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return None
