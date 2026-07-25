from fastapi import APIRouter

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.schemas.academy import AnalyticsSummaryOut, CoverageRow, StreakOut, XpDay
from app.services.leveling import unaided_rate
from app.services.progress import pattern_coverage, streak_heatmap, xp_history

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("", response_model=AnalyticsSummaryOut)
async def summary(
    db: DbSession, user: CurrentUser, progress: CurrentProgress
) -> AnalyticsSummaryOut:
    """Everything the Analytics screen charts."""
    history = await xp_history(db, user.id)
    return AnalyticsSummaryOut(
        xp_history=history,
        xp_this_week=sum(d.value for d in history),
        coverage=await pattern_coverage(db, user.id),
        unaided_rate=unaided_rate(progress),
        streak=await streak_heatmap(db, user.id, progress),
    )


@router.get("/xp-history", response_model=list[XpDay])
async def charge_history(db: DbSession, user: CurrentUser, days: int = 7) -> list[XpDay]:
    return await xp_history(db, user.id, days=max(1, min(days, 90)))


@router.get("/coverage", response_model=list[CoverageRow])
async def coverage(db: DbSession, user: CurrentUser) -> list[CoverageRow]:
    return await pattern_coverage(db, user.id)


@router.get("/streak", response_model=StreakOut)
async def streak(db: DbSession, user: CurrentUser, progress: CurrentProgress) -> StreakOut:
    return await streak_heatmap(db, user.id, progress)
