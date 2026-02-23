from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="", tags=["crops"])


# --------------------------------------------
# Helper: load user + validate farm
# --------------------------------------------
def get_farm_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User not assigned to a farm")

    return db_user


def _invalidate_crop_cache(farm_id: int, crop_id: int | None = None):
    keys = [
        f"crops:list:farm:{farm_id}",
        f"dashboard:stats:farm:{farm_id}",
    ]
    if crop_id is not None:
        keys.append(f"crops:item:farm:{farm_id}:{crop_id}")
    return keys


# --------------------------------------------
# GET /api/crops
# --------------------------------------------
@router.get("", response_model=List[schemas.CropRead])
async def list_crops(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crops:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crops = (
        db.query(models.Crop)
        .filter(models.Crop.farm_id == farm_id)
        .order_by(models.Crop.id.desc())
        .all()
    )

    payload = [
        schemas.CropRead.model_validate(c).model_dump(mode="json")
        for c in crops
    ]

    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


# --------------------------------------------
# POST /api/crops
# --------------------------------------------
@router.post("", response_model=schemas.CropRead, status_code=201)
async def create_crop(
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    data = payload.model_dump(exclude_unset=True)

    crop = models.Crop(**data, farm_id=farm_id, created_by_id=db_user.id)

    db.add(crop)
    db.commit()
    db.refresh(crop)

    # Invalidate cache
    for k in _invalidate_crop_cache(farm_id):
        await cache_delete(k)

    return schemas.CropRead.model_validate(crop)


# --------------------------------------------
# GET /api/crops/{crop_id}
# --------------------------------------------
@router.get("/{crop_id}", response_model=schemas.CropRead)
async def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crops:item:farm:{farm_id}:{crop_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    payload = schemas.CropRead.model_validate(crop).model_dump(mode="json")
    await cache_set(cache_key, payload, expire_seconds=120)

    return payload


# --------------------------------------------
# PUT /api/crops/{crop_id}
# --------------------------------------------
@router.put("/{crop_id}", response_model=schemas.CropRead)
async def update_crop(
    crop_id: int,
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    data = payload.model_dump(exclude_unset=True)

    # ✅ Only update provided fields (prevents accidental null overwrites)
    for k, v in data.items():
        setattr(crop, k, v)

    db.commit()
    db.refresh(crop)

    # Invalidate cache
    for k in _invalidate_crop_cache(farm_id, crop_id=crop_id):
        await cache_delete(k)

    return schemas.CropRead.model_validate(crop)


# --------------------------------------------
# DELETE /api/crops/{crop_id}
# --------------------------------------------
@router.delete("/{crop_id}", status_code=204)
async def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    db.delete(crop)
    db.commit()

    # Invalidate cache
    for k in _invalidate_crop_cache(farm_id, crop_id=crop_id):
        await cache_delete(k)

    return None
