export const FREDOKA = "var(--font-fredoka), system-ui, sans-serif";

export type Feature = {
  title: string;
  body: string;
  color: string;
};

export const FEATURES: Feature[] = [
  {
    title: "Explorable Quest Map",
    body: "Every DSA pattern is its own toy corner: building blocks for arrays, a marble run for linked lists, a board game for graphs.",
    color: "#4FB0E5",
  },
  {
    title: "Tiered Help Chests",
    body: "A free pattern explainer, then locked hint / approach / solution chests. Peek if you must, but you forfeit the unaided bonus.",
    color: "#F7C948",
  },
  {
    title: "Boss Battles",
    body: "Timed mock-interview rounds against giant boss toys. Beat the clock before the Jack-in-the-Box springs.",
    color: "#8B6FD6",
  },
  {
    title: "Merit Badges & Streaks",
    body: "Earn sticker badges, wind up your charge meter, and keep your spinning-top streak alive. Progress you can feel.",
    color: "#6FBF73",
  },
];

export type Step = {
  n: string;
  color: string;
  title: string;
  body: string;
};

export const STEPS: Step[] = [
  {
    n: "1",
    color: "#6FBF73",
    title: "Unbox your toy",
    body: "Create a free account and meet Sprocket, your wind-up coach.",
  },
  {
    n: "2",
    color: "#4FB0E5",
    title: "Fix broken toys",
    body: "Work through real interview problems disguised as playroom repairs.",
  },
  {
    n: "3",
    color: "#EF5B54",
    title: "Climb the shelves",
    body: "Level up, battle bosses, and reach the top shelf: Interview Ready.",
  },
];

export type Stat = { value: string; label: string; color: string };

export const STATS: Stat[] = [
  { value: "1,200+", label: "TOY PROBLEMS", color: "#F7C948" },
  { value: "14", label: "PATTERN CORNERS", color: "#6FBF73" },
  { value: "40k", label: "TOYS IN TRAINING", color: "#4FB0E5" },
  { value: "92%", label: "FELT MORE READY", color: "#EF5B54" },
];
