from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.auth_utils import get_current_user
from database import get_db
from utils.cache import cache_delete  # ✅ ADD
import models, schemas

router = APIRouter(prefix="", tags=["Upload"])


def get_db_user(user_data, db: Session) -> models.User:
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User has no assigned farm")

    return db_user


# --------------------------------------------------------
# POST /upload/animal/{animal_id}
# Save image for livestock (url + optional public_id)
# --------------------------------------------------------
@router.post("/animal/{animal_id}")
async def save_animal_image(
    animal_id: int,
    payload: schemas.ImageSaveRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    farm_id = db_user.farm_id

    animal = (
        db.query(models.Livestock)
        .filter(
            models.Livestock.id == animal_id,
            models.Livestock.farm_id == farm_id,
        )
        .first()
    )

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    animal.image_url = payload.url

    # ✅ Save public_id if provided (only if model column exists)
    if payload.public_id:
        animal.image_public_id = payload.public_id

    db.commit()
    db.refresh(animal)

    # ✅ Invalidate caches so frontend sees updated image immediately
    await cache_delete(f"livestock:list:farm:{farm_id}")
    await cache_delete(f"livestock:item:farm:{farm_id}:{animal_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return {
        "message": "Image saved",
        "animal": schemas.LivestockRead.model_validate(animal).model_dump(mode="json"),
    }


# --------------------------------------------------------
# POST /upload/crop/{crop_id}
# Save image for crop (url + optional public_id)
# --------------------------------------------------------
@router.post("/crop/{crop_id}")
async def save_crop_image(
    crop_id: int,
    payload: schemas.ImageSaveRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
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

    crop.image_url = payload.url

    if payload.public_id:
        crop.image_public_id = payload.public_id

    db.commit()
    db.refresh(crop)

    # ✅ Invalidate caches
    await cache_delete(f"crops:list:farm:{farm_id}")
    await cache_delete(f"crops:item:farm:{farm_id}:{crop_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return {
        "message": "Image saved",
        "crop": schemas.CropRead.model_validate(crop).model_dump(mode="json"),
    }
