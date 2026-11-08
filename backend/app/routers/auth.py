import datetime as dt
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, Token, UserCreate, UserOut
from ..security import (
    RESEND_COOLDOWN_SECONDS,
    create_access_token,
    generate_verification_token,
    hash_password,
    hash_token,
    verify_password,
)
from ..utils.mailer import send_verification_email

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger("app.auth")


class Message(BaseModel):
    detail: str


class RegisterOut(BaseModel):
    detail: str
    email: str


class ResendIn(BaseModel):
    email: str


class ResendOut(BaseModel):
    detail: str
    sent: bool


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _verify_url(plain_token: str) -> str:
    # points at THIS API (which marks the user verified), and the API
    # redirects the browser to the frontend status page afterwards
    return f"{settings.PUBLIC_API_URL}/auth/verify?token={plain_token}"


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
        is_verified=is_admin,  # admins are trusted, no mail round-trip
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if not is_admin:
        plain, token_hash, expires = generate_verification_token()
        user.verification_token_hash = token_hash
        user.verification_token_expires = expires
        user.verification_sent_at = _utcnow()
        db.commit()
        try:
            send_verification_email(user.email, user.full_name, _verify_url(plain))
        except Exception:
            # SMTP down must never block registration; allow immediate retry via /resend
            logger.exception("verification email could not be sent to %s", email)
            user.verification_sent_at = None
            db.commit()

    return {
        "detail": "Account created. Check your inbox for a verification link.",
        "email": user.email,
    }


@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_verified:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Verify your email first — check your inbox for the link, or request a new one below.",
        )
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}


@router.get("/verify")
def verify(token: str = "", db: Session = Depends(get_db)) -> RedirectResponse:
    """The link the email contains. One GET marks the user verified and
    redirects the browser to the frontend status page."""

    def redirect(state: str) -> RedirectResponse:
        return RedirectResponse(
            f"{settings.FRONTEND_ORIGIN}/verify?status={state}",
            status_code=302,
        )

    if not token:
        return redirect("invalid")

    user = db.scalar(select(User).where(User.verification_token_hash == hash_token(token)))
    if not user:
        return redirect("invalid")
    if user.is_verified or not user.verification_token_expires:
        return redirect("invalid")  # already used, or nothing pending
    if user.verification_token_expires < _utcnow():
        return redirect("expired")

    user.is_verified = True
    user.verification_token_hash = None  # one-use, kill it
    user.verification_token_expires = None
    db.commit()
    return redirect("ok")


@router.post("/resend", response_model=ResendOut)
def resend(data: ResendIn, db: Session = Depends(get_db)):
    email = data.email.lower()
    user = db.scalar(select(User).where(User.email == email))
    sent = False

    # Same 200 for known/unknown accounts — endpoint must not leak who exists.
    if user and not user.is_verified:
        last = user.verification_sent_at
        within_cooldown = last is not None and (_utcnow() - last).total_seconds() < RESEND_COOLDOWN_SECONDS
        if not within_cooldown:
            plain, token_hash, expires = generate_verification_token()
            user.verification_token_hash = token_hash
            user.verification_token_expires = expires
            user.verification_sent_at = _utcnow()
            db.commit()
            try:
                send_verification_email(user.email, user.full_name, _verify_url(plain))
                sent = True
            except Exception:
                logger.exception("resend failed for %s", email)
                user.verification_sent_at = None  # allow an immediate retry
                db.commit()

    if not user:
        detail = "If that account exists and needs verification, a link has been sent."
    elif sent:
        detail = "New verification link sent — check your inbox."
    elif user.is_verified:
        detail = "This account is already verified. Just log in."
    else:
        detail = "Please wait a couple of minutes before requesting another email."
    return {"detail": detail, "sent": sent}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
