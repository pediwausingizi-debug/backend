import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session

from database import get_db
from models import User
from utils.cache import cache_get, cache_set

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_DAYS = 7
ISSUER = "farmxpat_backend"
AUDIENCE = "farmxpat_users"

# Create Backend JWT (INCLUDES FARM ID)

def create_backend_jwt(user: User):
    now = datetime.utcnow()

    payload = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "farm_id": user.farm_id,   # REQUIRED FOR MULTI-TENANT FARM SCOPING

        "iss": ISSUER,
        "aud": AUDIENCE,
        "iat": now,
        "exp": now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
        "jti": f"{user.id}-{int(now.timestamp())}"
    }

    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Decode JWT

def verify_backend_jwt(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
            audience=AUDIENCE,
            issuer=ISSUER
        )

        return {
            "user_id": int(payload["sub"]),
            "email": payload["email"],
            "role": payload.get("role", "Worker"),
            "farm_id": payload.get("farm_id"),   # MUST RETURN FARM ID
        }

    except JWTError:
        return None

# Protect Routes + Redis Cache

async def get_current_user(
    db: Session = Depends(get_db),
    authorization: str = Header(None),
):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")

    token = parts[1]

    jwt_data = verify_backend_jwt(token)
    if not jwt_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    uid = jwt_data["user_id"]
    farm_id = jwt_data.get("farm_id")

    # Redis cache: user:{uid}
    
    cache_key = f"user:{uid}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    # Load DB user

    user = db.query(User).filter(User.id == uid).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    user_payload = {
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "farm_id": user.farm_id,   # ENSURE FARM ID ALWAYS PRESENT
    }

    await cache_set(cache_key, user_payload, expire_seconds=300)

    return user_payload


# ROLE-BASED ACCESS

def require_admin(user=Depends(get_current_user)):
    if user["role"].lower() != "admin":
        raise HTTPException(status_code=403, detail="Admins only")
    return user


def require_manager(user=Depends(get_current_user)):
    if user["role"].lower() not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Managers or Admins only")
    return user
