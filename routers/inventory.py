# routers/inventory.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(tags=["Inventory"])


# ---------------------------------------------------------
# Helper – get real user + farm_id
# ---------------------------------------------------------
def get_farm_user(user_data, db):
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(404, "User not found")

    if not db_user.farm_id:
        raise HTTPException(400, "User is not assigned to any farm")

    return db_user


# ---------------------------------------------------------
# GET /inventory  (JSON-safe, cached)
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.InventoryRead])
async def list_inventory(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"inventory:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    items = db.query(models.InventoryItem).filter(
        models.InventoryItem.farm_id == farm_id
    ).all()

    # Convert ORM → JSON dicts (safe for Redis)
    serialized = [
        schemas.InventoryRead.model_validate(i).model_dump()
        for i in items
    ]

    await cache_set(cache_key, serialized)
    return serialized


# ---------------------------------------------------------
# POST /inventory  (JSON-safe)
# ---------------------------------------------------------
@router.post("/", response_model=schemas.InventoryRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    item = models.InventoryItem(
        **payload.dict(),
        farm_id=farm_id,
        added_by=db_user.id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    # Invalidate caches
    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return schemas.InventoryRead.model_validate(item)


# ---------------------------------------------------------
# GET /inventory/{id}  (JSON-safe, cached)
# ---------------------------------------------------------
@router.get("/{item_id}", response_model=schemas.InventoryRead)
async def get_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"inventory:item:farm:{farm_id}:{item_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.farm_id == farm_id
    ).first()

    if not item:
        raise HTTPException(404, "Item not found")

    serialized = schemas.InventoryRead.model_validate(item).model_dump()
    await cache_set(cache_key, serialized)

    return serialized


# ---------------------------------------------------------
# PUT /inventory/{id}  (JSON-safe)
# ---------------------------------------------------------
@router.put("/{item_id}", response_model=schemas.InventoryRead)
async def update_inventory_item(
    item_id: int,
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.farm_id == farm_id
    ).first()

    if not item:
        raise HTTPException(404, "Item not found")

    for k, v in payload.dict().items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    # Clear caches
    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"inventory:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return schemas.InventoryRead.model_validate(item)


# ---------------------------------------------------------
# DELETE /inventory/{id}
# ---------------------------------------------------------
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_inventory_item(
    item_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):

    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    item = db.query(models.InventoryItem).filter(
        models.InventoryItem.id == item_id,
        models.InventoryItem.farm_id == farm_id
    ).first()

    if not item:
        raise HTTPException(404, "Item not found")

    db.delete(item)
    db.commit()

    # Clear caches
    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"inventory:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")

    return None
