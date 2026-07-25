from datetime import UTC, datetime

import jwt
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models import Progress, User
from app.schemas.auth import LoginIn, RefreshIn, SignupIn, TokenPair
from app.services.serialize import user_out

router = APIRouter(prefix="/auth", tags=["auth"])


def _tokens(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
        user=user_out(user),
    )


@router.post("/signup", response_model=TokenPair, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupIn, db: DbSession) -> TokenPair:
    """Unbox a new toy."""
    existing = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A toy with that email is already on the shelf.",
        )

    highest = await db.scalar(select(func.max(User.trainee_no)))
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        toy_name=payload.toy_name.strip(),
        trainee_no=(highest or 470) + 1,
        last_login_at=datetime.now(UTC),
    )
    user.progress = Progress(xp_max=settings.STARTING_XP_MAX, level=1)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _tokens(user)


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginIn, db: DbSession) -> TokenPair:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="That email and password don't wind up together.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This toy has been boxed up."
        )

    user.last_login_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    return _tokens(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshIn, db: DbSession) -> TokenPair:
    try:
        user_id = decode_token(payload.refresh_token, "refresh")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="That refresh key is bent."
        ) from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown toy.")
    return _tokens(user)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(_: CurrentUser) -> dict[str, str]:
    """Tokens are stateless — the client drops them. Here for symmetry with the UI."""
    return {"message": "Winding down… see you soon!"}
