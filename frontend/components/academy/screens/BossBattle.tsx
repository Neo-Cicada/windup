import { FREDOKA } from "../data";
import { JackBoss } from "../illustrations";

type Props = {
  timeFmt: string;
  pct: number;
  running: boolean;
  label: string;
  onToggle: () => void;
};

export function BossBattle({ timeFmt, pct, running, label, onToggle }: Props) {
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
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 30, color: "#fff", margin: "0 0 6px" }}>The Jack-in-the-Box</h1>
          <p style={{ margin: "0 0 24px", color: "#D6C7B4", fontSize: 14, fontWeight: 700 }}>3 problems · 15 minutes · no chests allowed. Springs out when the clock runs down!</p>

          <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", background: "#FBF4E4", border: "5px solid #F7C948", borderRadius: 22, padding: "18px 40px", marginBottom: 22, animation: running ? "tick 1s ease-in-out infinite" : undefined }}>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", letterSpacing: 2 }}>TIME REMAINING</div>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 56, lineHeight: 1, color: "#EF5B54", fontVariantNumeric: "tabular-nums" }}>{timeFmt}</div>
            <div style={{ width: 220, height: 12, background: "#EFE1C2", border: "3px solid #2E2620", borderRadius: 8, overflow: "hidden", marginTop: 10 }}>
              <div style={{ height: "100%", width: `${pct}%`, background: "repeating-linear-gradient(45deg,#EF5B54 0 8px,#E2504A 8px 16px)" }} />
            </div>
          </div>

          <div>
            <button className="tap" onClick={onToggle} style={{ border: "4px solid #F7C948", borderRadius: 18, background: "#EF5B54", color: "#fff", fontWeight: 700, fontSize: 18, padding: "14px 40px", boxShadow: "0 6px 0 #A9302B", fontFamily: FREDOKA }}>
              {label}
            </button>
          </div>

          <div style={{ display: "flex", justifyContent: "center", gap: 14, marginTop: 26 }}>
            <div style={{ background: "rgba(251,244,228,.14)", border: "3px solid #6FBF73", borderRadius: 14, padding: "10px 18px", color: "#fff" }}>
              <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>Round 1</div>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#8FD08F" }}>Arrays · solved</div>
            </div>
            <div style={{ background: "rgba(251,244,228,.14)", border: "3px solid #F7C948", borderRadius: 14, padding: "10px 18px", color: "#fff" }}>
              <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>Round 2</div>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#F7C948" }}>Trees · in progress</div>
            </div>
            <div style={{ background: "rgba(251,244,228,.14)", border: "3px solid #6B5A4A", borderRadius: 14, padding: "10px 18px", color: "#D6C7B4" }}>
              <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>Round 3</div>
              <div style={{ fontSize: 10, fontWeight: 800 }}>DP · locked</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
