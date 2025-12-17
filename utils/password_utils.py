from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    # bcrypt safety: truncate to 72 bytes
    safe_password = password.encode("utf-8")[:72]
    return pwd_context.hash(safe_password)

def verify_password(password: str, hashed: str) -> bool:
    safe_password = password.encode("utf-8")[:72]
    return pwd_context.verify(safe_password, hashed)
