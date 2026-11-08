import datetime as dt
import hashlib
import secrets

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")

RESEND_COOLDOWN_SECONDS = 120


def hash_password(password: str) -> str:
    return PWD_CONTEXT.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return PWD_CONTEXT.verify(password, hashed)


def generate_verification_token() -> tuple[str, str, dt.datetime]:
    """One-use link token. Returns (plain_token_for_the_link, db_hash, expiry).

    24 bytes (32 urlsafe chars) keeps the full verify URL under the 76-char
    line where quoted-printable mail encoders hard-wrap links.
    """
    plain = secrets.token_urlsafe(24)
    token_hash = hashlib.sha256(plain.encode()).hexdigest()
    expires = dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=settings.VERIFY_TOKEN_HOURS)
    return plain, token_hash, expires


def hash_token(plain: str) -> str:
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
