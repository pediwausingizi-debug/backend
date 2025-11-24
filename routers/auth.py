# routers/auth.py
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schemas import UserUpdate
from database import get_db
from models import User
from schemas import UserRead
from utils import (
    verify_firebase_token,
    verify_backend_jwt,
)

router = APIRouter(tags=["auth"])


# -------------------------------------------------------------------
# REQUEST MODELS
# -------------------------------------------------------------------
class IdTokenRequest(BaseModel):
    id_token: str


# -------------------------------------------------------------------
# FIREBASE LOGIN / REGISTER
# -------------------------------------------------------------------
@router.post("/firebase", response_model=UserRead)
def firebase_login(req: IdTokenRequest, db: Session = Depends(get_db)):
    """
    Accepts a Firebase ID token.
    Verifies token, upserts user, and returns user record.
    """

    token_data = verify_firebase_token(req.id_token)
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid Firebase ID token")

    firebase_uid = token_data["firebase_uid"]
    email = token_data.get("email")
    name = email.split("@")[0] if email else "Unnamed User"

    # 1. Look up by firebase UID
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

    # 2. Or lookup by email (for older accounts)
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    # 3. Create if missing
    if not user:
        user = User(
            email=email or f"{firebase_uid}@no-email",
            firebase_uid=firebase_uid,
            name=name,
            role="Worker",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Sync updated email/name if changed
        updated = False
        if email and user.email != email:
            user.email = email
            updated = True
        if name and user.name != name:
            user.name = name
            updated = True
        if not user.firebase_uid:
            user.firebase_uid = firebase_uid
            updated = True

        if updated:
            db.add(user)
            db.commit()
            db.refresh(user)

    return UserRead.from_orm(user)

@router.put("/update", response_model=UserRead)
def update_user(
    payload: UserUpdate,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    # Reuse the same firebase auth flow
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[1]
    payload_token = verify_firebase_token(token)

    firebase_uid = payload_token.get("sub") or payload_token.get("user_id")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Invalid Firebase token payload")

    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    for field, value in payload.dict(exclude_none=True).items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)

    return UserRead.from_orm(user)
# -------------------------------------------------------------------
# CURRENT USER (Supports Firebase token OR backend JWT)
# @router.get("/me", response_model=UserRead)
def me(authorization: str = Header(None), db: Session = Depends(get_db)):

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[1]

    # Try Firebase first
    firebase_data = verify_firebase_token(token)
    if firebase_data:
        firebase_uid = firebase_data["firebase_uid"]
        email = firebase_data.get("email")
        name = email.split("@")[0] if email else "User"

        user = db.query(User).filter(User.firebase_uid == firebase_uid).first()

        # AUTO-CREATE USER IF NOT EXISTS
        if not user:
            user = User(
                firebase_uid=firebase_uid,
                email=email or f"{firebase_uid}@no-email",
                name=name,
                role="Worker"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return UserRead.from_orm(user)

    # Try backend JWT
    jwt_data = verify_backend_jwt(token)
    if jwt_data:
        email = jwt_data["email"]
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserRead.from_orm(user)

    raise HTTPException(status_code=401, detail="Invalid token")
