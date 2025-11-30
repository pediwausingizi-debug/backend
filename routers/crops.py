# routers/crops.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to load real User model
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ---------------------------------------------------------
# GET /crops (cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.CropRead])
async def list_crops(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id
    cache_key = f"crops:list:{uid}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    crops = db.query(models.Crop).filter(models.Crop.owner_id == uid).all()
    payload = [schemas.CropRead.model_validate(c).model_dump() for c in crops]

    await cache_set(cache_key, payload, expire_seconds=300)
    return payload


# ---------------------------------------------------------
# POST /crops  (invalidate caches)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.CropRead, status_code=status.HTTP_201_CREATED)
async def create_crop(
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    crop = models.Crop(**payload.dict(), owner_id=uid)
    db.add(crop)
    db.commit()
    db.refresh(crop)

    await cache_delete(f"crops:list:{uid}")
    await cache_delete(f"dashboard:stats:{uid}")

    return crop


# ---------------------------------------------------------
# GET /crops/{id} (cached)
# ---------------------------------------------------------
@router.get("/{crop_id}", response_model=schemas.CropRead)
async def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"crops:item:{uid}:{crop_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == uid
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    payload = schemas.CropRead.model_validate(crop).model_dump()
    await cache_set(cache_key, payload, expire_seconds=300)
    return payload


# ---------------------------------------------------------
# PUT /crops/{id} (invalidate caches)
# ---------------------------------------------------------
@router.put("/{crop_id}", response_model=schemas.CropRead)
async def update_crop(
    crop_id: int,
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == uid
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    for k, v in payload.dict().items():
        setattr(crop, k, v)

    db.commit()
    db.refresh(crop)

    # invalidate caches
    await cache_delete(f"crops:list:{uid}")
    await cache_delete(f"crops:item:{uid}:{crop_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return crop


# ---------------------------------------------------------
# DELETE /crops/{id} (invalidate caches)
# ---------------------------------------------------------
@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    crop = db.query(models.Crop).filter(
        models.Crop.id == crop_id,
        models.Crop.owner_id == uid
    ).first()

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    db.delete(crop)
    db.commit()

    # invalidate caches
    await cache_delete(f"crops:list:{uid}")
    await cache_delete(f"crops:item:{uid}:{crop_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return None
