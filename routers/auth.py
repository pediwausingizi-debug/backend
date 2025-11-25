from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth
from database import get_db
from models import User
from schemas import UserRead, UserUpdate
from utils import create_backend_jwt, get_current_user

router = APIRouter(tags=["auth"])


# ---------------------------------------------
# Request model (Google Login)
# ---------------------------------------------
class GoogleLoginRequest(BaseModel):
    google_token: str


# ---------------------------------------------
# Google Login -> Backend JWT
# ---------------------------------------------
@router.post("/google-login", response_model=dict)
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # 1. Verify Google ID token via Firebase Admin
        decoded = firebase_auth.verify_id_token(req.google_token)

        email = decoded.get("email")
        name = decoded.get("name") or (email.split("@")[0] if email else "Unknown")
        picture = decoded.get("picture")
        google_uid = decoded.get("uid")

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # 2. Lookup user by email
        user = db.query(User).filter(User.email == email).first()

        # 3. Create new user if not found
        if not user:
            user = User(
                email=email,
                name=name,
                picture=picture,
                firebase_uid=google_uid,
                role="Worker"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update name / picture / google_uid if changed
            updated = False
            if not user.firebase_uid:
                user.firebase_uid = google_uid
                updated = True
            if name and user.name != name:
                user.name = name
                updated = True
            if picture and user.picture != picture:
                user.picture = picture
                updated = True

            if updated:
                db.add(user)
                db.commit()
                db.refresh(user)

        # 4. Generate Backend JWT
        token = create_backend_jwt(user)

        return {
            "user": UserRead.from_orm(user),
            "token": token
        }

    except Exception as e:
        print("Google login error:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")


# ---------------------------------------------
# Update user profile
# (Requires backend JWT only)
# ---------------------------------------------
@router.put("/update", response_model=UserRead)
def update_user(
    payload: UserUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_in_db = db.query(User).filter(User.id == user["user_id"]).first()

    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.dict(exclude_none=True).items():
        setattr(user_in_db, field, value)

    db.add(user_in_db)
    db.commit()
    db.refresh(user_in_db)

    return UserRead.from_orm(user_in_db)


# ---------------------------------------------
# Current logged-in user
# Backend JWT ONLY
# ---------------------------------------------
@router.get("/me", response_model=UserRead)
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.id == user["user_id"]).first()

    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    return UserRead.from_orm(user_in_db)
