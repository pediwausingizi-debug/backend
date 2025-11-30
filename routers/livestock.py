from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils import get_current_user
import models, schemas

router = APIRouter()


# Helper → fetch SQL user
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ---------------------------------------------------------
# GET /livestock  (cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.LivestockRead])
async def list_livestock(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"livestock:list:{uid}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    items = db.query(models.Livestock).filter(
        models.Livestock.owner_id == uid
    ).all()

    payload = [schemas.LivestockRead.model_validate(i).model_dump() for i in items]

    await cache_set(cache_key, payload, expire_seconds=300)
    return payload


# ---------------------------------------------------------
# POST /livestock (invalidates caches)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.LivestockRead, status_code=status.HTTP_201_CREATED)
async def create_livestock(
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = models.Livestock(
        **payload.dict(),
        created_at=datetime.utcnow(),
        owner_id=uid
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    # Clear caches
    await cache_delete(f"livestock:list:{uid}")
    await cache_delete(f"dashboard:stats:{uid}")

    return item


# ---------------------------------------------------------
# GET /livestock/{id} (cached)
# ---------------------------------------------------------
@router.get("/{item_id}", response_model=schemas.LivestockRead)
async def get_livestock_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"livestock:item:{uid}:{item_id}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    payload = schemas.LivestockRead.model_validate(item).model_dump()
    await cache_set(cache_key, payload, expire_seconds=300)

    return payload


# ---------------------------------------------------------
# PUT /livestock/{id} (invalidate caches)
# ---------------------------------------------------------
@router.put("/{item_id}", response_model=schemas.LivestockRead)
async def update_livestock(
    item_id: int,
    payload: schemas.LivestockCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for k, v in payload.dict().items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    await cache_delete(f"livestock:list:{uid}")
    await cache_delete(f"livestock:item:{uid}:{item_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return item


# ---------------------------------------------------------
# DELETE /livestock/{id}
# ---------------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_livestock(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = db.query(models.Livestock).filter(
        models.Livestock.id == item_id,
        models.Livestock.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    await cache_delete(f"livestock:list:{uid}")
    await cache_delete(f"livestock:item:{uid}:{item_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return None


# ---------------------------------------------------------
# Feed / Health / Production (future: AI)
# ---------------------------------------------------------
@router.get("/{item_id}/feed")
def get_livestock_feed(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    return {"feed_records": []}


@router.get("/{item_id}/health")
def get_livestock_health(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    return {"health_records": []}


@router.get("/{item_id}/production")
def get_livestock_production(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    return {"production_records": []}
