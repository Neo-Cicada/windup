// Mirrors backend/app/schemas — keep field names identical to the JSON on the wire.

export type Difficulty = "easy" | "medium" | "hard";
export type ChestTier = "hint" | "approach" | "solution";
export type BossStatus = "running" | "paused" | "completed" | "expired" | "abandoned";
export type SubmissionStatus = "passed" | "failed";

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

export type ProblemDetail = Problem & {
  prompt: string;
  example_input: string;
  example_output: string;
  language: string;
  starter_code: string;
  help_shelf: HelpShelf;
  chests: Chests;
  unaided: boolean;
  unaided_bonus: number;
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

export type SubmissionResult = {
  submission_id: string;
  status: SubmissionStatus;
  unaided: boolean;
  xp_awarded: number;
  coins_awarded: number;
  leveled_up: boolean;
  sprocket_message: string;
  confetti: number;
  newly_earned: Achievement[];
  progress: Progress;
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

