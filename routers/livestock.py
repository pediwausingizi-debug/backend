# routers/livestock.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="/livestock", tags=["Livestock"])


# ---------------------------------------------------------
# Helper — get real user + farm_id
# ---------------------------------------------------------
def get_farm_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User is not assigned to a farm")

    return db_user


# ---------------------------------------------------------
# GET /livestock  (JSON-safe, cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.LivestockRead])
async def list_livestock(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"livestock:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    animals = db.query(models.Livestock).filter(
        models.Livestock.farm_id == farm_id
    ).all()

    # ORM -> JSON dicts (safe)
    serialized = [
        schemas.LivestockRead.model_validate(a).model_dump()
        for a in animals
    ]

    await cache_set(cache_key, serialized)
    return serialized


# ---------------------------------------------------------
# POST /livestock  (create, JSON-safe)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.LivestockRead, status_code=status.HTTP_201_CREATED)
async def create_livestock(
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    animal = models.Livestock(
        **payload.dict(),
        farm_id=farm_id,
        added_by=db_user.id,
        created_at=datetime.utcnow(),
    )

    db.add(animal)
    db.commit()
    db.refresh(animal)

    # Clear caches
    await cache_delete(f"livestock:list:farm:{farm_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return schemas.LivestockRead.model_validate(animal)


# ---------------------------------------------------------
# GET /livestock/{id}  (JSON-safe, cached)
# ---------------------------------------------------------
@router.get("/{item_id}", response_model=schemas.LivestockRead)
async def get_livestock_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"livestock:item:farm:{farm_id}:{item_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    animal = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.farm_id == farm_id
    ).first()

    if not animal:
        raise HTTPException(404, "Livestock item not found")

    serialized = schemas.LivestockRead.model_validate(animal).model_dump()
    await cache_set(cache_key, serialized)

    return serialized


# ---------------------------------------------------------
# PUT /livestock/{id}  (JSON-safe)
# ---------------------------------------------------------
@router.put("/{item_id}", response_model=schemas.LivestockRead)
async def update_livestock(
    item_id: int,
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    animal = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.farm_id == farm_id
    ).first()

    if not animal:
        raise HTTPException(404, "Livestock item not found")

    for k, v in payload.dict().items():
        setattr(animal, k, v)

    db.commit()
    db.refresh(animal)

    await cache_delete(f"livestock:list:farm:{farm_id}")
    await cache_delete(f"livestock:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return schemas.LivestockRead.model_validate(animal)


# ---------------------------------------------------------
# DELETE /livestock/{id}
# ---------------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_livestock(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    animal = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.farm_id == farm_id
    ).first()

    if not animal:
        raise HTTPException(404, "Livestock item not found")

    db.delete(animal)
    db.commit()

    await cache_delete(f"livestock:list:farm:{farm_id}")
    await cache_delete(f"livestock:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return None


# ---------------------------------------------------------
# ADDITIONAL SIMPLE ENDPOINTS
# ---------------------------------------------------------
@router.get("/{item_id}/feed")
def get_livestock_feed(item_id: int):
    return {"feed_records": []}

@router.get("/{item_id}/health")
def get_livestock_health(item_id: int):
    return {"health_records": []}

@router.get("/{item_id}/production")
def get_livestock_production(item_id: int):
    return {"production_records": []}
