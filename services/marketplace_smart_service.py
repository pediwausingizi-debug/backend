from sqlalchemy.orm import Session
import models


def calculate_price_band(category: str, db: Session):
    listings = (
        db.query(models.MarketplaceListing)
        .filter(
            models.MarketplaceListing.category == category,
            models.MarketplaceListing.status == "active",
            models.MarketplaceListing.price > 0
        )
        .all()
    )

    prices = [float(i.price or 0) for i in listings if (i.price or 0) > 0]
    if not prices:
        return {
            "recommended_price": 0.0,
            "min_price": 0.0,
            "max_price": 0.0,
            "price_position": "unknown",
        }

    return {
        "recommended_price": round(sum(prices) / len(prices), 2),
        "min_price": round(min(prices), 2),
        "max_price": round(max(prices), 2),
    }


def calculate_demand_score(category: str, db: Session) -> float:
    open_requests = (
        db.query(models.MarketplaceRequest)
        .filter(
            models.MarketplaceRequest.category == category,
            models.MarketplaceRequest.status == "open"
        )
        .count()
    )

    active_listings = (
        db.query(models.MarketplaceListing)
        .filter(
            models.MarketplaceListing.category == category,
            models.MarketplaceListing.status == "active"
        )
        .count()
    )

    if open_requests == 0 and active_listings == 0:
        return 0.0

    if active_listings == 0:
        return 95.0

    score = (open_requests / active_listings) * 50
    return max(5.0, min(round(score, 2), 100.0))


def classify_price(price: float, recommended: float) -> str:
    if recommended <= 0:
        return "unknown"

    lower = recommended * 0.9
    upper = recommended * 1.1

    if price < lower:
        return "below"
    if price > upper:
        return "above"
    return "fair"


def calculate_sell_now_score(demand_score: float, price_position: str) -> float:
    score = demand_score
    if price_position == "fair":
        score += 20
    elif price_position == "below":
        score += 10
    elif price_position == "above":
        score -= 15

    return max(0.0, min(round(score, 2), 100.0))


def generate_listing_ai_fields(listing: models.MarketplaceListing, db: Session):
    price_band = calculate_price_band(listing.category, db)
    demand_score = calculate_demand_score(listing.category, db)

    recommended_price = price_band["recommended_price"]
    price_position = classify_price(float(listing.price or 0), recommended_price)
    sell_now_score = calculate_sell_now_score(demand_score, price_position)

    ai_summary = (
        f"Demand score is {demand_score:.0f}/100. "
        f"Recommended price is {recommended_price:.2f}. "
        f"Current pricing looks {price_position}."
    )

    listing.recommended_price = recommended_price
    listing.min_price = price_band["min_price"]
    listing.max_price = price_band["max_price"]
    listing.demand_score = demand_score
    listing.price_position = price_position
    listing.sell_now_score = sell_now_score
    listing.ai_summary = ai_summary

    return listing