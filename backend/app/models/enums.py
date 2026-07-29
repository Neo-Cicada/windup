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
    """A submission's place in the judging pipeline, then its verdict.

    PENDING/RUNNING are queue states — a submission in one of them has not been
    graded and must never count as an attempt, a solve, or a boss round.
    """

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"  # the code raised before every case could be judged
    TIMEOUT = "timeout"  # burned the whole fuel budget

    @property
    def is_terminal(self) -> bool:
        return self not in (SubmissionStatus.PENDING, SubmissionStatus.RUNNING)


class TestVisibility(StrEnum):
    """Example cases ship to the client; hidden ones never leave the server."""

    EXAMPLE = "example"
    HIDDEN = "hidden"


class BossStatus(StrEnum):
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"
    ABANDONED = "abandoned"


class DuelStatus(StrEnum):
    """A head-to-head race's place in its life.

    Deliberately the same vocabulary as BossStatus, minus PAUSED — two toys share one
    clock, so pausing is both meaningless and an obvious exploit.
    """

    WAITING = "waiting"  # the invite is out, nobody has accepted
    ACTIVE = "active"  # both toys in, clock running
    COMPLETED = "completed"  # someone won — on rounds or on a forfeit
    EXPIRED = "expired"  # the invite went stale, or the clock ran out
    ABANDONED = "abandoned"  # called off before it started, or both walked away


class XpSource(StrEnum):
    SOLVE = "solve"
    WIND_UP = "wind_up"
    BOSS = "boss"
    DUEL = "duel"
    ACHIEVEMENT = "achievement"
    STREAK = "streak"
