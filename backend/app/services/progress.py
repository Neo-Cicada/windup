"""Read helpers that assemble the progress / analytics payloads."""

from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Problem, Progress, Submission, User, XpEvent, Zone
from app.schemas.academy import CoverageRow, ProgressOut, StreakOut, XpDay
from app.services.leveling import interview_ready, level_name, unaided_rate, xp_pct

STREAK_CELLS = 36  # a 3-row x 12-column heatmap


async def total_problem_count(db: AsyncSession) -> int:
    return int(await db.scalar(select(func.count()).select_from(Problem)) or 0)


async def build_progress_out(db: AsyncSession, progress: Progress) -> ProgressOut:
    total = await total_problem_count(db)
    return ProgressOut(
        xp=progress.xp,
        xp_max=progress.xp_max,
        xp_pct=xp_pct(progress),
        level=progress.level,
        level_name=level_name(progress.level),
        total_xp=progress.total_xp,
        coins=progress.coins,
        streak=progress.streak,
        longest_streak=progress.longest_streak,
        solved_count=progress.solved_count,
        unaided_rate=unaided_rate(progress),
        interview_ready=interview_ready(progress, total),
    )


async def solved_problem_ids(db: AsyncSession, user_id: UUID) -> set[UUID]:
    rows = await db.scalars(
        select(Submission.problem_id).where(
            Submission.user_id == user_id, Submission.status == "passed"
        )
    )
    return set(rows.all())


async def xp_history(db: AsyncSession, user_id: UUID, days: int = 7) -> list[XpDay]:
    """Charge earned per day for the last `days` days, oldest first."""
    today = datetime.now(UTC).date()
    start = today - timedelta(days=days - 1)

    rows = await db.execute(
        select(XpEvent.happened_on, func.sum(XpEvent.amount))
        .where(XpEvent.user_id == user_id, XpEvent.happened_on >= start)
        .group_by(XpEvent.happened_on)
    )
    totals = {row[0]: int(row[1] or 0) for row in rows.all()}

    series = [(start + timedelta(days=i), totals.get(start + timedelta(days=i), 0))
              for i in range(days)]
    peak = max((v for _, v in series), default=0)

    return [
        XpDay(
            label=day.strftime("%a"),
            date=day,
            value=value,
            height=round(value / peak * 160) if peak else 0,
        )
        for day, value in series
    ]


async def pattern_coverage(db: AsyncSession, user_id: UUID) -> list[CoverageRow]:
    """Pegboard rows: how far each toy corner has been cleared, on a 1-5 scale."""
    totals = await db.execute(
        select(Zone.slug, Zone.pattern, Zone.sort_order, func.count(Problem.id))
        .join(Problem, Problem.zone_id == Zone.id, isouter=True)
        .group_by(Zone.slug, Zone.pattern, Zone.sort_order)
        .order_by(Zone.sort_order)
    )

    solved = await db.execute(
        select(Zone.slug, func.count(func.distinct(Submission.problem_id)))
        .join(Problem, Problem.zone_id == Zone.id)
        .join(Submission, Submission.problem_id == Problem.id)
        .where(Submission.user_id == user_id, Submission.status == "passed")
        .group_by(Zone.slug)
    )
    solved_by_zone = {slug: int(count) for slug, count in solved.all()}

    rows: list[CoverageRow] = []
    for slug, pattern, _order, total in totals.all():
        total = int(total)
        done = solved_by_zone.get(slug, 0)
        ratio = done / total if total else 0.0
        # 0 solved -> level 1 (an unlit pegboard row still shows one peg's worth of intent)
        level = 1 if ratio == 0 else min(5, max(1, round(ratio * 5)))
        rows.append(
            CoverageRow(pattern=pattern, zone_slug=slug, level=level, solved=done, total=total)
        )
    return rows


async def streak_heatmap(db: AsyncSession, user_id: UUID, progress: Progress) -> StreakOut:
    """36 daily activity levels (0-4), oldest first."""
    today = datetime.now(UTC).date()
    start = today - timedelta(days=STREAK_CELLS - 1)

    rows = await db.execute(
        select(XpEvent.happened_on, func.sum(XpEvent.amount))
        .where(XpEvent.user_id == user_id, XpEvent.happened_on >= start)
        .group_by(XpEvent.happened_on)
    )
    totals = {row[0]: int(row[1] or 0) for row in rows.all()}

    cells: list[int] = []
    for i in range(STREAK_CELLS):
        amount = totals.get(start + timedelta(days=i), 0)
        cells.append(_heat_level(amount))

    return StreakOut(streak=progress.streak, longest_streak=progress.longest_streak, cells=cells)


def _heat_level(amount: int) -> int:
    if amount <= 0:
        return 0
    if amount < 100:
        return 1
    if amount < 200:
        return 2
    if amount < 350:
        return 3
    return 4


async def leaderboard_rank(db: AsyncSession, user: User) -> int | None:
    """1-based rank by lifetime charge."""
    if user.progress is None:
        return None
    ahead = await db.scalar(
        select(func.count()).select_from(Progress).where(Progress.total_xp > user.progress.total_xp)
    )
    return int(ahead or 0) + 1


def today_utc() -> date:
    return datetime.now(UTC).date()
