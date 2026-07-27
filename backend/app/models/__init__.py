"""SQLAlchemy models. Importing this package registers every table on Base.metadata."""

from app.db.base import Base
from app.models.content import Achievement, Problem, ProblemLanguage, ProblemTest, Zone
from app.models.enums import (
    BossStatus,
    ChestTier,
    Difficulty,
    SubmissionStatus,
    TestVisibility,
    XpSource,
)
from app.models.gameplay import (
    BossSession,
    ChestUnlock,
    DailyQuest,
    Submission,
    UserAchievement,
    XpEvent,
)
from app.models.user import Progress, User

__all__ = [
    "Achievement",
    "Base",
    "BossSession",
    "BossStatus",
    "ChestTier",
    "ChestUnlock",
    "DailyQuest",
    "Difficulty",
    "Problem",
    "ProblemLanguage",
    "ProblemTest",
    "Progress",
    "Submission",
    "SubmissionStatus",
    "TestVisibility",
    "User",
    "UserAchievement",
    "XpEvent",
    "XpSource",
    "Zone",
]
