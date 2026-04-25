from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from utils.cache import cache_get, cache_set, cache_delete
from database import get_db
from utils.auth_utils import get_current_user
import models, schemas

router = APIRouter(prefix="", tags=["crops"])


# ---------------------------------------------------------
# Helper: load user + validate farm
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
        raise HTTPException(status_code=400, detail="User not assigned to a farm")

    return db_user


def _invalidate_crop_cache(farm_id: int, crop_id: int | None = None):
    keys = [
        f"crops:list:farm:{farm_id}",
        f"dashboard:stats:farm:{farm_id}",
    ]
    if crop_id is not None:
        keys.append(f"crops:item:farm:{farm_id}:{crop_id}")
    return keys


def _invalidate_plot_cache(farm_id: int, plot_id: int | None = None):
    keys = [
        f"plots:list:farm:{farm_id}",
        f"dashboard:stats:farm:{farm_id}",
    ]
    if plot_id is not None:
        keys.append(f"plots:item:farm:{farm_id}:{plot_id}")
    return keys


def _invalidate_crop_cycle_cache(farm_id: int, cycle_id: int | None = None):
    keys = [
        f"crop_cycles:list:farm:{farm_id}",
        f"dashboard:stats:farm:{farm_id}",
    ]
    if cycle_id is not None:
        keys.append(f"crop_cycles:item:farm:{farm_id}:{cycle_id}")
    return keys


# =========================================================
# CROP CRUD
# =========================================================

@router.get("", response_model=List[schemas.CropRead])
async def list_crops(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crops:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crops = (
        db.query(models.Crop)
        .filter(models.Crop.farm_id == farm_id)
        .order_by(models.Crop.id.desc())
        .all()
    )

    payload = [
        schemas.CropRead.model_validate(c).model_dump(mode="json")
        for c in crops
    ]

    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.post("", response_model=schemas.CropRead, status_code=status.HTTP_201_CREATED)
async def create_crop(
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    data = payload.model_dump(exclude_unset=True)
    crop = models.Crop(**data, farm_id=farm_id, created_by_id=db_user.id)

    db.add(crop)
    db.commit()
    db.refresh(crop)

    for k in _invalidate_crop_cache(farm_id):
        await cache_delete(k)

    return schemas.CropRead.model_validate(crop)


@router.get("/{crop_id}", response_model=schemas.CropRead)
async def get_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crops:item:farm:{farm_id}:{crop_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    payload = schemas.CropRead.model_validate(crop).model_dump(mode="json")
    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.put("/{crop_id}", response_model=schemas.CropRead)
async def update_crop(
    crop_id: int,
    payload: schemas.CropCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(crop, k, v)

    db.commit()
    db.refresh(crop)

    for k in _invalidate_crop_cache(farm_id, crop_id=crop_id):
        await cache_delete(k)

    return schemas.CropRead.model_validate(crop)


@router.delete("/{crop_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop(
    crop_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )

    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    db.delete(crop)
    db.commit()

    for k in _invalidate_crop_cache(farm_id, crop_id=crop_id):
        await cache_delete(k)

    return None


# =========================================================
# PLOT CRUD
# =========================================================

@router.get("/plots", response_model=List[schemas.PlotRead])
async def list_plots(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"plots:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    plots = (
        db.query(models.Plot)
        .filter(models.Plot.farm_id == farm_id)
        .order_by(models.Plot.id.desc())
        .all()
    )

    payload = [
        schemas.PlotRead.model_validate(p).model_dump(mode="json")
        for p in plots
    ]

    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.post("/plots", response_model=schemas.PlotRead, status_code=status.HTTP_201_CREATED)
async def create_plot(
    payload: schemas.PlotCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    plot = models.Plot(
        **payload.model_dump(exclude_unset=True),
        farm_id=farm_id,
        created_by_id=db_user.id,
    )

    db.add(plot)
    db.commit()
    db.refresh(plot)

    for k in _invalidate_plot_cache(farm_id):
        await cache_delete(k)

    return schemas.PlotRead.model_validate(plot)


@router.get("/plots/{plot_id}", response_model=schemas.PlotRead)
async def get_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"plots:item:farm:{farm_id}:{plot_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    plot = (
        db.query(models.Plot)
        .filter(
            models.Plot.id == plot_id,
            models.Plot.farm_id == farm_id,
        )
        .first()
    )

    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    payload = schemas.PlotRead.model_validate(plot).model_dump(mode="json")
    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.put("/plots/{plot_id}", response_model=schemas.PlotRead)
async def update_plot(
    plot_id: int,
    payload: schemas.PlotUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    plot = (
        db.query(models.Plot)
        .filter(
            models.Plot.id == plot_id,
            models.Plot.farm_id == farm_id,
        )
        .first()
    )

    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(plot, k, v)

    db.commit()
    db.refresh(plot)

    for k in _invalidate_plot_cache(farm_id, plot_id=plot_id):
        await cache_delete(k)

    return schemas.PlotRead.model_validate(plot)


@router.delete("/plots/{plot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plot(
    plot_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    plot = (
        db.query(models.Plot)
        .filter(
            models.Plot.id == plot_id,
            models.Plot.farm_id == farm_id,
        )
        .first()
    )

    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    db.delete(plot)
    db.commit()

    for k in _invalidate_plot_cache(farm_id, plot_id=plot_id):
        await cache_delete(k)

    return None


# =========================================================
# CROP CYCLE CRUD
# =========================================================

@router.get("/cycles", response_model=List[schemas.CropCycleRead])
async def list_crop_cycles(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crop_cycles:list:farm:{farm_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    cycles = (
        db.query(models.CropCycle)
        .filter(models.CropCycle.farm_id == farm_id)
        .order_by(models.CropCycle.id.desc())
        .all()
    )

    payload = [
        schemas.CropCycleRead.model_validate(c).model_dump(mode="json")
        for c in cycles
    ]

    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.post("/cycles", response_model=schemas.CropCycleRead, status_code=status.HTTP_201_CREATED)
async def create_crop_cycle(
    payload: schemas.CropCycleCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id
    data = payload.model_dump(exclude_unset=True)

    crop_id = data.get("crop_id")
    plot_id = data.get("plot_id")

    if not crop_id:
        raise HTTPException(status_code=400, detail="crop_id is required")

    if not plot_id:
        raise HTTPException(status_code=400, detail="plot_id is required")

    crop = (
        db.query(models.Crop)
        .filter(
            models.Crop.id == crop_id,
            models.Crop.farm_id == farm_id,
        )
        .first()
    )
    if not crop:
        raise HTTPException(status_code=404, detail="Crop not found")

    plot = (
        db.query(models.Plot)
        .filter(
            models.Plot.id == plot_id,
            models.Plot.farm_id == farm_id,
        )
        .first()
    )
    if not plot:
        raise HTTPException(status_code=404, detail="Plot not found")

    cycle = models.CropCycle(
        **data,
        farm_id=farm_id,
        created_by_id=db_user.id,
    )

    db.add(cycle)
    db.commit()
    db.refresh(cycle)

    for k in _invalidate_crop_cycle_cache(farm_id):
        await cache_delete(k)
    for k in _invalidate_plot_cache(farm_id, plot_id=plot_id):
        await cache_delete(k)

    return schemas.CropCycleRead.model_validate(cycle)


@router.get("/cycles/{cycle_id}", response_model=schemas.CropCycleRead)
async def get_crop_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cache_key = f"crop_cycles:item:farm:{farm_id}:{cycle_id}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )

    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    payload = schemas.CropCycleRead.model_validate(cycle).model_dump(mode="json")
    await cache_set(cache_key, payload, expire_seconds=120)
    return payload


@router.put("/cycles/{cycle_id}", response_model=schemas.CropCycleRead)
async def update_crop_cycle(
    cycle_id: int,
    payload: schemas.CropCycleUpdate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )

    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    data = payload.model_dump(exclude_unset=True)

    if "crop_id" in data:
        crop = (
            db.query(models.Crop)
            .filter(
                models.Crop.id == data["crop_id"],
                models.Crop.farm_id == farm_id,
            )
            .first()
        )
        if not crop:
            raise HTTPException(status_code=404, detail="Crop not found")

    if "plot_id" in data:
        plot = (
            db.query(models.Plot)
            .filter(
                models.Plot.id == data["plot_id"],
                models.Plot.farm_id == farm_id,
            )
            .first()
        )
        if not plot:
            raise HTTPException(status_code=404, detail="Plot not found")

    old_plot_id = cycle.plot_id

    for k, v in data.items():
        setattr(cycle, k, v)

    db.commit()
    db.refresh(cycle)

    for k in _invalidate_crop_cycle_cache(farm_id, cycle_id=cycle_id):
        await cache_delete(k)
    for k in _invalidate_plot_cache(farm_id, plot_id=old_plot_id):
        await cache_delete(k)
    if cycle.plot_id != old_plot_id:
        for k in _invalidate_plot_cache(farm_id, plot_id=cycle.plot_id):
            await cache_delete(k)

    return schemas.CropCycleRead.model_validate(cycle)


@router.delete("/cycles/{cycle_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crop_cycle(
    cycle_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )

    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    plot_id = cycle.plot_id

    db.delete(cycle)
    db.commit()

    for k in _invalidate_crop_cycle_cache(farm_id, cycle_id=cycle_id):
        await cache_delete(k)
    for k in _invalidate_plot_cache(farm_id, plot_id=plot_id):
        await cache_delete(k)

    return None


# =========================================================
# CROP CYCLE EXPENSES
# =========================================================

@router.post("/cycles/{cycle_id}/expenses", response_model=schemas.CropCycleExpenseRead, status_code=status.HTTP_201_CREATED)
async def add_crop_cycle_expense(
    cycle_id: int,
    payload: schemas.CropCycleExpenseCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    expense = models.CropCycleExpense(
        crop_cycle_id=cycle_id,
        **payload.model_dump(exclude_unset=True),
    )

    db.add(expense)
    db.commit()
    db.refresh(expense)

    for k in _invalidate_crop_cycle_cache(farm_id, cycle_id=cycle_id):
        await cache_delete(k)

    return schemas.CropCycleExpenseRead.model_validate(expense)


@router.get("/cycles/{cycle_id}/expenses", response_model=List[schemas.CropCycleExpenseRead])
async def list_crop_cycle_expenses(
    cycle_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    expenses = (
        db.query(models.CropCycleExpense)
        .filter(models.CropCycleExpense.crop_cycle_id == cycle_id)
        .order_by(models.CropCycleExpense.id.desc())
        .all()
    )

    return [schemas.CropCycleExpenseRead.model_validate(e) for e in expenses]


# =========================================================
# CROP CYCLE INCOME
# =========================================================

@router.post("/cycles/{cycle_id}/income", response_model=schemas.CropCycleIncomeRead, status_code=status.HTTP_201_CREATED)
async def add_crop_cycle_income(
    cycle_id: int,
    payload: schemas.CropCycleIncomeCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    income = models.CropCycleIncome(
        crop_cycle_id=cycle_id,
        **payload.model_dump(exclude_unset=True),
    )

    db.add(income)
    db.commit()
    db.refresh(income)

    for k in _invalidate_crop_cycle_cache(farm_id, cycle_id=cycle_id):
        await cache_delete(k)

    return schemas.CropCycleIncomeRead.model_validate(income)


@router.get("/cycles/{cycle_id}/income", response_model=List[schemas.CropCycleIncomeRead])
async def list_crop_cycle_income(
    cycle_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    incomes = (
        db.query(models.CropCycleIncome)
        .filter(models.CropCycleIncome.crop_cycle_id == cycle_id)
        .order_by(models.CropCycleIncome.id.desc())
        .all()
    )

    return [schemas.CropCycleIncomeRead.model_validate(i) for i in incomes]


# =========================================================
# CROP CYCLE PROFIT SUMMARY
# =========================================================

@router.get("/cycles/{cycle_id}/profit-summary", response_model=schemas.CropCycleProfitSummary)
async def get_crop_cycle_profit_summary(
    cycle_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_farm_user(user, db)
    farm_id = db_user.farm_id

    cycle = (
        db.query(models.CropCycle)
        .filter(
            models.CropCycle.id == cycle_id,
            models.CropCycle.farm_id == farm_id,
        )
        .first()
    )
    if not cycle:
        raise HTTPException(status_code=404, detail="Crop cycle not found")

    total_income = (
        db.query(func.sum(models.CropCycleIncome.amount))
        .filter(models.CropCycleIncome.crop_cycle_id == cycle_id)
        .scalar()
        or 0.0
    )

    total_expenses = (
        db.query(func.sum(models.CropCycleExpense.amount))
        .filter(models.CropCycleExpense.crop_cycle_id == cycle_id)
        .scalar()
        or 0.0
    )

    return schemas.CropCycleProfitSummary(
        crop_cycle_id=cycle_id,
        total_income=float(total_income),
        total_expenses=float(total_expenses),
        net_profit=float(total_income) - float(total_expenses),
    )