from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(
    prefix="",
    tags=["marketplace"]
)


def get_db_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


# ---------------------------------------------------------
# LISTINGS
# ---------------------------------------------------------
@router.get("/", response_model=List[schemas.MarketplaceListingRead])
async def list_marketplace_listings(
    category: Optional[str] = None,
    status: Optional[str] = "active",
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(models.MarketplaceListing)

    if status:
        query = query.filter(models.MarketplaceListing.status == status)

    if category:
        query = query.filter(models.MarketplaceListing.category == category)

    if q:
        like = f"%{q}%"
        query = query.filter(
            (models.MarketplaceListing.title.ilike(like)) |
            (models.MarketplaceListing.description.ilike(like)) |
            (models.MarketplaceListing.location.ilike(like))
        )

    items = query.order_by(models.MarketplaceListing.created_at.desc()).all()
    return [schemas.MarketplaceListingRead.model_validate(i) for i in items]


@router.get("/my-listings", response_model=List[schemas.MarketplaceListingRead])
async def get_my_listings(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    items = (
        db.query(models.MarketplaceListing)
        .filter(models.MarketplaceListing.farm_id == db_user.farm_id)
        .order_by(models.MarketplaceListing.created_at.desc())
        .all()
    )

    return [schemas.MarketplaceListingRead.model_validate(i) for i in items]


@router.get("/{listing_id}", response_model=schemas.MarketplaceListingRead)
async def get_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    item = db.query(models.MarketplaceListing).filter(
        models.MarketplaceListing.id == listing_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    return schemas.MarketplaceListingRead.model_validate(item)


@router.post("/", response_model=schemas.MarketplaceListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: schemas.MarketplaceListingCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    data = payload.model_dump(exclude_unset=True)

    item = models.MarketplaceListing(
        **data,
        farm_id=db_user.farm_id,
        created_by_id=db_user.id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return schemas.MarketplaceListingRead.model_validate(item)


@router.put("/{listing_id}", response_model=schemas.MarketplaceListingRead)
async def update_listing(
    listing_id: int,
    payload: schemas.MarketplaceListingUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = db.query(models.MarketplaceListing).filter(
        models.MarketplaceListing.id == listing_id,
        models.MarketplaceListing.farm_id == db_user.farm_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    update_data = payload.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(item, k, v)

    db.commit()
    db.refresh(item)

    return schemas.MarketplaceListingRead.model_validate(item)


@router.put("/{listing_id}/status", response_model=schemas.MarketplaceListingRead)
async def update_listing_status(
    listing_id: int,
    payload: schemas.MarketplaceStatusUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = db.query(models.MarketplaceListing).filter(
        models.MarketplaceListing.id == listing_id,
        models.MarketplaceListing.farm_id == db_user.farm_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    item.status = payload.status
    db.commit()
    db.refresh(item)

    return schemas.MarketplaceListingRead.model_validate(item)


@router.delete("/{listing_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_listing(
    listing_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = db.query(models.MarketplaceListing).filter(
        models.MarketplaceListing.id == listing_id,
        models.MarketplaceListing.farm_id == db_user.farm_id
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(item)
    db.commit()
    return None


# ---------------------------------------------------------
# BUYER REQUESTS
# ---------------------------------------------------------
@router.get("/requests/all", response_model=List[schemas.MarketplaceRequestRead])
async def list_requests(
    category: Optional[str] = None,
    status: Optional[str] = "open",
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    query = db.query(models.MarketplaceRequest)

    if status:
        query = query.filter(models.MarketplaceRequest.status == status)

    if category:
        query = query.filter(models.MarketplaceRequest.category == category)

    items = query.order_by(models.MarketplaceRequest.created_at.desc()).all()
    return [schemas.MarketplaceRequestRead.model_validate(i) for i in items]


@router.post("/requests", response_model=schemas.MarketplaceRequestRead, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: schemas.MarketplaceRequestCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = models.MarketplaceRequest(
        **payload.model_dump(exclude_unset=True),
        farm_id=db_user.farm_id,
        created_by_id=db_user.id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return schemas.MarketplaceRequestRead.model_validate(item)


# ---------------------------------------------------------
# SMART INSIGHTS
# ---------------------------------------------------------
@router.get("/insights", response_model=schemas.MarketplaceInsightsRead)
async def get_marketplace_insights(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # hook smart service here later
    return schemas.MarketplaceInsightsRead(
        trending_categories=[],
        high_demand_requests=0,
        active_listings=0,
        open_requests=0,
        suggestions=[]
    )