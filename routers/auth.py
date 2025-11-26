from fastapi import APIRouter, HTTPException, Depends
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
    token: str   # FIXED: matches frontend payload


# ---------------------------------------------
# Google Login -> Backend JWT
# ---------------------------------------------
@router.post("/google-login")
def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # 1. Verify Firebase ID token
        decoded = firebase_auth.verify_id_token(req.token)

        email = decoded.get("email")
        name = decoded.get("name") or email.split("@")[0]
        picture = decoded.get("picture")

        # FIXED: Firebase UID key
        firebase_uid = decoded.get("user_id")

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # 2. Find existing user
        user = db.query(User).filter(User.email == email).first()

        # 3. Create user if not exists
        if not user:
            user = User(
                email=email,
                name=name,
                picture=picture,
                firebase_uid=firebase_uid,
                role="Worker"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            changed = False

            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
                changed = True

            if name and user.name != name:
                user.name = name
                changed = True

            if picture and user.picture != picture:
                user.picture = picture
                changed = True

            if changed:
                db.add(user)
                db.commit()
                db.refresh(user)

        # 4. Create backend JWT
        backend_token = create_backend_jwt(user)

        return {
            "user": UserRead.model_validate(user),   # FIXED
            "token": backend_token
        }

    except Exception as e:
        print("Google login error:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")


# ---------------------------------------------
# Update profile
# ---------------------------------------------
@router.put("/update")
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

    db.commit()
    db.refresh(user_in_db)

    return UserRead.model_validate(user_in_db)


# ---------------------------------------------
# Current user
# ---------------------------------------------
@router.get("/me")
def me(user=Depends(get_current_user), db: Session = Depends(get_db)):
    user_in_db = db.query(User).filter(User.id == user["user_id"]).first()

    if not user_in_db:
        raise HTTPException(status_code=404, detail="User not found")

    return UserRead.model_validate(user_in_db)
