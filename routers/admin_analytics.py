from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from database import get_db
from utils.auth_utils import get_current_user
import models
import schemas

router = APIRouter(prefix="", tags=["admin-analytics"])


def get_db_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    return db_user


def ensure_admin(db_user: models.User):
    if db_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")


@router.post("/track", response_model=schemas.UserInteractionRead)
async def track_interaction(
    payload: schemas.UserInteractionCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)

    item = models.UserInteraction(
        user_id=db_user.id,
        farm_id=db_user.farm_id,
        page=payload.page,
        action=payload.action or "page_view",
        details=payload.details,
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return schemas.UserInteractionRead.model_validate(item)


@router.get("/overview", response_model=schemas.AdminAnalyticsOverview)
async def analytics_overview(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    ensure_admin(db_user)

    today_start = datetime.utcnow() - timedelta(hours=24)

    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_farms = db.query(func.count(models.Farm.id)).scalar() or 0
    total_interactions = db.query(func.count(models.UserInteraction.id)).scalar() or 0

    active_users_today = (
        db.query(func.count(func.distinct(models.UserInteraction.user_id)))
        .filter(models.UserInteraction.created_at >= today_start)
        .scalar()
        or 0
    )

    total_livestock = db.query(func.count(models.Livestock.id)).scalar() or 0
    total_crops = db.query(func.count(models.Crop.id)).scalar() or 0
    total_inventory_items = db.query(func.count(models.InventoryItem.id)).scalar() or 0
    total_workers = db.query(func.count(models.Worker.id)).scalar() or 0

    marketplace_listings = db.query(func.count(models.MarketplaceListing.id)).scalar() or 0
    marketplace_requests = db.query(func.count(models.MarketplaceRequest.id)).scalar() or 0
    marketplace_matches = db.query(func.count(models.MarketplaceMatch.id)).scalar() or 0
    marketplace_conversations = db.query(func.count(models.MarketplaceConversation.id)).scalar() or 0

    return schemas.AdminAnalyticsOverview(
        total_users=total_users,
        total_farms=total_farms,
        total_interactions=total_interactions,
        active_users_today=active_users_today,
        total_livestock=total_livestock,
        total_crops=total_crops,
        total_inventory_items=total_inventory_items,
        total_workers=total_workers,
        marketplace_listings=marketplace_listings,
        marketplace_requests=marketplace_requests,
        marketplace_matches=marketplace_matches,
        marketplace_conversations=marketplace_conversations,
    )


@router.get("/pages", response_model=schemas.AdminAnalyticsPageStats)
async def page_stats(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    ensure_admin(db_user)

    rows = (
        db.query(
            models.UserInteraction.page,
            func.count(models.UserInteraction.id).label("total"),
            func.sum(
                case(
                    (models.UserInteraction.action == "page_view", 1),
                    else_=0,
                )
            ).label("visits"),
        )
        .group_by(models.UserInteraction.page)
        .order_by(func.count(models.UserInteraction.id).desc())
        .all()
    )

    pages = []

    for row in rows:
        visits = int(row.visits or 0)
        total = int(row.total or 0)

        pages.append(
            schemas.PageInteractionSummary(
                page=row.page,
                visits=visits,
                actions=max(total - visits, 0),
            )
        )

    return schemas.AdminAnalyticsPageStats(pages=pages)


@router.get("/recent", response_model=list[schemas.AdminRecentInteraction])
async def recent_interactions(
    limit: int = 30,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    ensure_admin(db_user)

    limit = min(max(limit, 1), 100)

    rows = (
        db.query(models.UserInteraction, models.User.email)
        .outerjoin(models.User, models.User.id == models.UserInteraction.user_id)
        .order_by(models.UserInteraction.created_at.desc())
        .limit(limit)
        .all()
    )

    results = []

    for interaction, email in rows:
        results.append(
            schemas.AdminRecentInteraction(
                id=interaction.id,
                user_id=interaction.user_id,
                farm_id=interaction.farm_id,
                user_email=email,
                page=interaction.page,
                action=interaction.action,
                details=interaction.details,
                created_at=interaction.created_at,
            )
        )

    return results