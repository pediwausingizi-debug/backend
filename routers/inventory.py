from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.InventoryRead])
def list_inventory(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.InventoryItem).filter(models.InventoryItem.owner_id == current_user.id).all()
    return items


@router.post("/", response_model=schemas.InventoryRead, status_code=status.HTTP_201_CREATED)
def create_inventory_item(payload: schemas.InventoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = models.InventoryItem(**payload.dict(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.InventoryRead)
def get_inventory_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id, models.InventoryItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.InventoryRead)
def update_inventory_item(item_id: int, payload: schemas.InventoryCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id, models.InventoryItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for k, v in payload.dict().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.InventoryItem).filter(models.InventoryItem.id == item_id, models.InventoryItem.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return None
