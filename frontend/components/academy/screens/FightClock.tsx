import { FREDOKA } from "../data";

type Props = {
  /** Ticked down locally between requests; the server owns the real clock. */
  timeFmt: string;
  pct: number;
  running: boolean;
  label?: string;
};

/**
 * The cream-and-gold countdown, shared by the boss fight and the duel.
 *
 * Extracted because both screens should read identically — a toy under a clock should
 * not have to work out which game they're in. The class names stay `acad-boss-*` so the
 * responsive rules in globals.css keep applying to both.
 */
export function FightClock({ timeFmt, pct, running, label = "TIME REMAINING" }: Props) {
  return (
    <div
      className="acad-boss-clock"
      style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", background: "#FBF4E4", border: "5px solid #F7C948", borderRadius: 22, padding: "18px 40px", maxWidth: "100%", animation: running ? "tick 1s ease-in-out infinite" : undefined }}
    >
      <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", letterSpacing: 2 }}>{label}</div>
      <div className="acad-boss-time" style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 56, lineHeight: 1, color: "#EF5B54", fontVariantNumeric: "tabular-nums" }}>
        {timeFmt}
      </div>
      <div className="acad-boss-bar" style={{ width: 220, maxWidth: "100%", height: 12, background: "#EFE1C2", border: "3px solid #2E2620", borderRadius: 8, overflow: "hidden", marginTop: 10 }}>
        <div style={{ height: "100%", width: `${pct}%`, background: "repeating-linear-gradient(45deg,#EF5B54 0 8px,#E2504A 8px 16px)" }} />
      </div>
    </div>
  );
}
