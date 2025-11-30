from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth

from database import get_db
from models import User, Farm, Worker
from schemas import UserRead, UserUpdate
from utils.auth_utils import create_backend_jwt, get_current_user
from utils.cache import cache_get, cache_set, cache_delete

router = APIRouter(tags=["auth"])


# -------------------------------------------------
# Google Login Payload
# -------------------------------------------------
class GoogleLoginRequest(BaseModel):
    token: str


# -------------------------------------------------
# Admin Creates Manager/Worker Accounts
# -------------------------------------------------
class UserCreateByAdmin(BaseModel):
    email: EmailStr
    name: str
    role: str   # Manager | Worker


# -------------------------------------------------
# GOOGLE LOGIN (ADMIN ONLY FOR FIRST TIME)
# -------------------------------------------------
@router.post("/google-login")
async def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        decoded = firebase_auth.verify_id_token(req.token)

        email = decoded.get("email")
        name = decoded.get("name") or email.split("@")[0]
        picture = decoded.get("picture")
        firebase_uid = decoded.get("user_id")

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # 1. Check if user exists
        user = db.query(User).filter(User.email == email).first()

        # -------------------------------------------------------
        # CASE A — First time Google login → Create Admin + Farm
        # -------------------------------------------------------
        if not user:
            # Create a new farm for this admin
            farm = Farm(name=f"{name}'s Farm")
            db.add(farm)
            db.commit()
            db.refresh(farm)

            user = User(
                email=email,
                name=name,
                picture=picture,
                firebase_uid=firebase_uid,
                role="Admin",
                farm_id=farm.id,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        else:
            # -------------------------------------------------------
            # CASE B — Existing User Logging In
            # -------------------------------------------------------
            updated = False

            if not user.firebase_uid:
                user.firebase_uid = firebase_uid
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

        # 3. Create backend JWT including role + farm_id
        backend_token = create_backend_jwt(user)

        # 4. Invalidate cached profile
        await cache_delete(f"user:me:{user.id}")

        return {
            "user": UserRead.model_validate(user),
            "token": backend_token,
        }

    except Exception as e:
        print("GOOGLE LOGIN ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")


# -------------------------------------------------
# ADMIN: Create Manager / Worker
# -------------------------------------------------
#@router.post("/admin/create-user")
async def admin_create_user(
    payload: UserCreateByAdmin,
    auth_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if auth_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")

    if payload.role not in ["Manager", "Worker"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Check if user already exists
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # New user belongs to Admin’s farm
    new_user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        farm_id=auth_user["farm_id"],
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserRead.model_validate(new_user)


# -------------------------------------------------
# UPDATE PROFILE
# -------------------------------------------------
@router.put("/update")
async def update_user(
    payload: UserUpdate,
    auth_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_user = db.query(User).filter(User.id == auth_user["user_id"]).first()

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    for field, value in payload.dict(exclude_none=True).items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)

    # update cached profile
    await cache_set(
        f"user:me:{db_user.id}",
        UserRead.model_validate(db_user).model_dump(),
        expire_seconds=120,
    )

    return UserRead.model_validate(db_user)


# -------------------------------------------------
# CURRENT USER (CACHED)
# -------------------------------------------------
@router.get("/me")
async def me(
    auth_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = auth_user["user_id"]
    cache_key = f"user:me:{uid}"

    cached = await cache_get(cache_key)
    if cached:
        return cached

    db_user = db.query(User).filter(User.id == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    payload = UserRead.model_validate(db_user).model_dump()

    await cache_set(cache_key, payload, expire_seconds=120)

    return payload

# -------------------------------------------------
# ADMIN: Invite Manager / Worker (email + password)
# -------------------------------------------------
from utils.password_utils import hash_password
from utils.email_utils import send_email
import secrets
class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: str  # Manager | Worker

@router.post("/admin/invite")
async def invite_user(
    payload: InviteRequest,
    auth_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins
    if auth_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")

    if payload.role not in ["Manager", "Worker"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    # Exists already?
    existing = (
        db.query(User)
        .filter(User.email == payload.email)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # 1) Generate temporary password
    temp_password = secrets.token_hex(4)   # 8 chars

    # 2) Create user
    new_user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        password_hash=hash_password(temp_password),
        farm_id=auth_user["farm_id"],
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 3) Create worker entry
    worker = Worker(
        name=payload.name,
        role=payload.role,
        email=payload.email,
        status="Active",
        farm_id=auth_user["farm_id"],
        created_by_id=auth_user["user_id"]
    )
    db.add(worker)
    db.commit()

    # 4) Send invite email
    try:
        send_email(
            to=payload.email,
            subject="You’ve been invited to FarmXpat",
            body=(
                f"Hello {payload.name},\n\n"
                f"You have been invited to join FarmXpat as a {payload.role}.\n\n"
                f"Your login details:\n"
                f"Email: {payload.email}\n"
                f"Temporary Password: {temp_password}\n\n"
                f"Please log in and update your password.\n\n"
                "FarmXpat Team"
            )
        )
    except Exception as e:
        print("EMAIL SEND ERROR:", e)

    return {
        "message": "User invited successfully",
        "user_id": new_user.id,
        "worker_id": worker.id
    }

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/login")
async def email_login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.password_hash:
        raise HTTPException(status_code=400, detail="This account uses Google login")

    from utils.password_utils import verify_password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = create_backend_jwt(user)

    return {
        "user": UserRead.model_validate(user),
        "token": token,
    }
