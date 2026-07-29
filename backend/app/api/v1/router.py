from fastapi import APIRouter

from app.api.v1.endpoints import (
    achievements,
    analytics,
    auth,
    boss,
    duels,
    languages,
    leaderboard,
    problems,
    quests,
    submissions,
    users,
    zones,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(quests.router)
api_router.include_router(zones.router)
api_router.include_router(problems.router)
api_router.include_router(languages.router)
api_router.include_router(submissions.router)
api_router.include_router(achievements.router)
api_router.include_router(analytics.router)
api_router.include_router(leaderboard.router)
api_router.include_router(boss.router)
api_router.include_router(duels.router)
