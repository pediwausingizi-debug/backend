from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session

import models


PRO_PRICE = 499.0
PRO_CURRENCY = "KES"


FREE_LIMITS = {
    "livestock": 20,
    "crops": 10,
    "inventory": 20,
    "workers": 3,
    "marketplace_listings": 3,
    "buyer_requests": 3,
    "ai_messages_daily": 5,
}


PRO_FEATURES = {
    "ai_image_analysis",
    "reports_export",
    "advanced_ai",
    "priority_marketplace",
}


def is_user_pro(user: models.User) -> bool:
    """
    Returns True only if user has active Pro subscription.
    """

    if not user:
        return False

    if user.plan != "pro":
        return False

    if user.subscription_status != "active":
        return False

    if user.subscription_expires_at and user.subscription_expires_at < datetime.utcnow():
        return False

    return True


def get_user_plan(user: models.User) -> str:
    if is_user_pro(user):
        return "pro"
    return "free"


def count_feature_usage(db: Session, user: models.User, feature: str) -> int:
    """
    Counts current farm usage for a feature.
    """

    farm_id = user.farm_id

    if feature == "livestock":
        return (
            db.query(models.Livestock)
            .filter(models.Livestock.farm_id == farm_id)
            .count()
        )

    if feature == "crops":
        return (
            db.query(models.Crop)
            .filter(models.Crop.farm_id == farm_id)
            .count()
        )

    if feature == "inventory":
        return (
            db.query(models.InventoryItem)
            .filter(models.InventoryItem.farm_id == farm_id)
            .count()
        )

    if feature == "workers":
        return (
            db.query(models.Worker)
            .filter(models.Worker.farm_id == farm_id)
            .count()
        )

    if feature == "marketplace_listings":
        return (
            db.query(models.MarketplaceListing)
            .filter(
                models.MarketplaceListing.farm_id == farm_id,
                models.MarketplaceListing.status == "active",
            )
            .count()
        )

    if feature == "buyer_requests":
        return (
            db.query(models.MarketplaceRequest)
            .filter(
                models.MarketplaceRequest.farm_id == farm_id,
                models.MarketplaceRequest.status == "open",
            )
            .count()
        )

    return 0


def check_feature_limit(
    db: Session,
    user: models.User,
    feature: str,
):
    """
    Use this before creating records.

    Example:
        check_feature_limit(db, db_user, "livestock")
    """

    if is_user_pro(user):
        return {
            "allowed": True,
            "plan": "pro",
            "feature": feature,
            "current_usage": 0,
            "limit": None,
            "message": "Pro plan active. Unlimited access.",
        }

    limit = FREE_LIMITS.get(feature)

    if limit is None:
        return {
            "allowed": True,
            "plan": "free",
            "feature": feature,
            "current_usage": 0,
            "limit": None,
            "message": "Feature allowed.",
        }

    current_usage = count_feature_usage(db, user, feature)

    if current_usage >= limit:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PLAN_LIMIT_REACHED",
                "feature": feature,
                "plan": "free",
                "current_usage": current_usage,
                "limit": limit,
                "message": f"Free plan limit reached for {feature}. Upgrade to Pro for KES 499/month.",
            },
        )

    return {
        "allowed": True,
        "plan": "free",
        "feature": feature,
        "current_usage": current_usage,
        "limit": limit,
        "message": f"Free plan usage: {current_usage}/{limit}",
    }


def require_pro_feature(
    user: models.User,
    feature: str,
):
    """
    Use this before Pro-only features.

    Example:
        require_pro_feature(db_user, "reports_export")
    """

    if is_user_pro(user):
        return True

    raise HTTPException(
        status_code=403,
        detail={
            "code": "PRO_REQUIRED",
            "feature": feature,
            "plan": "free",
            "price": PRO_PRICE,
            "currency": PRO_CURRENCY,
            "message": f"This feature requires FarmXpat Pro at KES 499/month.",
        },
    )


def get_subscription_status(user: models.User):
    return {
        "plan": get_user_plan(user),
        "subscription_status": user.subscription_status or "inactive",
        "subscription_started_at": user.subscription_started_at,
        "subscription_expires_at": user.subscription_expires_at,
        "is_pro": is_user_pro(user),
        "price": PRO_PRICE,
        "currency": PRO_CURRENCY,
    }