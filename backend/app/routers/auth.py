from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import LoginIn, Token, UserCreate, UserOut
from ..security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class Message(BaseModel):
    detail: str


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already registered")

    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        is_admin=email in settings.admin_email_list,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.lower()))
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return {"access_token": create_access_token(user.email), "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user
