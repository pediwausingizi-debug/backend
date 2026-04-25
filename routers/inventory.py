from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(
    prefix="",
    tags=["inventory"]
)


# ---------------------------------------------------------
# Helper – get real user + farm_id
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
        raise HTTPException(status_code=400, detail="User is not assigned to any farm")

    return db_user


# ---------------------------------------------------------
# GET /inventory/
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

    items = (
        db.query(models.InventoryItem)
        .filter(models.InventoryItem.farm_id == farm_id)
        .order_by(models.InventoryItem.id.desc())
        .all()
    )

    serialized = [
        schemas.InventoryRead.model_validate(i).model_dump(mode="json")
        for i in items
    ]

    await cache_set(cache_key, serialized)
    return serialized


# ---------------------------------------------------------
# POST /inventory/
# ---------------------------------------------------------
@router.post("/", response_model=schemas.InventoryRead, status_code=status.HTTP_201_CREATED)
async def create_inventory_item(
    payload: schemas.InventoryCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    data = payload.model_dump()

    quantity = float(data.get("quantity", 0) or 0)
    reorder_level = data.get("reorder_level")
    price = data.get("price")

    if quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    if reorder_level is not None and float(reorder_level) < 0:
        raise HTTPException(status_code=400, detail="Reorder level cannot be negative")

    if price is not None and float(price) < 0:
        raise HTTPException(status_code=400, detail="Price cannot be negative")

    item = models.InventoryItem(
        **data,
        farm_id=farm_id,
        created_by_id=db_user.id
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")
    await cache_delete(f"dashboard:alerts:farm:{farm_id}")
    await cache_delete(f"reports:inventory:farm:{farm_id}")

    return schemas.InventoryRead.model_validate(item)


# ---------------------------------------------------------
# GET /inventory/{id}
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

    item = (
        db.query(models.InventoryItem)
        .filter(
            models.InventoryItem.id == item_id,
            models.InventoryItem.farm_id == farm_id
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    serialized = schemas.InventoryRead.model_validate(item).model_dump(mode="json")
    await cache_set(cache_key, serialized)

    return serialized


# ---------------------------------------------------------
# PUT /inventory/{id}
# Partial update safe
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

    item = (
        db.query(models.InventoryItem)
        .filter(
            models.InventoryItem.id == item_id,
            models.InventoryItem.farm_id == farm_id
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "quantity" in update_data and float(update_data["quantity"]) < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")

    if "reorder_level" in update_data and update_data["reorder_level"] is not None:
        if float(update_data["reorder_level"]) < 0:
            raise HTTPException(status_code=400, detail="Reorder level cannot be negative")

    if "price" in update_data and update_data["price"] is not None:
        if float(update_data["price"]) < 0:
            raise HTTPException(status_code=400, detail="Price cannot be negative")

    for k, v in update_data.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"inventory:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")
    await cache_delete(f"dashboard:alerts:farm:{farm_id}")
    await cache_delete(f"reports:inventory:farm:{farm_id}")

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

    item = (
        db.query(models.InventoryItem)
        .filter(
            models.InventoryItem.id == item_id,
            models.InventoryItem.farm_id == farm_id
        )
        .first()
    )

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    await cache_delete(f"inventory:list:farm:{farm_id}")
    await cache_delete(f"inventory:item:farm:{farm_id}:{item_id}")
    await cache_delete(f"dashboard:stats:farm:{farm_id}")
    await cache_delete(f"dashboard:alerts:farm:{farm_id}")
    await cache_delete(f"reports:inventory:farm:{farm_id}")

    return None