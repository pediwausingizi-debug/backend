from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


@router.get("/", response_model=List[schemas.LivestockRead])
def list_livestock(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    items = db.query(models.Livestock).filter(models.Livestock.owner_id == current_user.id).all()
    return items


@router.post("/", response_model=schemas.LivestockRead, status_code=status.HTTP_201_CREATED)
def create_livestock(payload: schemas.LivestockCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = models.Livestock(**payload.dict(), created_at=datetime.utcnow(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=schemas.LivestockRead)
def get_livestock_item(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@router.put("/{item_id}", response_model=schemas.LivestockRead)
def update_livestock(item_id: int, payload: schemas.LivestockCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    for k, v in payload.dict().items():
        setattr(item, k, v)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_livestock(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    db.delete(item)
    db.commit()
    return None


@router.get("/{item_id}/feed")
def get_livestock_feed(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # implement feed records later
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"feed_records": []}


@router.get("/{item_id}/health")
def get_livestock_health(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"health_records": []}


@router.get("/{item_id}/production")
def get_livestock_production(item_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    item = db.query(models.Livestock).filter(models.Livestock.id == item_id, models.Livestock.owner_id == current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"production_records": []}
