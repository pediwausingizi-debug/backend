from sqlalchemy.orm import Session
from typing import List
import models


def calculate_match_score(
    listing: models.MarketplaceListing,
    request: models.MarketplaceRequest
) -> tuple[float, str]:
    score = 0
    reasons = []

    # Category match
    if listing.category and request.category:
        if listing.category.lower() == request.category.lower():
            score += 40
            reasons.append("Same product category")

    # Quantity match
    if listing.quantity and request.quantity_needed:
        if listing.quantity >= request.quantity_needed:
            score += 20
            reasons.append("Listing quantity can satisfy request")
        else:
            partial_score = (listing.quantity / request.quantity_needed) * 20
            score += max(0, partial_score)
            reasons.append("Listing can partially satisfy request")

    # Price match
    if listing.price and request.target_price and request.target_price > 0:
        if listing.price <= request.target_price:
            score += 25
            reasons.append("Listing price is within buyer target price")
        else:
            difference = listing.price - request.target_price
            penalty_ratio = difference / request.target_price
            price_score = max(0, 25 - (penalty_ratio * 25))
            score += price_score
            reasons.append("Listing price is close to buyer target price")

    # Location match
    if listing.location and request.location:
        if listing.location.lower() == request.location.lower():
            score += 15
            reasons.append("Same location")
        elif request.location.lower() in listing.location.lower() or listing.location.lower() in request.location.lower():
            score += 8
            reasons.append("Nearby or related location")

    final_score = round(min(score, 100), 2)

    if not reasons:
        reasons.append("Basic match based on available marketplace data")

    return final_score, ", ".join(reasons)


def generate_matches_for_request(
    db: Session,
    request: models.MarketplaceRequest,
    minimum_score: float = 40
) -> List[models.MarketplaceMatch]:
    listings = (
        db.query(models.MarketplaceListing)
        .filter(
            models.MarketplaceListing.status == "active",
            models.MarketplaceListing.category == request.category
        )
        .all()
    )

    created_matches = []

    for listing in listings:
        # Avoid matching buyer's own farm listing
        if request.farm_id and listing.farm_id == request.farm_id:
            continue

        existing_match = (
            db.query(models.MarketplaceMatch)
            .filter(
                models.MarketplaceMatch.listing_id == listing.id,
                models.MarketplaceMatch.request_id == request.id
            )
            .first()
        )

        if existing_match:
            continue

        score, reason = calculate_match_score(listing, request)

        if score >= minimum_score:
            match = models.MarketplaceMatch(
                listing_id=listing.id,
                request_id=request.id,
                match_score=score,
                reason=reason,
            )

            db.add(match)
            created_matches.append(match)

    db.commit()

    for match in created_matches:
        db.refresh(match)

    return created_matches