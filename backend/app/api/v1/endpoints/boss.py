from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.core.config import settings
from app.models import BossSession, BossStatus, Progress, Submission, XpEvent, XpSource
from app.schemas.academy import BossActionIn, BossSessionOut
from app.services.leveling import apply_xp, touch_streak
from app.services.progress import today_utc

router = APIRouter(prefix="/boss", tags=["boss battle"])

ACTIVE = (BossStatus.RUNNING, BossStatus.PAUSED)


def _elapsed(session: BossSession) -> int:
    """Seconds burned since the clock was last resumed."""
    if session.status != BossStatus.RUNNING or session.resumed_at is None:
        return 0
    resumed = session.resumed_at
    if resumed.tzinfo is None:
        resumed = resumed.replace(tzinfo=UTC)
    return int((datetime.now(UTC) - resumed).total_seconds())


def _remaining(session: BossSession) -> int:
    return max(0, session.remaining_seconds - _elapsed(session))


def _settle_clock(session: BossSession) -> None:
    """Fold elapsed time into remaining_seconds; expire the session if it ran out."""
    session.remaining_seconds = _remaining(session)
    session.resumed_at = None
    if session.remaining_seconds == 0 and session.status == BossStatus.RUNNING:
        session.status = BossStatus.EXPIRED
        session.finished_at = datetime.now(UTC)


def _out(session: BossSession) -> BossSessionOut:
    remaining = _remaining(session)
    minutes, seconds = divmod(remaining, 60)
    if session.status == BossStatus.RUNNING:
        label = "Pause fight"
    elif remaining <= 0 or session.status in (BossStatus.COMPLETED, BossStatus.EXPIRED):
        label = "Rematch"
    elif session.status == BossStatus.PAUSED and remaining < session.total_seconds:
        label = "Resume fight"
    else:
        label = "Begin battle"

    return BossSessionOut(
        id=session.id,
        boss_name=session.boss_name,
        status=session.status,
        total_seconds=session.total_seconds,
        remaining_seconds=remaining,
        time_label=f"{minutes}:{seconds:02d}",
        pct=round(remaining / session.total_seconds * 100) if session.total_seconds else 0,
        rounds_total=session.rounds_total,
        rounds_cleared=session.rounds_cleared,
        xp_awarded=session.xp_awarded,
        button_label=label,
    )


async def _rounds_cleared(db: AsyncSession, session: BossSession) -> int:
    """Distinct problems genuinely solved *during* this fight.

    Only submissions that paid out (xp_awarded > 0) count, which means a first-time
    solve. Without this, a fight could be "won" by re-solving the same three problems
    over and over, or by doing nothing at all.
    """
    return int(
        await db.scalar(
            select(func.count(func.distinct(Submission.problem_id))).where(
                Submission.boss_session_id == session.id,
                Submission.user_id == session.user_id,
                Submission.status == "passed",
                Submission.xp_awarded > 0,
            )
        )
        or 0
    )


async def _current(db: AsyncSession, user_id) -> BossSession | None:
    return await db.scalar(
        select(BossSession)
        .where(BossSession.user_id == user_id, BossSession.status.in_(ACTIVE))
        .order_by(BossSession.created_at.desc())
        .limit(1)
    )


@router.get("/current", response_model=BossSessionOut | None)
async def current_session(db: DbSession, user: CurrentUser) -> BossSessionOut | None:
    session = await _current(db, user.id)
    if session is None:
        return None
    if _remaining(session) == 0 and session.status == BossStatus.RUNNING:
        _settle_clock(session)
        await db.commit()
    return _out(session)


@router.post("/sessions", response_model=BossSessionOut, status_code=status.HTTP_201_CREATED)
async def start_session(db: DbSession, user: CurrentUser) -> BossSessionOut:
    """Ring the bell on a fresh 15-minute mock round. Abandons any in-flight fight."""
    existing = await _current(db, user.id)
    if existing is not None:
        existing.status = BossStatus.ABANDONED
        existing.finished_at = datetime.now(UTC)

    session = BossSession(
        user_id=user.id,
        total_seconds=settings.BOSS_DURATION_SECONDS,
        remaining_seconds=settings.BOSS_DURATION_SECONDS,
        status=BossStatus.RUNNING,
        resumed_at=datetime.now(UTC),
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return _out(session)


@router.post("/sessions/{session_id}", response_model=BossSessionOut)
async def act_on_session(
    session_id: UUID,
    payload: BossActionIn,
    db: DbSession,
    user: CurrentUser,
    progress: CurrentProgress,
) -> BossSessionOut:
    """Pause / resume / finish a fight — the single button under the timer."""
    session = await db.scalar(
        select(BossSession).where(BossSession.id == session_id, BossSession.user_id == user.id)
    )
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No such battle on the record."
        )

    now = datetime.now(UTC)
    action = payload.action

    if action in ("pause", "resume", "complete", "abandon"):
        _settle_clock(session)

    if session.status in (BossStatus.COMPLETED, BossStatus.EXPIRED) and action != "start":
        return _out(session)

    if action == "pause":
        session.status = BossStatus.PAUSED
    elif action in ("start", "resume"):
        if session.remaining_seconds <= 0:
            session.remaining_seconds = session.total_seconds
            session.rounds_cleared = 0
            session.finished_at = None
        session.status = BossStatus.RUNNING
        session.resumed_at = now
    elif action == "abandon":
        session.status = BossStatus.ABANDONED
        session.finished_at = now
    elif action == "complete":
        # A win has to be earned: every round solved, in this fight, before the clock ran out.
        cleared = await _rounds_cleared(db, session)
        session.rounds_cleared = min(cleared, session.rounds_total)
        if cleared < session.rounds_total:
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"The boss is still standing — {cleared} of {session.rounds_total} rounds "
                    "solved. Fix the rest before you call it a win."
                ),
            )
        if session.remaining_seconds <= 0:
            await db.commit()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="The Jack-in-the-Box already sprang — that fight is over.",
            )
        session.status = BossStatus.COMPLETED
        session.finished_at = now
        _award_boss_xp(db, session, progress, user.id)

    await db.commit()
    await db.refresh(session)
    return _out(session)


def _award_boss_xp(db, session: BossSession, progress: Progress, user_id) -> None:
    """Beating the boss pays the round reward plus a speed bonus for time left."""
    if session.xp_awarded:
        return
    base = 300
    speed_bonus = round(session.remaining_seconds / max(1, session.total_seconds) * 150)
    total = base + speed_bonus

    outcome = apply_xp(progress, total)
    touch_streak(progress, today_utc())
    session.xp_awarded = outcome.xp_awarded
    db.add(
        XpEvent(
            user_id=user_id,
            amount=total,
            source=XpSource.BOSS,
            note=f"Defeated {session.boss_name}",
            happened_on=today_utc(),
        )
    )


@router.get("/sessions", response_model=list[BossSessionOut])
async def list_sessions(db: DbSession, user: CurrentUser, limit: int = 10) -> list[BossSessionOut]:
    rows = await db.scalars(
        select(BossSession)
        .where(BossSession.user_id == user.id)
        .order_by(BossSession.created_at.desc())
        .limit(max(1, min(limit, 50)))
    )
    return [_out(s) for s in rows.all()]
