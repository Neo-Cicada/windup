from fastapi import APIRouter
from sqlalchemy import select

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.models import Achievement, UserAchievement
from app.schemas.academy import AchievementOut, AchievementsOut
from app.services.achievements import evaluate

router = APIRouter(prefix="/achievements", tags=["merit sash"])


@router.get("", response_model=AchievementsOut)
async def list_achievements(
    db: DbSession, user: CurrentUser, progress: CurrentProgress
) -> AchievementsOut:
    """The merit sash — every badge, earned or not, in display order."""
    if await evaluate(db, user.id, progress):
        await db.commit()

    badges = (await db.scalars(select(Achievement).order_by(Achievement.sort_order))).all()
    earned_rows = await db.execute(
        select(UserAchievement.achievement_id, UserAchievement.earned_at).where(
            UserAchievement.user_id == user.id
        )
    )
    earned = {row[0]: row[1] for row in earned_rows.all()}

    items = [
        AchievementOut(
            slug=b.slug,
            name=b.name,
            description=b.description,
            color=b.color,
            earned=b.id in earned,
            earned_at=earned.get(b.id),
        )
        for b in badges
    ]
    return AchievementsOut(
        earned_count=len(earned),
        total_count=len(items),
        label=f"{len(earned)}/{len(items)}",
        items=items,
    )
