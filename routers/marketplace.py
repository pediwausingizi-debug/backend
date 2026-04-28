from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from utils.auth_utils import get_current_user
from services.marketplace_matching import generate_matches_for_request
from services.marketplace_smart_service import generate_listing_ai_fields

import models
import schemas

router = APIRouter(prefix="", tags=["marketplace"])


def get_db_user(user_data, db: Session) -> models.User:
    db_user = db.query(models.User).filter(
        models.User.id == user_data["user_id"]
    ).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to a farm")

    return db_user


# ---------------------------------------------------------
# MATCHES
# ---------------------------------------------------------
@router.get("/requests/{request_id}/matches", response_model=List[schemas.MarketplaceMatchRead])
async def get_request_matches(
    request_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    request = db.query(models.MarketplaceRequest).filter(
        models.MarketplaceRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.created_by_id != db_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to view these matches")

    matches = (
        db.query(models.MarketplaceMatch)
        .filter(models.MarketplaceMatch.request_id == request_id)
        .order_by(models.MarketplaceMatch.match_score.desc())
        .all()
    )

    return [schemas.MarketplaceMatchRead.model_validate(m) for m in matches]


@router.get("/my-listing-matches", response_model=List[schemas.MarketplaceMatchRead])
async def get_my_listing_matches(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    matches = (
        db.query(models.MarketplaceMatch)
        .join(models.MarketplaceListing)
        .filter(models.MarketplaceListing.farm_id == db_user.farm_id)
        .order_by(models.MarketplaceMatch.match_score.desc())
        .all()
    )

    return [schemas.MarketplaceMatchRead.model_validate(m) for m in matches]


@router.post("/requests/{request_id}/rematch", response_model=List[schemas.MarketplaceMatchRead])
async def rematch_request(
    request_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    request = db.query(models.MarketplaceRequest).filter(
        models.MarketplaceRequest.id == request_id
    ).first()

    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    if request.created_by_id != db_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to rematch this request")

    matches = generate_matches_for_request(db, request)

    return [schemas.MarketplaceMatchRead.model_validate(m) for m in matches]


@router.post("/matches/{match_id}/accept", response_model=schemas.MarketplaceMatchAcceptResponse)
async def accept_marketplace_match(
    match_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    match = db.query(models.MarketplaceMatch).filter(
        models.MarketplaceMatch.id == match_id
    ).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    listing = match.listing
    request = match.request

    if not listing or not request:
        raise HTTPException(status_code=400, detail="Invalid match data")

    is_listing_owner = listing.created_by_id == db_user.id
    is_request_owner = request.created_by_id == db_user.id

    if not is_listing_owner and not is_request_owner:
        raise HTTPException(status_code=403, detail="Not allowed to accept this match")

    buyer_user_id = request.created_by_id
    seller_user_id = listing.created_by_id

    if not buyer_user_id or not seller_user_id:
        raise HTTPException(status_code=400, detail="Missing listing or request owner")

    if buyer_user_id == seller_user_id:
        raise HTTPException(status_code=400, detail="Cannot create conversation with yourself")

    existing_conversation = (
        db.query(models.MarketplaceConversation)
        .filter(
            models.MarketplaceConversation.listing_id == listing.id,
            models.MarketplaceConversation.request_id == request.id,
        )
        .first()
    )

    if existing_conversation:
        match.status = "accepted"
        request.status = "matched"
        db.commit()
        db.refresh(match)
        db.refresh(existing_conversation)

        return schemas.MarketplaceMatchAcceptResponse(
            match=schemas.MarketplaceMatchRead.model_validate(match),
            conversation=schemas.MarketplaceConversationRead.model_validate(existing_conversation),
        )

    conversation = models.MarketplaceConversation(
        conversation_type="request",
        title=f"{request.title} ↔ {listing.title}",
        listing_id=listing.id,
        request_id=request.id,
        created_by_id=db_user.id,
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    db.add_all([
        models.MarketplaceConversationParticipant(
            conversation_id=conversation.id,
            user_id=buyer_user_id,
        ),
        models.MarketplaceConversationParticipant(
            conversation_id=conversation.id,
            user_id=seller_user_id,
        ),
    ])

    db.add(
        models.MarketplaceMessage(
            conversation_id=conversation.id,
            sender_id=db_user.id,
            message_type="system",
            content="Marketplace match accepted. You can now discuss the order details here.",
        )
    )

    match.status = "accepted"
    request.status = "matched"

    db.commit()
    db.refresh(match)
    db.refresh(conversation)

    return schemas.MarketplaceMatchAcceptResponse(
        match=schemas.MarketplaceMatchRead.model_validate(match),
        conversation=schemas.MarketplaceConversationRead.model_validate(conversation),
    )


@router.post("/matches/{match_id}/reject", response_model=schemas.MarketplaceMatchRead)
async def reject_marketplace_match(
    match_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    match = db.query(models.MarketplaceMatch).filter(
        models.MarketplaceMatch.id == match_id
    ).first()

    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    listing = match.listing
    request = match.request

    if not listing or not request:
        raise HTTPException(status_code=400, detail="Invalid match data")

    is_listing_owner = listing.created_by_id == db_user.id
    is_request_owner = request.created_by_id == db_user.id

    if not is_listing_owner and not is_request_owner:
        raise HTTPException(status_code=403, detail="Not allowed to reject this match")

    match.status = "rejected"
    db.commit()
    db.refresh(match)

    return schemas.MarketplaceMatchRead.model_validate(match)


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


@router.post("/", response_model=schemas.MarketplaceListingRead, status_code=status.HTTP_201_CREATED)
async def create_listing(
    payload: schemas.MarketplaceListingCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = models.MarketplaceListing(
        **payload.model_dump(exclude_unset=True),
        farm_id=db_user.farm_id,
        created_by_id=db_user.id,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    generate_listing_ai_fields(item, db)

    db.commit()
    db.refresh(item)

    return schemas.MarketplaceListingRead.model_validate(item)


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

    generate_matches_for_request(db, item)

    return schemas.MarketplaceRequestRead.model_validate(item)


# ---------------------------------------------------------
# SMART INSIGHTS
# ---------------------------------------------------------
@router.get("/insights", response_model=schemas.MarketplaceInsightsRead)
async def get_marketplace_insights(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    active_listings = db.query(models.MarketplaceListing).filter(
        models.MarketplaceListing.status == "active"
    ).count()

    open_requests = db.query(models.MarketplaceRequest).filter(
        models.MarketplaceRequest.status == "open"
    ).count()

    high_demand_requests = db.query(models.MarketplaceRequest).filter(
        models.MarketplaceRequest.status == "open",
        models.MarketplaceRequest.demand_score >= 70,
    ).count()

    categories = (
        db.query(models.MarketplaceRequest.category)
        .filter(models.MarketplaceRequest.status == "open")
        .all()
    )

    category_counts = {}
    for row in categories:
        category = row[0]
        if category:
            category_counts[category] = category_counts.get(category, 0) + 1

    trending_categories = sorted(
        category_counts,
        key=category_counts.get,
        reverse=True,
    )[:5]

    suggestions = []

    if open_requests > active_listings:
        suggestions.append("There are more buyer requests than active listings. Farmers should consider posting more products.")

    if active_listings == 0:
        suggestions.append("No active listings are available. Add farm products to make the marketplace useful.")

    if open_requests == 0:
        suggestions.append("No open buyer requests are available yet. Encourage buyers to post demand.")

    return schemas.MarketplaceInsightsRead(
        trending_categories=trending_categories,
        high_demand_requests=high_demand_requests,
        active_listings=active_listings,
        open_requests=open_requests,
        suggestions=suggestions,
    )


# ---------------------------------------------------------
# DYNAMIC LISTING ROUTES MUST STAY LAST
# ---------------------------------------------------------
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
        models.MarketplaceListing.farm_id == db_user.farm_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    update_data = payload.model_dump(exclude_unset=True)

    for k, v in update_data.items():
        setattr(item, k, v)

    generate_listing_ai_fields(item, db)

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
        models.MarketplaceListing.farm_id == db_user.farm_id,
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
        models.MarketplaceListing.farm_id == db_user.farm_id,
    ).first()

    if not item:
        raise HTTPException(status_code=404, detail="Listing not found")

    db.delete(item)
    db.commit()

    return None