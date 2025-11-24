# utils.py (Unified Firebase + JWT Auth)

import os
import requests
from jose import jwt, JWTError
from fastapi import HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserRead

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


# ---------------------------
# BACKEND JWT VERIFICATION
# ---------------------------
def verify_backend_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        return {"email": email}
    except JWTError:
        return None


# ---------------------------
# FIREBASE TOKEN VERIFICATION
# ---------------------------
def verify_firebase_token(token: str):
    """
    Uses Google's tokeninfo API.
    Works, but rate-limited.
    Proper version uses Firebase public keys.
    """
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=5
        )
        if resp.status_code != 200:
            return None

        data = resp.json()

        firebase_uid = data.get("user_id") or data.get("sub")
        email = data.get("email")

        if not firebase_uid:
            return None

        return {"firebase_uid": firebase_uid, "email": email}

    except:
        return None


# ---------------------------
# MAIN USER AUTH (Firebase or Backend JWT)
# ---------------------------
def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    token = authorization.split(" ")[1]

    # Try Firebase token
    firebase_data = verify_firebase_token(token)
    if firebase_data:
        uid = firebase_data["firebase_uid"]
        email = firebase_data["email"]

        user = db.query(User).filter(User.firebase_uid == uid).first()

        # Auto-create user
        if not user:
            if not email:
                raise HTTPException(status_code=401, detail="Email missing in Firebase token")

            user = User(
                firebase_uid=uid,
                email=email,
                name=email.split("@")[0],
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

    raise HTTPException(status_code=401, detail="Invalid or expired token")
