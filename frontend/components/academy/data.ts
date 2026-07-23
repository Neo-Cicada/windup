// Static definitions and pure derivations for the Academy dashboard.
// Mirrors the data model in the "Toybox Academy" design file.

export const FREDOKA = "var(--font-fredoka), system-ui, sans-serif";
export const DARK = "#2E2620";
export const MONO = "ui-monospace, Menlo, monospace";

export type ScreenKey =
  | "dashboard"
  | "quests"
  | "problem"
  | "boss"
  | "achievements"
  | "analytics"
  | "leaderboard"
  | "workshop";

export type NavItem = {
  key: ScreenKey;
  label: string;
  sub: string;
  color: string;
};

export const NAV: NavItem[] = [
  { key: "dashboard", label: "Playroom", sub: "Home", color: "#EF5B54" },
  { key: "quests", label: "Quest Map", sub: "Explore", color: "#4FB0E5" },
  { key: "problem", label: "Problem", sub: "Today's toy", color: "#6FBF73" },
  { key: "boss", label: "Boss Battle", sub: "Mock round", color: "#8B6FD6" },
  { key: "achievements", label: "Merit Sash", sub: "Badges", color: "#F7C948" },
  { key: "analytics", label: "Analytics", sub: "Progress", color: "#E08A3C" },
  { key: "leaderboard", label: "Shelf of Fame", sub: "Ranks", color: "#3E8FC4" },
  { key: "workshop", label: "Profile", sub: "Account", color: "#4FB0E5" },
];

export const TITLES: Record<ScreenKey, string> = {
  dashboard: "Playroom",
  quests: "Quest Map",
  problem: "Problem View",
  boss: "Boss Battle",
  achievements: "Merit Sash",
  analytics: "Analytics",
  leaderboard: "Shelf of Fame",
  workshop: "Profile",
};

export const LEVEL_NAMES = [
  "",
  "Freshly Unboxed",
  "Wind-Up Rookie",
  "Shelf Climber",
  "Spring-Loaded",
  "Top-Shelf Talent",
  "Legendary Toy",
];

export function levelName(level: number): string {
  return LEVEL_NAMES[Math.min(level, 6)];
}

// ---- Today's quests
export type Quest = { name: string; zone: string; pct: number; color: string };

export const QUESTS: Quest[] = [
  { name: "Two Sum", zone: "BUILDING BLOCKS", pct: 60, color: "#6FBF73" },
  { name: "Reverse Linked List", zone: "MARBLE RUN", pct: 25, color: "#4FB0E5" },
  { name: "Number of Islands", zone: "BOARD GAME", pct: 0, color: "#EF5B54" },
];

// ---- Climbing shelves (top row first)
export type Shelf = { label: string; lvl: number };
const SHELF_DEFS: Shelf[] = [
  { label: "TOP SHELF", lvl: 5 },
  { label: "MID SHELF", lvl: 4 },
  { label: "LOW SHELF", lvl: 3 },
  { label: "THE FLOOR", lvl: 1 },
];
export const SHELF_ROW_H = 48;

export type ShelfRow = Shelf & { here: boolean; top: number };

export function buildShelves(level: number): ShelfRow[] {
  const last = SHELF_DEFS.length - 1;
  return SHELF_DEFS.map((s, i) => {
    // upper bound of this shelf's level band (Infinity for the top shelf)
    const upper = i === 0 ? Infinity : SHELF_DEFS[i - 1].lvl;
    const here =
      i === last ? level <= s.lvl : level >= s.lvl && level < upper;
    return { ...s, here, top: i * SHELF_ROW_H };
  });
}

// ---- Quest Map zones
export type Zone = {
  name: string;
  pattern: string;
  color: string;
  done: number;
  total: number;
  blurb: string;
};

export const ZONES: Zone[] = [
  { name: "Building Blocks", pattern: "Arrays & Strings", color: "#6FBF73", done: 14, total: 20, blurb: "Snap-together cubes" },
  { name: "Marble Run", pattern: "Linked Lists", color: "#4FB0E5", done: 6, total: 16, blurb: "Chutes & pointers" },
  { name: "Board Game", pattern: "Graphs & Trees", color: "#EF5B54", done: 9, total: 24, blurb: "Roll, branch, explore" },
  { name: "Toy Kitchen", pattern: "SQL", color: "#F7C948", done: 11, total: 18, blurb: "Recipes & queries" },
  { name: "Stacking Cups", pattern: "Stacks & Queues", color: "#E08A3C", done: 4, total: 12, blurb: "Last in, first out" },
  { name: "Puzzle Box", pattern: "Dynamic Programming", color: "#8B6FD6", done: 2, total: 22, blurb: "Solve once, reuse" },
];

// ---- Achievements
export type Achievement = { name: string; desc: string; color: string; earned: boolean };

export const ACHIEVEMENTS: Achievement[] = [
  { name: "First Fix", desc: "Solve your first toy", color: "#6FBF73", earned: true },
  { name: "Week Winder", desc: "7-day streak", color: "#EF5B54", earned: true },
  { name: "Unaided Ace", desc: "10 solves, no chests", color: "#4FB0E5", earned: true },
  { name: "Block Master", desc: "Clear Building Blocks", color: "#F7C948", earned: true },
  { name: "Night Owl", desc: "Solve after midnight", color: "#8B6FD6", earned: true },
  { name: "Boss Slayer", desc: "Beat a Boss Battle", color: "#E08A3C", earned: true },
  { name: "Marble Champ", desc: "Clear Marble Run", color: "#4FB0E5", earned: false },
  { name: "Century Toy", desc: "Solve 100 problems", color: "#EF5B54", earned: false },
  { name: "Perfect Week", desc: "All quests, 7 days", color: "#6FBF73", earned: false },
  { name: "Graph Guru", desc: "Clear Board Game", color: "#8B6FD6", earned: false },
  { name: "Speed Wind", desc: "Solve under 5 min", color: "#F7C948", earned: false },
  { name: "Top Shelf", desc: "Reach Level 5", color: "#E08A3C", earned: false },
];

// ---- Analytics: charge earned this week
export type XpDay = { label: string; v: number; height: number; valLabel: number };
const XP_RAW: [string, number][] = [
  ["Mon", 180], ["Tue", 260], ["Wed", 140], ["Thu", 320],
  ["Fri", 300], ["Sat", 420], ["Sun", 360],
];
export function buildXpHistory(): XpDay[] {
  const max = Math.max(...XP_RAW.map((d) => d[1]));
  return XP_RAW.map(([label, v]) => ({
    label,
    v,
    valLabel: v,
    height: Math.round((v / max) * 160),
  }));
}

// ---- Analytics: pattern coverage pegboard
export type CoverageRow = { pattern: string; level: number; pegs: boolean[]; litColor: string };
const COVERAGE_DEFS: { pattern: string; level: number }[] = [
  { pattern: "Arrays & Strings", level: 5 },
  { pattern: "Linked Lists", level: 3 },
  { pattern: "Graphs & Trees", level: 4 },
  { pattern: "SQL", level: 4 },
  { pattern: "Stacks & Queues", level: 2 },
  { pattern: "Dynamic Prog.", level: 1 },
];
const PEG_SCALE = ["#F4C0C0", "#F7C948", "#8FD08F", "#6FBF73", "#4C9E51"];
export function buildCoverage(): CoverageRow[] {
  return COVERAGE_DEFS.map((c) => ({
    ...c,
    pegs: [0, 1, 2, 3, 4].map((i) => i < c.level),
    litColor: PEG_SCALE[c.level - 1] || "#6FBF73",
  }));
}

// ---- Analytics: unaided-solve gauge
export const UNAIDED_RATE = 74;
export function gaugeBackground(rate: number): string {
  const deg = (rate / 100) * 280;
  return `conic-gradient(from 220deg,#6FBF73 0deg ${deg}deg,#E4D6B8 ${deg}deg 280deg,transparent 280deg 360deg)`;
}

// ---- Leaderboard
export type Leader = { rank: number; name: string; xp: number; color: string; you: boolean };
export const LEADERS: Leader[] = [
  { rank: 1, name: "Cogsworth", xp: 9840, color: "#F7C948", you: false },
  { rank: 2, name: "Patches", xp: 9120, color: "#4FB0E5", you: false },
  { rank: 3, name: "Domino", xp: 8760, color: "#EF5B54", you: false },
  { rank: 4, name: "Wheels", xp: 7990, color: "#8B6FD6", you: false },
  { rank: 5, name: "Squeak", xp: 7420, color: "#E08A3C", you: false },
  { rank: 6, name: "Bramble (You)", xp: 7180, color: "#6FBF73", you: true },
  { rank: 7, name: "Tumble", xp: 6810, color: "#4FB0E5", you: false },
  { rank: 8, name: "Bolt", xp: 6540, color: "#EF5B54", you: false },
];

export type PodiumSpot = { name: string; xp: number; rank: number; color: string; height: number; medal: string };
export function buildPodium(): PodiumSpot[] {
  // order: 2nd, 1st, 3rd
  const spec: [Leader, number, string][] = [
    [LEADERS[1], 96, "#C0C0C0"],
    [LEADERS[0], 128, "#F7C948"],
    [LEADERS[2], 74, "#CD7F32"],
  ];
  return spec.map(([l, height, medal]) => ({
    name: l.name, xp: l.xp, rank: l.rank, color: l.color, height, medal,
  }));
}

// ---- Profile: plans + notifications
export type Plan = { key: string; name: string; price: string; perk: string };
export const PLANS: Plan[] = [
  { key: "free", name: "Free", price: "$0", perk: "3 quests/day" },
  { key: "pro", name: "Pro", price: "$9/mo", perk: "Unlimited + bosses" },
  { key: "team", name: "Playroom", price: "$29/mo", perk: "For toy squads" },
];

export type NotifKey = "streak" | "weekly" | "bosses";
export type NotifToggle = { key: NotifKey; label: string };
export const TOGGLES: NotifToggle[] = [
  { key: "streak", label: "Streak reminders (don’t break the chain!)" },
  { key: "weekly", label: "Weekly progress recap" },
  { key: "bosses", label: "New Boss Battle alerts" },
];

// ---- Topbar streak heatmap (deterministic 3x12 grid, recent = hotter)
const STREAK_SCALE = ["#EFE1C2", "#C8E6A8", "#8FD08F", "#6FBF73", "#4C9E51"];
export function buildStreakCells(): string[] {
  return Array.from({ length: 36 }, (_, i) => {
    const col = Math.floor(i / 3);
    let lvl: number;
    if (col >= 8) lvl = 3 + (i % 2); // this week: hot streak
    else if (col >= 5) lvl = 1 + (i % 3); // ramping up
    else lvl = (i * 7) % 5 === 0 ? 2 : i % 4 === 0 ? 1 : 0; // sparse history
    return STREAK_SCALE[lvl];
  });
}

export function fmtTime(t: number): string {
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
