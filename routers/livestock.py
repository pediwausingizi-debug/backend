# routers/livestock.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="", tags=["livestock"])


# ---------------------------------------------------------
# Helper — get real user + farm_id
# ---------------------------------------------------------
def get_farm_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to a farm")

    return db_user


def _invalidate_livestock_cache(farm_id: int, item_id: int | None = None):
    keys = [
        f"livestock:list:farm:{farm_id}",
        f"dashboard:stats:farm:{farm_id}",
    ]
    if item_id is not None:
        keys.append(f"livestock:item:farm:{farm_id}:{item_id}")
    return keys


# ---------------------------------------------------------
# GET /api/livestock/   (trailing slash)
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

    animals = (
        db.query(models.Livestock)
        .filter(models.Livestock.farm_id == farm_id)
        .order_by(models.Livestock.id.desc())
        .all()
    )

    serialized = [
        schemas.LivestockRead.model_validate(a).model_dump(mode="json")
        for a in animals
    ]

    await cache_set(cache_key, serialized, expire_seconds=120)
    return serialized


# ---------------------------------------------------------
# POST /api/livestock/
# ---------------------------------------------------------
@router.post("/", response_model=schemas.LivestockRead, status_code=status.HTTP_201_CREATED)
async def create_livestock(
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    data = payload.model_dump(exclude_unset=True)

    animal = models.Livestock(
        **data,
        farm_id=farm_id,
        created_by_id=db_user.id,
        created_at=datetime.utcnow(),  # ok even though model has default
    )

    db.add(animal)
    db.commit()
    db.refresh(animal)

    for k in _invalidate_livestock_cache(farm_id):
        await cache_delete(k)

    return schemas.LivestockRead.model_validate(animal)


# ---------------------------------------------------------
# GET /api/livestock/{id}
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

    animal = (
        db.query(models.Livestock)
        .filter(
            models.Livestock.id == item_id,
            models.Livestock.farm_id == farm_id,
        )
        .first()
    )

    if not animal:
        raise HTTPException(status_code=404, detail="Livestock item not found")

    serialized = schemas.LivestockRead.model_validate(animal).model_dump(mode="json")
    await cache_set(cache_key, serialized, expire_seconds=120)
    return serialized


# ---------------------------------------------------------
# PUT /api/livestock/{id}
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

    animal = (
        db.query(models.Livestock)
        .filter(
            models.Livestock.id == item_id,
            models.Livestock.farm_id == farm_id,
        )
        .first()
    )

    if not animal:
        raise HTTPException(status_code=404, detail="Livestock item not found")

    data = payload.model_dump(exclude_unset=True)

    # ✅ Only update provided fields (prevents null overwrites)
    for k, v in data.items():
        setattr(animal, k, v)

    db.commit()
    db.refresh(animal)

    for k in _invalidate_livestock_cache(farm_id, item_id=item_id):
        await cache_delete(k)

    return schemas.LivestockRead.model_validate(animal)


# ---------------------------------------------------------
# DELETE /api/livestock/{id}
# ---------------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_livestock(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    animal = (
        db.query(models.Livestock)
        .filter(
            models.Livestock.id == item_id,
            models.Livestock.farm_id == farm_id,
        )
        .first()
    )

    if not animal:
        raise HTTPException(status_code=404, detail="Livestock item not found")

    db.delete(animal)
    db.commit()

    for k in _invalidate_livestock_cache(farm_id, item_id=item_id):
        await cache_delete(k)

    return None


# ---------------------------------------------------------
# SIMPLE EXTRA ENDPOINTS (placeholders)
# ---------------------------------------------------------
@router.get("/{item_id}/feed")
async def get_livestock_feed(item_id: int):
    return {"feed_records": []}


@router.get("/{item_id}/health")
async def get_livestock_health(item_id: int):
    return {"health_records": []}


@router.get("/{item_id}/production")
async def get_livestock_production(item_id: int):
    return {"production_records": []}
