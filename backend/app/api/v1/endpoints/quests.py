from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.core.config import settings
from app.models import (
    Achievement,
    DailyQuest,
    Problem,
    Progress,
    User,
    UserAchievement,
    XpEvent,
    XpSource,
)
from app.schemas.academy import DailyQuestOut, DashboardOut
from app.services.achievements import evaluate
from app.services.leveling import apply_xp, touch_streak
from app.services.progress import (
    build_progress_out,
    leaderboard_rank,
    solved_problem_ids,
    today_utc,
)

router = APIRouter(tags=["playroom"])

_QUEST_LOAD = selectinload(DailyQuest.problem).selectinload(Problem.zone)


class QuestProgressIn(BaseModel):
    pct: int = Field(ge=0, le=100)


async def _load_today_quests(db: AsyncSession, user_id) -> list[DailyQuest]:
    rows = await db.scalars(
        select(DailyQuest)
        .options(_QUEST_LOAD)
        .where(DailyQuest.user_id == user_id, DailyQuest.quest_date == today_utc())
        .order_by(DailyQuest.sort_order)
    )
    return list(rows.all())


async def ensure_today_quests(db: AsyncSession, user: User) -> list[DailyQuest]:
    """Today's quest cards, rolled once per day from problems the toy hasn't fixed."""
    existing = await _load_today_quests(db, user.id)
    if existing:
        return existing

    wanted = settings.DAILY_QUESTS
    solved = await solved_problem_ids(db, user.id)

    candidates = list(
        (
            await db.scalars(
                select(Problem).options(selectinload(Problem.zone)).order_by(Problem.sort_order)
            )
        ).all()
    )
    unsolved = [p for p in candidates if p.id not in solved] or candidates

    # Prefer one problem per zone so the day's quests span different toy corners.
    picked: list[Problem] = []
    seen_zones: set = set()
    for problem in unsolved:
        if problem.zone_id not in seen_zones:
            picked.append(problem)
            seen_zones.add(problem.zone_id)
        if len(picked) == wanted:
            break
    for problem in unsolved:
        if len(picked) >= wanted:
            break
        if problem not in picked:
            picked.append(problem)

    db.add_all(
        DailyQuest(user_id=user.id, problem_id=p.id, quest_date=today_utc(), sort_order=i)
        for i, p in enumerate(picked)
    )
    await db.commit()
    return await _load_today_quests(db, user.id)


def quest_out(quest: DailyQuest) -> DailyQuestOut:
    return DailyQuestOut(
        id=quest.id,
        name=quest.problem.title,
        slug=quest.problem.slug,
        zone=quest.problem.zone.name.upper(),
        color=quest.problem.zone.color,
        pct=quest.progress_pct,
        completed=quest.completed_at is not None,
        quest_date=quest.quest_date,
    )


@router.get("/quests/today", response_model=list[DailyQuestOut])
async def todays_quests(db: DbSession, user: CurrentUser) -> list[DailyQuestOut]:
    return [quest_out(q) for q in await ensure_today_quests(db, user)]


@router.patch("/quests/{quest_id}", response_model=DailyQuestOut)
async def update_quest_progress(
    quest_id: UUID, payload: QuestProgressIn, db: DbSession, user: CurrentUser
) -> DailyQuestOut:
    """Nudge a quest card's progress bar as the toy works."""
    quest = await db.scalar(
        select(DailyQuest)
        .options(_QUEST_LOAD)
        .where(DailyQuest.id == quest_id, DailyQuest.user_id == user.id)
    )
    if quest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No such quest today.")

    quest.progress_pct = payload.pct
    await db.commit()
    await db.refresh(quest)
    return quest_out(quest)


async def build_dashboard(db: AsyncSession, user: User, progress: Progress) -> DashboardOut:
    quests = await ensure_today_quests(db, user)
    if await evaluate(db, user.id, progress):
        await db.commit()

    earned = int(
        await db.scalar(
            select(func.count())
            .select_from(UserAchievement)
            .where(UserAchievement.user_id == user.id)
        )
        or 0
    )
    total = int(await db.scalar(select(func.count()).select_from(Achievement)) or 0)
    rank = await leaderboard_rank(db, user)
    progress_out = await build_progress_out(db, progress)

    done = sum(1 for q in quests if q.completed_at is not None)
    remaining = len(quests) - done
    if progress.streak == 0:
        message = "You showed up today — that's the hardest part. Let's fix some toys!"
    elif remaining == 0:
        message = f"All quests cleared! {progress.streak}-day streak and still winding."
    else:
        message = (
            f"You're {progress_out.interview_ready}% Interview Ready. "
            f"{remaining} quest{'s' if remaining != 1 else ''} left today to keep the streak alive."
        )

    return DashboardOut(
        toy_name=user.toy_name,
        trainee_no=f"{user.trainee_no:04d}",
        avatar_body=user.avatar_body,
        avatar_head=user.avatar_head,
        avatar_accent=user.avatar_accent,
        sprocket_message=message,
        progress=progress_out,
        badges_label=f"{earned}/{total}",
        rank=rank,
        quests=[quest_out(q) for q in quests],
        quests_done=done,
        wind_up_available=not await _wound_up_today(db, user.id),
    )


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(db: DbSession, user: CurrentUser, progress: CurrentProgress) -> DashboardOut:
    """Everything the playroom home screen renders, in one round trip."""
    return await build_dashboard(db, user, progress)


async def _wound_up_today(db: AsyncSession, user_id) -> bool:
    return (
        await db.scalar(
            select(XpEvent.id).where(
                XpEvent.user_id == user_id,
                XpEvent.source == XpSource.WIND_UP,
                XpEvent.happened_on == today_utc(),
            )
        )
    ) is not None


@router.post("/me/wind-up", response_model=DashboardOut)
async def wind_up(db: DbSession, user: CurrentUser, progress: CurrentProgress) -> DashboardOut:
    """The topbar wind-up key: one free charge top-up per day.

    Without the daily cap this is an unlimited XP faucet — the button can be clicked
    (or scripted) forever. A partial unique index on the XpEvent row enforces the same
    rule at the database level, so concurrent requests can't both slip through.
    """
    today = today_utc()
    if await _wound_up_today(db, user.id):
        return await build_dashboard(db, user, progress)

    outcome = apply_xp(progress, settings.XP_WIND_UP)
    touch_streak(progress, today)
    db.add(
        XpEvent(
            user_id=user.id,
            amount=outcome.xp_awarded,
            source=XpSource.WIND_UP,
            note="Wound up the key",
            happened_on=today,
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        # Lost the race against a concurrent wind-up; the other one counted.
        await db.rollback()
        return await build_dashboard(db, user, progress)

    await db.refresh(progress)
    return await build_dashboard(db, user, progress)
