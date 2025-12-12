from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.auth_utils import get_current_user
from database import get_db
import models, schemas

# ✅ Must include empty prefix so main include_router prefix works correctly
router = APIRouter(
    prefix="",
    tags=["Upload"]
)


# --------------------------------------------------------
# Helper → Check user + farm
# --------------------------------------------------------
def get_db_user(user_data, db):
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
# Save image for livestock
# --------------------------------------------------------
@router.post("/animal/{animal_id}")
def save_animal_image(
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
    db.commit()
    db.refresh(animal)

    # Always return JSON-safe response
    return {
        "message": "Image saved",
        "animal": schemas.LivestockRead.model_validate(animal).model_dump()
    }


# --------------------------------------------------------
# POST /upload/crop/{crop_id}
# Save image for crop
# --------------------------------------------------------
@router.post("/crop/{crop_id}")
def save_crop_image(
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
    db.commit()
    db.refresh(crop)

    return {
        "message": "Image saved",
        "crop": schemas.CropRead.model_validate(crop).model_dump()
    }
