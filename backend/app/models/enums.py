from enum import StrEnum


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ChestTier(StrEnum):
    """Tier 1 (the pattern explainer) is always free, so it is not a chest."""

    HINT = "hint"
    APPROACH = "approach"
    SOLUTION = "solution"


class SubmissionStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"


class BossStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class XpSource(StrEnum):
    SOLVE = "solve"
    WIND_UP = "wind_up"
    BOSS = "boss"
    ACHIEVEMENT = "achievement"
    STREAK = "streak"
