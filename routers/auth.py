from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from firebase_admin import auth as firebase_auth
from firebase_admin.auth import (
    InvalidIdTokenError,
    ExpiredIdTokenError,
    RevokedIdTokenError,
    CertificateFetchError,
)
import traceback

from database import get_db
from models import User, Farm, Worker, Notification
from schemas import UserRead, UserUpdate
from utils.auth_utils import create_backend_jwt, get_current_user
from utils.cache import cache_get, cache_set, cache_delete
from utils.notification_utils import create_notification

router = APIRouter(tags=["auth"])


# -------------------------------------------------
# Google Login Payload
# -------------------------------------------------
class GoogleLoginRequest(BaseModel):
    token: str  # Firebase ID token (JWT)


# -------------------------------------------------
# Admin Creates Manager/Worker Accounts
# -------------------------------------------------
class UserCreateByAdmin(BaseModel):
    email: EmailStr
    name: str
    role: str  # Manager | Worker


# -------------------------------------------------
# GOOGLE LOGIN
# Creates Admin + Farm if first login
# -------------------------------------------------
@router.post("/google-login")
async def google_login(req: GoogleLoginRequest, db: Session = Depends(get_db)):
    try:
        # ✅ Verify Firebase ID token
        decoded = firebase_auth.verify_id_token(req.token)

        email = decoded.get("email")
        name = decoded.get("name") or (email.split("@")[0] if email else None)
        picture = decoded.get("picture")
        firebase_uid = decoded.get("uid")  # ✅ correct claim key

        if not email:
            raise HTTPException(status_code=400, detail="Google token missing email")

        # Check if user exists
        user = db.query(User).filter(User.email == email).first()

        # CASE A — First login → Create Admin + Farm
        if not user:
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
            # CASE B — Existing user login (update fields if needed)
            updated = False

            if firebase_uid and user.firebase_uid != firebase_uid:
                user.firebase_uid = firebase_uid
                updated = True

            if name and name != user.name:
                user.name = name
                updated = True

            if picture and picture != user.picture:
                user.picture = picture
                updated = True

            if updated:
                db.commit()
                db.refresh(user)

        # Create backend JWT
        backend_token = create_backend_jwt(user)

        # Invalidate caches (both keys used elsewhere)
        await cache_delete(f"user:me:{user.id}")
        await cache_delete(f"user:{user.id}")

        return {
            "user": UserRead.model_validate(user).model_dump(mode="json"),
            "token": backend_token,
        }

    except (InvalidIdTokenError, ExpiredIdTokenError, RevokedIdTokenError) as e:
        print("FIREBASE TOKEN ERROR:", repr(e))
        raise HTTPException(status_code=401, detail="Invalid or expired Google token")

    except CertificateFetchError as e:
        # This usually means your server couldn't fetch Google's public certs (network/DNS/proxy)
        print("FIREBASE CERT FETCH ERROR:", repr(e))
        raise HTTPException(status_code=503, detail="Auth service temporarily unavailable")

    except HTTPException:
        # Let explicit HTTP errors pass through unchanged
        raise

    except Exception as e:
        # Anything else is a real server bug (DB, models, etc.)
        print("GOOGLE LOGIN UNEXPECTED ERROR:", repr(e))
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Google login failed (server error)")


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

    json_safe_user = UserRead.model_validate(db_user).model_dump(mode="json")

    # ✅ Invalidate both caches to prevent stale reload after toggles
    await cache_delete(f"user:me:{db_user.id}")
    await cache_delete(f"user:{db_user.id}")  # from get_current_user()

    # ✅ Re-cache fresh /me payload
    await cache_set(
        f"user:me:{db_user.id}",
        json_safe_user,
        expire_seconds=120,
    )

    return json_safe_user


# -------------------------------------------------
# CURRENT USER (CACHED)
# Returns: user + unread_notifications
# -------------------------------------------------
@router.get("/me")
async def me(
    auth_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    uid = auth_user["user_id"]
    farm_id = auth_user["farm_id"]
    cache_key = f"user:me:{uid}"

    # Try cache first
    cached = await cache_get(cache_key)
    if cached:
        return cached

    db_user = db.query(User).filter(User.id == uid).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Count UNREAD notifications for the entire farm
    unread = (
        db.query(Notification)
        .filter(
            Notification.farm_id == farm_id,
            Notification.read == False
        )
        .count()
    )

    # Build JSON response
    payload = UserRead.model_validate(db_user).model_dump(mode="json")
    payload["unread_notifications"] = unread

    # Cache it
    await cache_set(cache_key, payload, expire_seconds=120)

    return payload


# -------------------------------------------------
# ADMIN INVITE WORKER OR MANAGER
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
    db: Session = Depends(get_db),
):
    if auth_user["role"] != "Admin":
        raise HTTPException(status_code=403, detail="Admins only")

    if payload.role not in ["Manager", "Worker"]:
        raise HTTPException(status_code=400, detail="Invalid role")

    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    temp_password = secrets.token_hex(4)

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

    worker = Worker(
        name=payload.name,
        role=payload.role,
        email=payload.email,
        status="Active",
        farm_id=auth_user["farm_id"],
        created_by_id=auth_user["user_id"],
    )
    db.add(worker)
    db.commit()

    # ---------------- EMAIL ----------------
    try:
        send_email(
            to=payload.email,
            subject="You’ve been invited to FarmXpat",
            html_body=f"""
            <h2>Hello {payload.name},</h2>

            <p>You have been invited to join <strong>FarmXpat</strong> as a
            <strong>{payload.role}</strong>.</p>

            <p><strong>Login details:</strong></p>
            <ul>
                <li>Email: {payload.email}</li>
                <li>Temporary Password: {temp_password}</li>
            </ul>

            <p>Please log in and update your password.</p>

            <br/>
            <p>— FarmXpat Team</p>
            """
        )
    except Exception as e:
        print("EMAIL SEND ERROR:", repr(e))

    # ---------------- NOTIFICATION ----------------
    create_notification(
        db=db,
        farm_id=auth_user["farm_id"],
        title="User Invitation Sent",
        message=f"Invitation email sent to {payload.email}",
        notif_type="invite",
    )

    return {
        "message": "User invited successfully",
        "user_id": new_user.id,
        "worker_id": worker.id,
    }


# -------------------------------------------------
# EMAIL/PASSWORD LOGIN
# -------------------------------------------------
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
        "user": UserRead.model_validate(user).model_dump(mode="json"),
        "token": token,
    }


# -------------------------------------------------
# EMAIL/PASSWORD REGISTRATION (Creates Farm + Admin)
# -------------------------------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    farm_name: str


@router.post("/register")
async def email_register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create farm
    farm = Farm(name=payload.farm_name)
    db.add(farm)
    db.commit()
    db.refresh(farm)

    from utils.password_utils import hash_password

    # Create admin
    user = User(
        email=payload.email,
        name=payload.name or payload.email.split("@")[0],
        role="Admin",
        password_hash=hash_password(payload.password),
        farm_id=farm.id,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_backend_jwt(user)

    return {
        "user": UserRead.model_validate(user).model_dump(mode="json"),
        "token": token,
    }