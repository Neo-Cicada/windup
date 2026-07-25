from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import BossStatus, ChestTier, Difficulty, SubmissionStatus


# ---- progress ---------------------------------------------------------------
class ProgressOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    xp: int
    xp_max: int
    xp_pct: int
    level: int
    level_name: str
    total_xp: int
    coins: int
    streak: int
    longest_streak: int
    solved_count: int
    unaided_rate: int
    interview_ready: int


# ---- zones & problems -------------------------------------------------------
class ZoneOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    name: str
    pattern: str
    color: str
    blurb: str
    total: int = 0
    done: int = 0


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    slug: str
    title: str
    difficulty: Difficulty
    weight_label: str
    xp_reward: int
    zone_slug: str
    zone_name: str
    zone_color: str
    solved: bool = False


class ChestsOut(BaseModel):
    hint: bool = False
    approach: bool = False
    solution: bool = False


class HelpShelfOut(BaseModel):
    """Locked tiers come back as null so the UI can render a closed chest."""

    explainer: str
    hint: str | None = None
    approach: str | None = None
    solution: str | None = None


class ProblemDetailOut(ProblemOut):
    prompt: str
    example_input: str
    example_output: str
    language: str
    starter_code: str
    help_shelf: HelpShelfOut
    chests: ChestsOut
    unaided: bool
    unaided_bonus: int


class ChestUnlockOut(BaseModel):
    tier: ChestTier
    content: str
    chests: ChestsOut
    unaided: bool
    message: str


# ---- submissions ------------------------------------------------------------
class SubmissionIn(BaseModel):
    code: str = Field(default="", max_length=20000)
    language: str = Field(default="python", max_length=24)
    status: SubmissionStatus = SubmissionStatus.PASSED
    duration_seconds: int | None = Field(default=None, ge=0, le=86_400)
    boss_session_id: UUID | None = None


class SubmissionResultOut(BaseModel):
    submission_id: UUID
    status: SubmissionStatus
    unaided: bool
    xp_awarded: int
    coins_awarded: int
    leveled_up: bool
    sprocket_message: str
    confetti: int
    newly_earned: list["AchievementOut"] = []
    progress: ProgressOut


# ---- quests -----------------------------------------------------------------
class DailyQuestOut(BaseModel):
    id: UUID
    name: str
    slug: str
    zone: str
    color: str
    pct: int
    completed: bool
    quest_date: date


# ---- achievements -----------------------------------------------------------
class AchievementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    name: str
    description: str
    color: str
    earned: bool = False
    earned_at: datetime | None = None


class AchievementsOut(BaseModel):
    earned_count: int
    total_count: int
    label: str
    items: list[AchievementOut]


# ---- analytics --------------------------------------------------------------
class XpDay(BaseModel):
    label: str
    date: date
    value: int
    height: int


class CoverageRow(BaseModel):
    pattern: str
    zone_slug: str
    level: int
    solved: int
    total: int


class StreakOut(BaseModel):
    streak: int
    longest_streak: int
    cells: list[int]  # 36 activity levels (0-4), oldest first — a 3x12 grid


class AnalyticsSummaryOut(BaseModel):
    xp_history: list[XpDay]
    xp_this_week: int
    coverage: list[CoverageRow]
    unaided_rate: int
    streak: StreakOut


# ---- leaderboard ------------------------------------------------------------
class LeaderOut(BaseModel):
    rank: int
    name: str
    xp: int
    color: str
    you: bool = False


class LeaderboardOut(BaseModel):
    leaders: list[LeaderOut]
    podium: list[LeaderOut]
    your_rank: int | None = None


# ---- boss battle ------------------------------------------------------------
class BossActionIn(BaseModel):
    action: str = Field(pattern="^(start|pause|resume|complete|abandon)$")


class BossSessionOut(BaseModel):
    id: UUID
    boss_name: str
    status: BossStatus
    total_seconds: int
    remaining_seconds: int
    time_label: str
    pct: int
    rounds_total: int
    rounds_cleared: int
    xp_awarded: int
    button_label: str


# ---- dashboard --------------------------------------------------------------
class DashboardOut(BaseModel):
    toy_name: str
    trainee_no: str
    avatar_body: str
    avatar_head: str
    avatar_accent: str
    sprocket_message: str
    progress: ProgressOut
    badges_label: str
    rank: int | None
    quests: list[DailyQuestOut]
    quests_done: int
    wind_up_available: bool  # false once today's wind-up has been claimed


SubmissionResultOut.model_rebuild()
