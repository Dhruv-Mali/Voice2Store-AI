from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import UserCreate, UserLogin, UserPublic, UserToken
from app.security import create_access_token, get_current_user, get_password_hash, verify_password

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserToken)
def register_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserToken:
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A user with this email already exists")

    user = User(
        name=payload.name.strip(),
        email=payload.email.lower(),
        hashed_password=get_password_hash(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)
    return UserToken(token=token, user=UserPublic.model_validate(user))


@router.post("/login", response_model=UserToken)
def login_user(payload: UserLogin, db: Session = Depends(get_db)) -> UserToken:
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user.id)
    return UserToken(token=token, user=UserPublic.model_validate(user))


@router.get("/me", response_model=UserPublic)
def get_user_profile(current_user: User = Depends(get_current_user)) -> UserPublic:
    return UserPublic.model_validate(current_user)
