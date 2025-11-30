from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from utils.auth_utils import get_current_user
from database import get_db
import models, schemas

router = APIRouter(prefix="/upload", tags=["Upload"])

# ------------------------------
# Save image for livestock
# ------------------------------
@router.post("/animal/{animal_id}")
def save_animal_image(
    animal_id: int,
    payload: schemas.ImageSaveRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    owner_id = user["user_id"]

    animal = (
        db.query(models.Livestock)
        .filter(
            models.Livestock.id == animal_id,
            models.Livestock.owner_id == owner_id
        )
        .first()
    )

    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")

    # Save the URL
    animal.image_url = payload.url
    db.commit()
    db.refresh(animal)

    return {"message": "Image saved", "animal": animal}


# ------------------------------
# Save image for crop
# ------------------------------
@router.post("/crop/{crop_id}")
def save_crop_image(
    crop_id: int,
    payload: schemas.ImageSaveRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    owner_id = user["user_id"]

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.owner_id == owner_id
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    crop.image_url = payload.url
    db.commit()
    db.refresh(crop)

    return {"message": "Image saved", "crop": crop}
