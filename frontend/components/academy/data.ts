// Presentation constants and pure derivations for the Academy dashboard.
//
// Every number the toy actually earns now comes from the API (see lib/types.ts) — what
// lives here is styling: which colours a pegboard row lights up in, how tall a podium
// step is, where the climbing shelves sit.

import type { Leader } from "@/lib/types";

export const FREDOKA = "var(--font-fredoka), system-ui, sans-serif";
export const DARK = "#2E2620";
export const MONO = "ui-monospace, Menlo, monospace";

export type NavItem = {
  href: string;
  /** What the sidebar button reads. */
  label: string;
  /** What the topbar and the document title read — only "Problem" differs. */
  title: string;
  sub: string;
  color: string;
};

export const NAV: NavItem[] = [
  { href: "/academy", label: "Playroom", title: "Playroom", sub: "Home", color: "#EF5B54" },
  { href: "/academy/quests", label: "Quest Map", title: "Quest Map", sub: "Explore", color: "#4FB0E5" },
  { href: "/academy/problem", label: "Problem", title: "Problem View", sub: "Today's toy", color: "#6FBF73" },
  { href: "/academy/boss", label: "Boss Battle", title: "Boss Battle", sub: "Mock round", color: "#8B6FD6" },
  { href: "/academy/duel", label: "Duel", title: "Duel", sub: "1v1", color: "#E0566B" },
  { href: "/academy/achievements", label: "Merit Sash", title: "Merit Sash", sub: "Badges", color: "#F7C948" },
  { href: "/academy/analytics", label: "Analytics", title: "Analytics", sub: "Progress", color: "#E08A3C" },
  { href: "/academy/leaderboard", label: "Shelf of Fame", title: "Shelf of Fame", sub: "Ranks", color: "#3E8FC4" },
  { href: "/academy/profile", label: "Profile", title: "Profile", sub: "Account", color: "#4FB0E5" },
];

/**
 * Is this nav item the one the given path belongs to?
 *
 * `/academy` is the Playroom itself, so it matches only itself — every other tab also
 * claims its children, which is what keeps "Problem" lit on `/academy/problem/two-sum`.
 */
export function isNavActive(pathname: string, href: string): boolean {
  if (href === "/academy") return pathname === href;
  return pathname === href || pathname.startsWith(`${href}/`);
}

export function titleForPath(pathname: string): string {
  return NAV.find((n) => isNavActive(pathname, n.href))?.title ?? "Playroom";
}

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

// ---- Problem difficulty pills
export type Tone = { bg: string; border: string; color: string };
export const DIFFICULTY_STYLE: Record<string, Tone> = {
  easy: { bg: "#EAF7D9", border: "#6FBF73", color: "#4C7A2F" },
  medium: { bg: "#FDF3D6", border: "#E0A93C", color: "#A9761F" },
  hard: { bg: "#FDECEC", border: "#EF5B54", color: "#B4342D" },
};

export function difficultyTone(difficulty: string): Tone {
  return DIFFICULTY_STYLE[difficulty] ?? DIFFICULTY_STYLE.medium;
}

// ---- Analytics: pattern coverage pegboard
const PEG_SCALE = ["#F4C0C0", "#F7C948", "#8FD08F", "#6FBF73", "#4C9E51"];

/** Lit-peg colour for a 1-5 coverage level. */
export function pegColor(level: number): string {
  return PEG_SCALE[level - 1] ?? "#6FBF73";
}

// ---- Analytics: unaided-solve gauge
export function gaugeBackground(rate: number): string {
  const deg = (rate / 100) * 280;
  return `conic-gradient(from 220deg,#6FBF73 0deg ${deg}deg,#E4D6B8 ${deg}deg 280deg,transparent 280deg 360deg)`;
}

// ---- Leaderboard podium
export type PodiumSpot = Leader & { height: number; medal: string };

const PODIUM_STEPS: Record<number, { height: number; medal: string }> = {
  1: { height: 128, medal: "#F7C948" },
  2: { height: 96, medal: "#C0C0C0" },
  3: { height: 74, medal: "#CD7F32" },
};

/** The API returns the podium already ordered 2nd, 1st, 3rd — this only adds the step. */
export function buildPodium(podium: Leader[]): PodiumSpot[] {
  return podium.map((l) => ({ ...l, ...(PODIUM_STEPS[l.rank] ?? { height: 60, medal: "#C9A96A" }) }));
}

// ---- Profile: notification toggles
export type NotifKey = "streak" | "weekly" | "bosses";
export type NotifToggle = { key: NotifKey; label: string };
export const TOGGLES: NotifToggle[] = [
  { key: "streak", label: "Streak reminders (don’t break the chain!)" },
  { key: "weekly", label: "Weekly progress recap" },
  { key: "bosses", label: "New Boss Battle alerts" },
];

// ---- Topbar streak heatmap: 36 activity levels (0-4) -> swatches
const STREAK_SCALE = ["#EFE1C2", "#C8E6A8", "#8FD08F", "#6FBF73", "#4C9E51"];

export function streakColors(cells: number[]): string[] {
  return cells.map((lvl) => STREAK_SCALE[Math.max(0, Math.min(lvl, STREAK_SCALE.length - 1))]);
}

export function fmtTime(t: number): string {
  const m = Math.floor(t / 60);
  const s = t % 60;
  return `${m}:${String(s).padStart(2, "0")}`;
}
