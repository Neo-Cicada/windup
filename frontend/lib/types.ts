// Mirrors backend/app/schemas — keep field names identical to the JSON on the wire.

export type Difficulty = "easy" | "medium" | "hard";
export type ChestTier = "hint" | "approach" | "solution";
export type BossStatus = "running" | "paused" | "completed" | "expired" | "abandoned";
export type DuelStatus = "waiting" | "active" | "completed" | "expired" | "abandoned";
/** `pending`/`running` are queue states — the judge hasn't ruled yet. */
export type SubmissionStatus =
  | "pending"
  | "running"
  | "passed"
  | "failed"
  | "error"
  | "timeout";

export const TERMINAL_STATUSES: SubmissionStatus[] = [
  "passed",
  "failed",
  "error",
  "timeout",
];

export type Avatar = { body: string; head: string; accent: string };

export type NotificationPrefs = { streak: boolean; weekly: boolean; bosses: boolean };

export type User = {
  id: string;
  email: string;
  toy_name: string;
  trainee_no: string;
  avatar: Avatar;
  notifications: NotificationPrefs;
};

export type TokenPair = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User | null;
};

export type Progress = {
  xp: number;
  xp_max: number;
  xp_pct: number;
  level: number;
  level_name: string;
  total_xp: number;
  coins: number;
  streak: number;
  longest_streak: number;
  solved_count: number;
  unaided_rate: number;
  interview_ready: number;
};

export type Zone = {
  id: string;
  slug: string;
  name: string;
  pattern: string;
  color: string;
  blurb: string;
  total: number;
  done: number;
};

export type Problem = {
  id: string;
  slug: string;
  title: string;
  difficulty: Difficulty;
  weight_label: string;
  xp_reward: number;
  zone_slug: string;
  zone_name: string;
  zone_color: string;
  solved: boolean;
};

export type Chests = { hint: boolean; approach: boolean; solution: boolean };

/** Locked tiers come back as null — the server never ships a chest you haven't opened. */
export type HelpShelf = {
  explainer: string;
  hint: string | null;
  approach: string | null;
  solution: string | null;
};

/** A visible example case. The hidden cases that actually grade never arrive here. */
export type TestCase = {
  ordinal: number;
  label: string;
  args: unknown[];
  expected: unknown;
};

/**
 * One bench: everything needed to open, run and submit in a single language.
 *
 * The example cases are deliberately not in here. They are the same whatever
 * you solve in — plain JSON, compared on the server — so one set of them grades
 * every language.
 */
export type ProblemLanguage = {
  language: string;
  label: string;
  /** Whether Run can execute this language locally. Submit always works. */
  runs_in_browser: boolean;
  entrypoint: string;
  starter_code: string;
  harness_preamble: string;
};

export type ProblemDetail = Problem & {
  prompt: string;
  example_input: string;
  example_output: string;
  /** The bench the workbench opens on; `languages` is what it may switch to. */
  language: string;
  starter_code: string;
  languages: ProblemLanguage[];
  help_shelf: HelpShelf;
  chests: Chests;
  unaided: boolean;
  unaided_bonus: number;
  /** false for problems with no test rig at all — they settle on the honour system. */
  graded: boolean;
  entrypoint: string;
  harness_preamble: string;
  example_tests: TestCase[];
  hidden_test_count: number;
};

export type ChestUnlockResult = {
  tier: ChestTier;
  content: string;
  chests: Chests;
  unaided: boolean;
  message: string;
};

export type Achievement = {
  slug: string;
  name: string;
  description: string;
  color: string;
  earned: boolean;
  earned_at: string | null;
};

/** 202 from submit — the code is queued, poll for the verdict. */
export type SubmissionAccepted = {
  submission_id: string;
  status: SubmissionStatus;
  poll_after_ms: number;
  queue_position: number;
};

/** The first failing case. `expected` is null for a hidden one, by design. */
export type SubmissionFailure = {
  ordinal: number;
  label: string;
  hidden: boolean;
  args: unknown[];
  actual: unknown;
  expected: unknown;
  stdout: string;
  error: string | null;
};

export type SubmissionResult = {
  submission_id: string;
  status: SubmissionStatus;
  /** Which bench judged it — the workbench may be at a different one by now. */
  language: string;
  unaided: boolean;
  /** null until the judge has ruled; everything below lands at once. */
  xp_awarded: number | null;
  coins_awarded: number | null;
  leveled_up: boolean | null;
  sprocket_message: string;
  confetti: number;
  newly_earned: Achievement[];
  progress: Progress | null;
  tests_passed: number;
  tests_total: number;
  runtime_ms: number | null;
  failure: SubmissionFailure | null;
  /** Waiting far longer than it should — `sprocket_message` says why. */
  stalled: boolean;
};

export type DailyQuest = {
  id: string;
  name: string;
  slug: string;
  zone: string;
  color: string;
  pct: number;
  completed: boolean;
  quest_date: string;
};

export type AchievementsSummary = {
  earned_count: number;
  total_count: number;
  label: string;
  items: Achievement[];
};

export type XpDay = { label: string; date: string; value: number; height: number };

export type CoverageRow = {
  pattern: string;
  zone_slug: string;
  level: number;
  solved: number;
  total: number;
};

/** `cells` is 36 activity levels (0-4), oldest first — a 3x12 grid. */
export type StreakSummary = { streak: number; longest_streak: number; cells: number[] };

export type AnalyticsSummary = {
  xp_history: XpDay[];
  xp_this_week: number;
  coverage: CoverageRow[];
  unaided_rate: number;
  streak: StreakSummary;
};

export type Leader = { rank: number; name: string; xp: number; color: string; you: boolean };

export type LeaderboardSummary = {
  leaders: Leader[];
  podium: Leader[];
  your_rank: number | null;
};

export type BossSession = {
  id: string;
  boss_name: string;
  status: BossStatus;
  total_seconds: number;
  remaining_seconds: number;
  time_label: string;
  pct: number;
  rounds_total: number;
  rounds_cleared: number;
  xp_awarded: number;
  button_label: string;
};

export type BossAction = "start" | "pause" | "resume" | "complete" | "abandon";

/**
 * A duel, always from the reading toy's own point of view — `you` and `them`, never
 * host and opponent. Both sides render from the same shape with no branching.
 */
export type DuelPlayer = {
  toy_name: string;
  avatar_body: string;
  avatar_head: string;
  rounds_cleared: number;
  /** Which chips light up on this side. */
  cleared_ordinals: number[];
  forfeited: boolean;
  xp_awarded: number;
};

export type DuelRound = {
  ordinal: number;
  slug: string;
  title: string;
  difficulty: Difficulty;
  zone: string;
  color: string;
  you_solved: boolean;
  they_solved: boolean;
};

export type Duel = {
  id: string;
  code: string;
  status: DuelStatus;
  rounds_total: number;
  total_seconds: number;
  remaining_seconds: number;
  time_label: string;
  pct: number;
  you: DuelPlayer;
  them: DuelPlayer | null;
  you_are_host: boolean;
  /** Empty until the duel starts — the server has nothing to reveal before then. */
  rounds: DuelRound[];
  winner: "you" | "them" | "draw" | null;
  outcome_label: string;
  invite_path: string;
  /** The server owns the cadence: 2s racing, 5s waiting, 0 means stop polling. */
  poll_after_ms: number;
};

/** What a non-participant sees of an invite. Structurally cannot carry the problems. */
export type DuelInvite = {
  code: string;
  status: DuelStatus;
  host_name: string;
  host_avatar: string;
  rounds_total: number;
  total_seconds: number;
  joinable: boolean;
  message: string;
};

export type DuelAction = "forfeit" | "cancel";

export type DashboardData = {
  toy_name: string;
  trainee_no: string;
  avatar_body: string;
  avatar_head: string;
  avatar_accent: string;
  sprocket_message: string;
  progress: Progress;
  badges_label: string;
  rank: number | null;
  quests: DailyQuest[];
  quests_done: number;
  /** false once today's wind-up has been claimed */
  wind_up_available: boolean;
};

