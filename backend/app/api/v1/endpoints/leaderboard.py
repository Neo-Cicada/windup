from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession
from app.models import Progress, User
from app.schemas.academy import LeaderboardOut, LeaderOut
from app.services.progress import leaderboard_rank

# Shelf-of-fame swatches, cycled so every toy gets a colour.
PALETTE = ["#F7C948", "#4FB0E5", "#EF5B54", "#8B6FD6", "#E08A3C", "#6FBF73", "#3E8FC4"]

router = APIRouter(prefix="/leaderboard", tags=["shelf of fame"])


@router.get("", response_model=LeaderboardOut)
async def shelf_of_fame(
    db: DbSession, user: CurrentUser, limit: int = Query(default=10, ge=3, le=100)
) -> LeaderboardOut:
    rows = await db.execute(
        select(User.id, User.toy_name, User.avatar_body, Progress.total_xp)
        .join(Progress, Progress.user_id == User.id)
        .where(User.is_active.is_(True))
        .order_by(Progress.total_xp.desc(), User.created_at)
        .limit(limit)
    )

    leaders: list[LeaderOut] = []
    for rank, (uid, toy_name, color, total_xp) in enumerate(rows.all(), start=1):
        you = uid == user.id
        leaders.append(
            LeaderOut(
                rank=rank,
                name=f"{toy_name} (You)" if you else toy_name,
                xp=int(total_xp or 0),
                color=color or PALETTE[(rank - 1) % len(PALETTE)],
                you=you,
            )
        )

    your_rank = next((entry.rank for entry in leaders if entry.you), None)
    if your_rank is None:
        your_rank = await leaderboard_rank(db, user)

    # Podium order: 2nd, 1st, 3rd — matching the illustration.
    podium = [leaders[i] for i in (1, 0, 2) if i < len(leaders)]

    return LeaderboardOut(leaders=leaders, podium=podium, your_rank=your_rank)
