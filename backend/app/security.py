import datetime as dt
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESEND_COOLDOWN_SECONDS = 120
MAX_CODE_ATTEMPTS = 6


def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return PWD_CONTEXT.verify(password, hashed)


def generate_verification_code() -> tuple[str, str, dt.datetime]:
    """6-digit code. Returns (plain_code_shown/user_entered, db_hash, expiry).
    Stored as SHA-256 like the tokens used to be — DB leak ≠ usable codes."""
    plain = "".join(secrets.choice("0123456789") for _ in range(6))
    code_hash = hashlib.sha256(plain.encode()).hexdigest()
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.VERIFY_CODE_MINUTES)
    return plain, code_hash, expires


def hash_code(plain: str) -> str:
    return hashlib.sha256(plain.encode()).hexdigest()


def create_access_token(subject: str) -> str:
    exp = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=settings.ACCESS_TOKEN_MINUTES)
    payload = {"sub": subject, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> str | None:
    """Return the subject (email) the token was issued for, or None."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None
