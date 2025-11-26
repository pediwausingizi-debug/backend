import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi import Header
from database import get_db
from models import User

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7


# -------------------------------------------------
# Generate Backend JWT
# -------------------------------------------------
def create_backend_jwt(user):
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# -------------------------------------------------
# Decode Backend JWT
# -------------------------------------------------
def verify_backend_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")

        if not user_id or not email:
            return None

        return {"user_id": user_id, "email": email}

    except JWTError:
        return None


# -------------------------------------------------
# FastAPI Dependency for Protected Routes
# -------------------------------------------------

def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(None)
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = parts[1]

    jwt_data = verify_backend_jwt(token)
    if not jwt_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == jwt_data["user_id"]).first()

    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    # FIX: return dict not model
    return {"user_id": user.id, "email": user.email}

