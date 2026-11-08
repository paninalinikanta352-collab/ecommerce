import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, Token, UserCreate, UserOut
from ..security import (
    MAX_CODE_ATTEMPTS,
    RESEND_COOLDOWN_SECONDS,
    create_access_token,
    generate_verification_code,
    hash_code,
    hash_password,
    verify_password,
)
from ..utils.mailer import send_code_email

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")


class Message(BaseModel):
    detail: str


class RegisterOut(BaseModel):
    detail: str
    email: str
    # dev convenience: with no SMTP configured, the code rides the response
    # so you can see it on screen. Never set in production.
    dev_code: str | None = None


class VerifyCodeIn(BaseModel):
    email: str
    code: str


class ResendIn(BaseModel):
    email: str


class ResendOut(BaseModel):
    detail: str
    sent: bool
    dev_code: str | None = None


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


@router.post("/register", response_model=RegisterOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    is_admin = email in settings.admin_email_list
    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        is_admin=is_admin,
        is_verified=is_admin,  # admins are trusted, no code round-trip
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    dev_code = None
    if not is_admin:
        raw_code, code_hash, expires = generate_verification_code()
        user.verification_code_hash = code_hash
        user.verification_code_expires = expires
        user.verification_code_attempts = 0
        user.verification_sent_at = _utcnow()
        db.commit()
        if settings.smtp_configured():
            try:
                send_code_email(user.email, user.full_name, raw_code)
            except Exception:
                # SMTP failure never blocks saving the account
                logger.exception("code email could not be sent to %s", email)
                user.verification_sent_at = None  # allow immediate resend retry
                db.commit()
        else:
            dev_code = raw_code  # dev mode: show it on screen

    return {
        "detail": "Account created. Enter your verification code.",
        "email": user.email,
        "dev_code": dev_code,
    }


@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "This account needs a verification code first — use the Verify page.",
        )
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}


@router.post("/verify-code", response_model=Message)
def verify_code(data: VerifyCodeIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No account with that email")
    if user.is_verified:
        return Message(detail="Already verified — log in any time.")
    if not user.verification_code_hash or not user.verification_code_expires:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No code pending — request one first")
    if user.verification_code_expires < _utcnow():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "That code expired — request a new one")

    if hash_code(data.code.strip()) != user.verification_code_hash:
        user.verification_code_attempts += 1
        if user.verification_code_attempts >= MAX_CODE_ATTEMPTS:
            user.verification_code_hash = None
            user.verification_code_expires = None
            user.verification_code_attempts = 0
            db.commit()
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Too many wrong attempts — request a fresh code.",
            )
        left = MAX_CODE_ATTEMPTS - user.verification_code_attempts
        db.commit()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Wrong code - {left} tries left")

    user.is_verified = True
    user.verification_code_hash = None
    user.verification_code_expires = None
    user.verification_code_attempts = 0
    db.commit()
    return Message(detail="verified")


@router.post("/resend", response_model=ResendOut)
def resend(data: ResendIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    sent = False
    dev_code = None

    # Same 200 for known/unknown accounts — endpoint must not leak who exists.
    if user and not user.is_verified:
        last = user.verification_sent_at
        within_cooldown = last is not None and (_utcnow() - last).total_seconds() < RESEND_COOLDOWN_SECONDS
        if not within_cooldown:
            raw_code, code_hash, expires = generate_verification_code()
            user.verification_code_hash = code_hash
            user.verification_code_expires = expires
            user.verification_code_attempts = 0
            user.verification_sent_at = _utcnow()
            db.commit()
            if settings.smtp_configured():
                try:
                    send_code_email(user.email, user.full_name, raw_code)
                    sent = True
                except Exception:
                    logger.exception("resend failed for %s", email)
                    user.verification_sent_at = None
                    db.commit()
            else:
                dev_code = raw_code

    if user and user.is_verified:
        detail = "This account is already verified. Just log in."
    elif user is None:
        detail = "If that account exists and needs verification, a code has been sent."
    elif dev_code is not None:
        detail = "New code generated — it's shown on screen (dev mode)."
    elif sent:
        detail = "New code sent to your email."
    elif not settings.smtp_configured() and user and user.verification_sent_at is None:
        detail = "Code delivery was blocked — try requesting again."
    else:
        detail = "Please wait a couple of minutes before requesting another code."
    return {"detail": detail, "sent": sent, "dev_code": dev_code}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
