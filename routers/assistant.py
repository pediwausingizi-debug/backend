from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from utils.auth_utils import get_current_user
import models

from services.recommendation_service import build_recommendations
from services.prediction_service import build_predictions
from services.gemini_service import generate_chat_reply
from services.gemini_vision_service import analyze_farm_image_bytes

router = APIRouter(prefix="", tags=["assistant"])


def get_farm_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User not assigned to a farm")

    return db_user


def build_assistant_summary_data(db: Session, farm_id: int) -> dict:
    animal_count = (
        db.query(func.count(models.Animal.id))
        .filter(models.Animal.farm_id == farm_id)
        .scalar()
        or 0
    )

    crop_cycle_count = (
        db.query(func.count(models.CropCycle.id))
        .filter(models.CropCycle.farm_id == farm_id)
        .scalar()
        or 0
    )

    plot_count = (
        db.query(func.count(models.Plot.id))
        .filter(models.Plot.farm_id == farm_id)
        .scalar()
        or 0
    )

    total_animal_income = (
        db.query(func.sum(models.AnimalIncome.amount))
        .join(models.Animal, models.Animal.id == models.AnimalIncome.animal_id)
        .filter(models.Animal.farm_id == farm_id)
        .scalar()
        or 0.0
    )

    total_animal_expenses = (
        db.query(func.sum(models.AnimalExpense.amount))
        .join(models.Animal, models.Animal.id == models.AnimalExpense.animal_id)
        .filter(models.Animal.farm_id == farm_id)
        .scalar()
        or 0.0
    )

    total_crop_income = (
        db.query(func.sum(models.CropCycleIncome.amount))
        .join(models.CropCycle, models.CropCycle.id == models.CropCycleIncome.crop_cycle_id)
        .filter(models.CropCycle.farm_id == farm_id)
        .scalar()
        or 0.0
    )

    total_crop_expenses = (
        db.query(func.sum(models.CropCycleExpense.amount))
        .join(models.CropCycle, models.CropCycle.id == models.CropCycleExpense.crop_cycle_id)
        .filter(models.CropCycle.farm_id == farm_id)
        .scalar()
        or 0.0
    )

    total_income = float(total_animal_income) + float(total_crop_income)
    total_expenses = float(total_animal_expenses) + float(total_crop_expenses)

    summary_lines = []

    if total_income > total_expenses:
        summary_lines.append("The farm is currently operating at a positive margin.")
    elif total_expenses > total_income:
        summary_lines.append("The farm is currently spending more than it earns.")
    else:
        summary_lines.append("The farm is currently at break-even based on recorded income and expenses.")

    if animal_count > 0:
        summary_lines.append(f"There are {animal_count} individual animals being tracked.")

    if crop_cycle_count > 0:
        summary_lines.append(f"There are {crop_cycle_count} crop cycles across {plot_count} plots.")

    return {
        "farm_id": farm_id,
        "animals_tracked": animal_count,
        "plots_tracked": plot_count,
        "crop_cycles_tracked": crop_cycle_count,
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "net_profit": round(total_income - total_expenses, 2),
        "summary": " ".join(summary_lines),
    }


@router.get("/summary")
async def get_assistant_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    return build_assistant_summary_data(db, db_user.farm_id)


@router.get("/recommendations")
async def get_recommendations(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    return build_recommendations(db, db_user.farm_id)


@router.get("/predictions")
async def get_predictions(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    return build_predictions(db, db_user.farm_id)


@router.get("/livestock-insights")
async def get_livestock_insights(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    recs = build_recommendations(db, db_user.farm_id)
    return {
        "items": recs["livestock"],
        "total": len(recs["livestock"]),
    }


@router.get("/crop-insights")
async def get_crop_insights(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    recs = build_recommendations(db, db_user.farm_id)
    return {
        "items": recs["crops"],
        "total": len(recs["crops"]),
    }


@router.post("/chat")
async def chat_assistant(
    payload: dict,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id
    raw_message = (payload.get("message") or "").strip()

    if not raw_message:
        raise HTTPException(status_code=400, detail="Message is required")

    summary = build_assistant_summary_data(db, farm_id)
    recommendations = build_recommendations(db, farm_id)
    predictions = build_predictions(db, farm_id)

    try:
        reply = generate_chat_reply(
            user_message=raw_message,
            summary=summary,
            recommendations=recommendations,
            predictions=predictions,
        )
    except Exception:
        reply = (
            f"{summary['summary']} "
            f"Current net profit is {summary['net_profit']:.2f}. "
            f"There are {recommendations['total']} recommendation(s) available."
        )

    return {
        "message": raw_message,
        "reply": reply,
        "summary": summary,
        "recommendation_count": recommendations["total"],
    }


@router.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...),
    note: str = Form(default=""),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are allowed")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Uploaded image is empty")

    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB allowed.")

    try:
        result = analyze_farm_image_bytes(
            image_bytes=image_bytes,
            mime_type=file.content_type,
            note=note,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

    return {
        "reply": result["reply"],
        "note": result["note"],
        "filename": file.filename,
        "content_type": file.content_type,
        "farm_id": db_user.farm_id,
    }