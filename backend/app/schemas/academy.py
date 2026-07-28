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


class TestCaseOut(BaseModel):
    """A visible example case, for the in-browser "Run" button.

    Only `example`-visibility cases are ever serialised. The hidden ones grade
    the submission and never leave the server — same rule as a locked chest.
    """

    ordinal: int
    label: str
    args: list
    expected: object


class LanguageOut(BaseModel):
    """A language this deployment offers, for the workbench's picker."""

    slug: str
    label: str
    extension: str
    runs_in_browser: bool


class ProblemLanguageOut(BaseModel):
    """One bench: everything needed to open, run and submit in one language.

    The test cases are *not* in here — they are the same for every language,
    because they are plain JSON compared on the host.
    """

    language: str
    label: str
    runs_in_browser: bool
    entrypoint: str
    starter_code: str
    # The browser needs the adapters to run the examples locally; they define
    # ListNode and friends, and give nothing away that the prompt doesn't.
    harness_preamble: str = ""


class ProblemDetailOut(ProblemOut):
    prompt: str
    example_input: str
    example_output: str
    # The language the workbench opens on. `languages` is what it may switch to.
    language: str
    starter_code: str
    languages: list[ProblemLanguageOut] = []
    help_shelf: HelpShelfOut
    chests: ChestsOut
    unaided: bool
    unaided_bonus: int
    # False for problems with no test rig at all — they settle on the honour system.
    graded: bool = True
    entrypoint: str = ""
    harness_preamble: str = ""
    example_tests: list[TestCaseOut] = []
    hidden_test_count: int = 0


class ChestUnlockOut(BaseModel):
    tier: ChestTier
    content: str
    chests: ChestsOut
    unaided: bool
    message: str


# ---- submissions ------------------------------------------------------------
class SubmissionIn(BaseModel):
    """What the workbench sends.

    Note the absence of `status`. The client used to declare its own verdict and
    the server took its word for it; now the judge decides, so there is nothing
    here to declare it with.
    """

    code: str = Field(min_length=1, max_length=20000)
    # Which bench the toy worked at. The server checks the problem actually
    # offers it; an unset value means the problem's default language.
    language: str | None = Field(default=None, max_length=24)
    duration_seconds: int | None = Field(default=None, ge=0, le=86_400)
    boss_session_id: UUID | None = None


class SubmissionAcceptedOut(BaseModel):
    """202 from submit: it's queued, poll for the verdict."""

    submission_id: UUID
    status: SubmissionStatus = SubmissionStatus.PENDING
    poll_after_ms: int = 400
    queue_position: int = 0


class FailureOut(BaseModel):
    """The first failing case, and only as much of it as is fair to show."""

    ordinal: int = 0
    label: str = ""
    hidden: bool = False
    args: list = []
    actual: object = None
    # Omitted for hidden cases — handing it back would make them a lookup table.
    expected: object = None
    stdout: str = ""
    error: str | None = None


class SubmissionResultOut(BaseModel):
    submission_id: UUID
    status: SubmissionStatus
    # Which bench judged it. Echoed back because the workbench can be at a
    # different one by the time a verdict lands.
    language: str = ""
    unaided: bool
    # Null until the judge has ruled — everything below is settled at once.
    xp_awarded: int | None = None
    coins_awarded: int | None = None
    leveled_up: bool | None = None
    sprocket_message: str = ""
    confetti: int = 0
    newly_earned: list["AchievementOut"] = []
    progress: ProgressOut | None = None
    tests_passed: int = 0
    tests_total: int = 0
    runtime_ms: int | None = None
    failure: FailureOut | None = None
    # True when a still-unjudged submission has been waiting long enough that
    # something is likely wrong (usually: no judge worker is running). The
    # message says which. The client stops polling rather than waiting it out.
    stalled: bool = False


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
