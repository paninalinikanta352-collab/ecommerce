import datetime as dt

from jose import JWTError, jwt
from passlib.context import CryptContext

from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


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
