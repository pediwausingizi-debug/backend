from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

from database import get_db
from utils.auth_utils import get_current_user
import models
import schemas

router = APIRouter(prefix="", tags=["payments"])

PRO_PRICE = 499.0
PRO_CURRENCY = "KES"


def get_db_user(user_data, db: Session) -> models.User:
    db_user = (
        db.query(models.User)
        .filter(models.User.id == user_data["user_id"])
        .first()
    )

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    if not db_user.farm_id:
        raise HTTPException(status_code=400, detail="User is not assigned to a farm")

    return db_user


def normalize_phone(phone: str) -> str:
    value = str(phone or "").strip().replace(" ", "").replace("+", "")

    if value.startswith("0") and len(value) == 10:
        return "254" + value[1:]

    if value.startswith("254") and len(value) == 12:
        return value

    raise HTTPException(
        status_code=400,
        detail="Invalid phone number. Use 07XXXXXXXX or 2547XXXXXXXX.",
    )


@router.post("/demo/upgrade")
async def demo_upgrade_to_pro(
    payload: schemas.StartSubscriptionPayment,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    db_user = get_db_user(user, db)
    phone = normalize_phone(payload.phone_number)

    now = datetime.utcnow()
    expires_at = now + timedelta(days=30)

    subscription = models.Subscription(
        user_id=db_user.id,
        farm_id=db_user.farm_id,
        plan="pro",
        status="active",
        amount=PRO_PRICE,
        currency=PRO_CURRENCY,
        started_at=now,
        expires_at=expires_at,
        payment_reference=f"DEMO-{db_user.id}-{int(now.timestamp())}",
        checkout_request_id=f"DEMO-CHECKOUT-{db_user.id}-{int(now.timestamp())}",
        merchant_request_id=f"DEMO-MERCHANT-{db_user.id}-{int(now.timestamp())}",
    )

    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    transaction = models.PaymentTransaction(
        user_id=db_user.id,
        farm_id=db_user.farm_id,
        subscription_id=subscription.id,
        provider="demo_mpesa",
        payment_type="subscription",
        amount=PRO_PRICE,
        currency=PRO_CURRENCY,
        phone_number=phone,
        status="success",
        checkout_request_id=subscription.checkout_request_id,
        merchant_request_id=subscription.merchant_request_id,
        mpesa_receipt_number=f"DEMO{subscription.id}",
        result_code="0",
        result_description="Demo payment successful",
        raw_response=json.dumps(
            {
                "demo": True,
                "message": "Simulated M-Pesa payment successful",
                "amount": PRO_PRICE,
                "phone_number": phone,
            }
        ),
    )

    db.add(transaction)

    db_user.plan = "pro"
    db_user.subscription_status = "active"
    db_user.subscription_started_at = now
    db_user.subscription_expires_at = expires_at

    db.commit()
    db.refresh(db_user)
    db.refresh(transaction)

    return {
        "message": "Demo payment successful. FarmXpat Pro activated.",
        "plan": db_user.plan,
        "subscription_status": db_user.subscription_status,
        "subscription_started_at": db_user.subscription_started_at,
        "subscription_expires_at": db_user.subscription_expires_at,
        "amount": PRO_PRICE,
        "currency": PRO_CURRENCY,
        "payment": schemas.PaymentTransactionRead.model_validate(transaction),
        "subscription": schemas.SubscriptionRead.model_validate(subscription),
    }