"""Merit badge evaluation — run after anything that changes progress."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Achievement,
    BossSession,
    Duel,
    Problem,
    Progress,
    Submission,
    UserAchievement,
    Zone,
)


async def _zone_cleared(db: AsyncSession, user_id: UUID, zone_slug: str) -> bool:
    total = await db.scalar(
        select(func.count(Problem.id)).join(Zone, Zone.id == Problem.zone_id).where(
            Zone.slug == zone_slug
        )
    )
    if not total:
        return False
    done = await db.scalar(
        select(func.count(func.distinct(Submission.problem_id)))
        .join(Problem, Problem.id == Submission.problem_id)
        .join(Zone, Zone.id == Problem.zone_id)
        .where(
            Zone.slug == zone_slug,
            Submission.user_id == user_id,
            Submission.status == "passed",
        )
    )
    return int(done or 0) >= int(total)


async def evaluate(db: AsyncSession, user_id: UUID, progress: Progress) -> list[Achievement]:
    """Award any newly-qualified badges. Returns the ones earned on this call."""
    already = set(
        (
            await db.scalars(
                select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
            )
        ).all()
    )

    all_badges = (await db.scalars(select(Achievement).order_by(Achievement.sort_order))).all()
    by_slug = {a.slug: a for a in all_badges}

    unaided_solves = int(
        await db.scalar(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.status == "passed",
                Submission.unaided.is_(True),
            )
        )
        or 0
    )
    fast_solve = bool(
        await db.scalar(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.status == "passed",
                Submission.duration_seconds.is_not(None),
                Submission.duration_seconds <= 300,
            )
        )
    )
    night_solve = bool(
        await db.scalar(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.user_id == user_id,
                Submission.status == "passed",
                func.extract("hour", Submission.created_at) < 5,
            )
        )
    )
    boss_win = bool(
        await db.scalar(
            select(func.count())
            .select_from(BossSession)
            .where(BossSession.user_id == user_id, BossSession.status == "completed")
        )
    )
    duel_win = bool(
        await db.scalar(select(func.count()).select_from(Duel).where(Duel.winner_id == user_id))
    )

    checks: dict[str, bool] = {
        "first-fix": progress.solved_count >= 1,
        "week-winder": progress.streak >= 7 or progress.longest_streak >= 7,
        "unaided-ace": unaided_solves >= 10,
        "block-master": await _zone_cleared(db, user_id, "building-blocks"),
        "marble-champ": await _zone_cleared(db, user_id, "marble-run"),
        "graph-guru": await _zone_cleared(db, user_id, "board-game"),
        "night-owl": night_solve,
        "boss-slayer": boss_win,
        "duellist": duel_win,
        "century-toy": progress.solved_count >= 100,
        "perfect-week": progress.longest_streak >= 7 and progress.solved_count >= 21,
        "speed-wind": fast_solve,
        "top-shelf": progress.level >= 5,
    }

    now = datetime.now(UTC)
    newly: list[Achievement] = []
    for slug, qualified in checks.items():
        badge = by_slug.get(slug)
        if badge is None or not qualified or badge.id in already:
            continue
        db.add(UserAchievement(user_id=user_id, achievement_id=badge.id, earned_at=now))
        newly.append(badge)

    return newly
