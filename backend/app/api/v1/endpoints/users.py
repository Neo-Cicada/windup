from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.core.security import hash_password, verify_password
from app.models import User
from app.schemas.academy import ProgressOut
from app.schemas.user import (
    AccountUpdateIn,
    EmailChangeIn,
    PasswordChangeIn,
    UserOut,
)
from app.services.progress import build_progress_out
from app.services.serialize import user_out

router = APIRouter(tags=["account"])


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> UserOut:
    return user_out(user)


@router.patch("/me", response_model=UserOut)
async def update_me(payload: AccountUpdateIn, user: CurrentUser, db: DbSession) -> UserOut:
    """Backs the profile screen's "Save account" button — display preferences only.

    Credentials go through /me/password and /me/email.
    """
    if payload.toy_name is not None:
        user.toy_name = payload.toy_name.strip()
    if payload.notifications is not None:
        user.notify_streak = payload.notifications.streak
        user.notify_weekly = payload.notifications.weekly
        user.notify_bosses = payload.notifications.bosses

    await db.commit()
    await db.refresh(user)
    return user_out(user)


@router.post("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    payload: PasswordChangeIn, user: CurrentUser, db: DbSession
) -> dict[str, str]:
    """Re-authenticates, so a stolen access token alone can't lock the owner out."""
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect."
        )
    user.password_hash = hash_password(payload.new_password)
    await db.commit()
    return {"message": "✓ Password saved!"}


@router.post("/me/email", response_model=UserOut)
async def change_email(payload: EmailChangeIn, user: CurrentUser, db: DbSession) -> UserOut:
    """Also re-authenticated: the email address is what a reset flow would trust."""
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect."
        )

    new_email = payload.new_email.lower()
    if new_email != user.email:
        taken = await db.scalar(select(User).where(User.email == new_email))
        if taken is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Another toy already claimed that email.",
            )
        user.email = new_email

    await db.commit()
    await db.refresh(user)
    return user_out(user)


@router.get("/me/progress", response_model=ProgressOut)
async def read_progress(db: DbSession, progress: CurrentProgress) -> ProgressOut:
    return await build_progress_out(db, progress)
