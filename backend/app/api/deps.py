from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_db
from app.models import Progress, User

bearer_scheme = HTTPBearer(auto_error=False)

DbSession = Annotated[AsyncSession, Depends(get_db)]

CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Sprocket doesn't recognise that key — log in again.",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None:
        raise CREDENTIALS_ERROR
    try:
        user_id = decode_token(credentials.credentials, "access")
    except jwt.PyJWTError as exc:
        raise CREDENTIALS_ERROR from exc

    user = await db.get(User, user_id)
    if user is None or not user.is_active:
        raise CREDENTIALS_ERROR
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_current_progress(db: DbSession, user: CurrentUser) -> Progress:
    if user.progress is not None:
        return user.progress
    # Defensive: a user row should always have progress, but never 500 if it doesn't.
    progress = Progress(user_id=user.id)
    db.add(progress)
    await db.flush()
    user.progress = progress
    return progress


CurrentProgress = Annotated[Progress, Depends(get_current_progress)]
