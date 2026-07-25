import { FREDOKA, buildPodium } from "../data";
import type { LeaderboardSummary } from "@/lib/types";

type Props = { data: LeaderboardSummary };

export function Leaderboard({ data }: Props) {
  const podium = buildPodium(data.podium);

  return (
    <div data-screen-label="Leaderboard" style={{ maxWidth: 920, margin: "0 auto" }}>
      <div style={{ textAlign: "center", marginBottom: 26 }}>
        <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 28, margin: 0 }}>The Shelf of Fame</h1>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "#8B7358", fontWeight: 700 }}>
          The most wound-up toys in the playroom
          {data.your_rank !== null ? ` — you're sitting at #${data.your_rank}.` : "."}
        </p>
      </div>

      {/* podium */}
      {podium.length > 0 && (
        <>
          <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "center", gap: 16, marginBottom: 30 }}>
            {podium.map((p) => (
              <div key={p.rank} style={{ flex: 1, maxWidth: 200, display: "flex", flexDirection: "column", alignItems: "center" }}>
                <div style={{ width: 56, height: 56, borderRadius: 16, border: "4px solid #2E2620", background: p.color, boxShadow: "0 4px 0 #2E2620", marginBottom: 8 }} />
                <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15, marginBottom: 2, textAlign: "center" }}>{p.name}</div>
                <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", marginBottom: 8 }}>{p.xp} charge</div>
                <div style={{ width: "100%", height: p.height, border: "4px solid #2E2620", borderBottom: 0, borderRadius: "16px 16px 0 0", background: p.medal, display: "flex", alignItems: "flex-start", justifyContent: "center", paddingTop: 8, fontFamily: FREDOKA, fontWeight: 700, fontSize: 24, color: "#2E2620" }}>
                  {p.rank}
                </div>
              </div>
            ))}
          </div>

          {/* wood shelf under podium */}
          <div style={{ height: 20, border: "4px solid #2E2620", borderRadius: 10, background: "repeating-linear-gradient(90deg,#C9A96A 0 20px,#BE9C5C 20px 23px)", marginBottom: 26, boxShadow: "0 6px 0 #A98544" }} />
        </>
      )}

      {/* full ranking */}
      <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
        {data.leaders.map((l) => (
          <div
            key={l.rank}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 14,
              padding: "11px 16px",
              borderRadius: 16,
              border: "3px solid #2E2620",
              background: l.you ? "#EAF7D9" : "#fff",
              boxShadow: l.you ? "0 4px 0 #CFE4B6" : "0 4px 0 #E0CBA0",
            }}
          >
            <div style={{ width: 30, fontFamily: FREDOKA, fontWeight: 700, fontSize: 18, color: "#B0794A", textAlign: "center" }}>{l.rank}</div>
            <span style={{ width: 38, height: 38, flex: "none", borderRadius: 12, border: "3px solid #2E2620", background: l.color }} />
            <div style={{ flex: 1, fontFamily: FREDOKA, fontWeight: 600, fontSize: 16 }}>{l.name}</div>
            <div style={{ fontWeight: 800, fontSize: 14, color: "#5C4A3C" }}>{l.xp}</div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A" }}>charge</div>
          </div>
        ))}
      </div>
    </div>
  );
}
