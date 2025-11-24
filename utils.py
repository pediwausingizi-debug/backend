import os
import requests
from datetime import datetime
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models import User

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("ALGORITHM", "HS256")


def verify_backend_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            return None
        return {"type": "jwt", "email": email}
    except JWTError:
        return None


def verify_firebase_token(token: str):
    try:
        resp = requests.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": token},
            timeout=5
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        firebase_uid = data.get("user_id")
        email = data.get("email")

        if not firebase_uid:
            return None

        return {
            "type": "firebase",
            "firebase_uid": firebase_uid,
            "email": email
        }

    except:
        return None


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = None
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    token = parts[1]

    firebase_data = verify_firebase_token(token)
    if firebase_data:
        user = db.query(User).filter(
            User.firebase_uid == firebase_data["firebase_uid"]
        ).first()

        if not user:
            if not firebase_data.get("email"):
                raise HTTPException(status_code=401, detail="Firebase token missing email")

            user = User(
                email=firebase_data["email"],
                firebase_uid=firebase_data["firebase_uid"],
                name=firebase_data["email"].split("@")[0],
                role="Worker"
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        return user

    jwt_data = verify_backend_jwt(token)
    if jwt_data:
        user = db.query(User).filter(User.email == jwt_data["email"]).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user

    raise HTTPException(status_code=401, detail="Invalid or expired token")
