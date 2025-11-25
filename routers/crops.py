from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to get the actual SQL user
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@router.get("/", response_model=List[schemas.CropRead])
def list_crops(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    crops = db.query(models.Crop).filter(models.Crop.owner_id == db_user.id).all()
    return crops


@router.post("/", response_model=schemas.CropRead, status_code=status.HTTP_201_CREATED)
def create_crop(
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = models.Crop(**payload.dict(), owner_id=db_user.id)
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


@router.get("/{crop_id}", response_model=schemas.CropRead)
def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == db_user.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    return crop


@router.put("/{crop_id}", response_model=schemas.CropRead)
def update_crop(
    crop_id: int,
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == db_user.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    for k, v in payload.dict().items():
        setattr(crop, k, v)

    db.commit()
    db.refresh(crop)
    return crop


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == db_user.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    db.delete(crop)
    db.commit()
    return None


@router.get("/{crop_id}/growth")
def get_crop_growth(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == db_user.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    return {"growth_records": []}


@router.get("/{crop_id}/pests")
def get_crop_pests(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == db_user.id
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    return {"pest_records": []}
