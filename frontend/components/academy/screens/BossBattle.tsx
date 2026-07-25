import { FREDOKA } from "../data";
import { JackBoss } from "../illustrations";
import type { BossSession } from "@/lib/types";

type Props = {
  session: BossSession | null;
  /** Ticked down locally between requests; the server owns the real clock. */
  timeFmt: string;
  pct: number;
  running: boolean;
  label: string;
  pending: boolean;
  error: string | null;
  onToggle: () => void;
  onComplete: () => void;
  onAbandon: () => void;
};

type RoundTone = { border: string; label: string; color: string };

function roundTone(index: number, cleared: number, running: boolean): RoundTone {
  if (index < cleared) return { border: "#6FBF73", label: "solved", color: "#8FD08F" };
  if (index === cleared && running) return { border: "#F7C948", label: "in progress", color: "#F7C948" };
  return { border: "#6B5A4A", label: "locked", color: "#D6C7B4" };
}

export function BossBattle({ session, timeFmt, pct, running, label, pending, error, onToggle, onComplete, onAbandon }: Props) {
  const roundsTotal = session?.rounds_total ?? 3;
  const cleared = session?.rounds_cleared ?? 0;
  const finished = session?.status === "completed";

  return (
    <div data-screen-label="Boss Battle" style={{ maxWidth: 960, margin: "0 auto" }}>
      <div style={{ background: "#2E2620", border: "4px solid #2E2620", borderRadius: 28, padding: 34, boxShadow: "0 12px 0 #1c1712", position: "relative", overflow: "hidden", textAlign: "center" }}>
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 30%,rgba(239,91,84,.35),transparent 60%)" }} />
        <div style={{ position: "relative" }}>
          <div style={{ display: "inline-block", background: "#EF5B54", border: "3px solid #F7C948", color: "#fff", fontFamily: FREDOKA, fontWeight: 700, fontSize: 13, letterSpacing: 2, padding: "6px 16px", borderRadius: 20, marginBottom: 20 }}>
            ⚡ BOSS BATTLE · MOCK INTERVIEW ⚡
          </div>

          <div style={{ display: "flex", justifyContent: "center", marginBottom: 8 }}>
            <JackBoss />
          </div>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 30, color: "#fff", margin: "0 0 6px" }}>
            {session?.boss_name ?? "The Jack-in-the-Box"}
          </h1>
          <p style={{ margin: "0 0 24px", color: "#D6C7B4", fontSize: 14, fontWeight: 700 }}>
            {roundsTotal} problems · 15 minutes · no chests allowed. Springs out when the clock runs down!
          </p>

          <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", background: "#FBF4E4", border: "5px solid #F7C948", borderRadius: 22, padding: "18px 40px", marginBottom: 22, animation: running ? "tick 1s ease-in-out infinite" : undefined }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", letterSpacing: 2 }}>TIME REMAINING</div>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 56, lineHeight: 1, color: "#EF5B54", fontVariantNumeric: "tabular-nums" }}>{timeFmt}</div>
            <div style={{ width: 220, height: 12, background: "#EFE1C2", border: "3px solid #2E2620", borderRadius: 8, overflow: "hidden", marginTop: 10 }}>
              <div style={{ height: "100%", width: `${pct}%`, background: "repeating-linear-gradient(45deg,#EF5B54 0 8px,#E2504A 8px 16px)" }} />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
            <button
              className="tap"
              onClick={onToggle}
              disabled={pending}
              style={{ border: "4px solid #F7C948", borderRadius: 18, background: "#EF5B54", color: "#fff", fontWeight: 700, fontSize: 18, padding: "14px 40px", boxShadow: "0 6px 0 #A9302B", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
            >
              {pending ? "Winding…" : label}
            </button>
            {session && !finished && (
              <button
                className="tap"
                onClick={onComplete}
                disabled={pending}
                style={{ border: "4px solid #6FBF73", borderRadius: 18, background: "rgba(251,244,228,.14)", color: "#EAF7D9", fontWeight: 700, fontSize: 16, padding: "14px 26px", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
              >
                Call it a win
              </button>
            )}
            {session && !finished && (
              <button
                className="tap"
                onClick={onAbandon}
                disabled={pending}
                style={{ border: "4px solid #6B5A4A", borderRadius: 18, background: "transparent", color: "#D6C7B4", fontWeight: 700, fontSize: 16, padding: "14px 22px", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
              >
                Run away
              </button>
            )}
          </div>

          {error && (
            <div style={{ margin: "20px auto 0", maxWidth: 520, background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#B4342D" }} role="alert">
              {error}
            </div>
          )}

          {finished && (
            <div style={{ margin: "20px auto 0", maxWidth: 520, background: "#EAF7D9", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#4C7A2F" }}>
              Boss down! +{session?.xp_awarded ?? 0} charge, speed bonus included.
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "center", gap: 14, marginTop: 26, flexWrap: "wrap" }}>
            {Array.from({ length: roundsTotal }, (_, i) => {
              const tone = roundTone(i, cleared, running);
              return (
                <div key={i} style={{ background: "rgba(251,244,228,.14)", border: `3px solid ${tone.border}`, borderRadius: 14, padding: "10px 18px", color: "#fff" }}>
                  <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>Round {i + 1}</div>
                  <div style={{ fontSize: 10, fontWeight: 800, color: tone.color }}>{tone.label}</div>
                </div>
              );
            })}
          </div>

          <p style={{ margin: "22px auto 0", maxWidth: 560, color: "#B9A98C", fontSize: 12, fontWeight: 700, lineHeight: 1.5 }}>
            Rounds only clear when you solve a fresh problem during the fight — head to the Quest
            Map, fix {Math.max(0, roundsTotal - cleared)} more, then come back and call it.
          </p>
        </div>
      </div>
    </div>
  );
}
