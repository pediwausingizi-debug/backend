# routers/inventory.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter()


# Helper to get actual User object
def get_db_user(user_data, db):
    db_user = db.query(models.User).filter(models.User.id == user_data["user_id"]).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ---------------------------------------------------------
# GET /inventory  (cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.InventoryRead])
async def list_inventory(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"inventory:list:{uid}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.owner_id == uid
    ).all()

    payload = [schemas.InventoryRead.model_validate(i).model_dump() for i in items]

    await cache_set(cache_key, payload, expire_seconds=300)
    return payload


# ---------------------------------------------------------
# POST /inventory  (clear list + dashboard caches)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.InventoryRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = models.InventoryItem(**payload.dict(), owner_id=uid)

    db.add(item)
    db.commit()
    db.refresh(item)

    await cache_delete(f"inventory:list:{uid}")
    await cache_delete(f"dashboard:stats:{uid}")

    return item


# ---------------------------------------------------------
# GET /inventory/{id} (cached)
# ---------------------------------------------------------
@router.get("/{item_id}", response_model=schemas.InventoryRead)
async def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    cache_key = f"inventory:item:{uid}:{item_id}"
    cached = await cache_get(cache_key)

    if cached:
        return cached

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    payload = schemas.InventoryRead.model_validate(item).model_dump()
    await cache_set(cache_key, payload, expire_seconds=300)

    return payload


# ---------------------------------------------------------
# PUT /inventory/{id} (clear caches)
# ---------------------------------------------------------
@router.put("/{item_id}", response_model=schemas.InventoryRead)
async def update_inventory_item(
    item_id: int,
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    for k, v in payload.dict().items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    # clear caches
    await cache_delete(f"inventory:list:{uid}")
    await cache_delete(f"inventory:item:{uid}:{item_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return item


# ---------------------------------------------------------
# DELETE /inventory/{id} (clear caches)
# ---------------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_db_user(user, db)
    uid = db_user.id

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.owner_id == uid
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    await cache_delete(f"inventory:list:{uid}")
    await cache_delete(f"inventory:item:{uid}:{item_id}")
    await cache_delete(f"dashboard:stats:{uid}")

    return None
