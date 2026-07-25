import { FREDOKA, gaugeBackground, pegColor } from "../data";
import type { AnalyticsSummary } from "@/lib/types";

type Props = { data: AnalyticsSummary };

const card = {
  background: "#fff",
  border: "4px solid #2E2620",
  borderRadius: 24,
  boxShadow: "0 8px 0 #E0CBA0",
} as const;

export function Analytics({ data }: Props) {
  const { xp_history: history, coverage, unaided_rate: unaided } = data;

  return (
    <div data-screen-label="Analytics" style={{ maxWidth: 1180, margin: "0 auto" }}>
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 22, marginBottom: 22 }} className="acad-analytics-top">
        {/* Charge earned */}
        <section style={{ ...card, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 4 }}>
            <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: 0 }}>Charge Earned</h2>
            <span style={{ fontSize: 12, fontWeight: 800, color: "#9B7B5B" }}>
              This week · +{data.xp_this_week.toLocaleString()}
            </span>
          </div>
          <p style={{ margin: "0 0 18px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>Each block ≈ 60 charge.</p>
          <div style={{ display: "flex", alignItems: "flex-end", gap: 14, height: 190, paddingTop: 10 }}>
            {history.map((d) => (
              <div key={d.date} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 7 }}>
                <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A" }}>{d.value}</div>
                <div style={{ height: d.height, width: "100%", maxWidth: 42, background: "repeating-linear-gradient(#6FBF73 0 14px,#5FAF63 14px 16px)", border: "3px solid #2E2620", borderRadius: 8, transition: "height .4s ease" }} />
                <div style={{ fontSize: 11, fontWeight: 800, color: "#9B7B5B" }}>{d.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* Unaided-solve gauge */}
        <section style={{ ...card, padding: 24, display: "flex", flexDirection: "column", alignItems: "center" }}>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 2px", alignSelf: "flex-start" }}>Unaided-Solve Rate</h2>
          <p style={{ margin: "0 0 14px", fontSize: 12, color: "#9B7B5B", fontWeight: 700, alignSelf: "flex-start" }}>Solved without opening a chest.</p>
          <div style={{ position: "relative", width: 190, height: 190, borderRadius: "50%", background: gaugeBackground(unaided), border: "4px solid #2E2620", display: "flex", alignItems: "center", justifyContent: "center", margin: "6px 0" }}>
            <div style={{ width: 120, height: 120, background: "#fff", border: "4px solid #2E2620", borderRadius: "50%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
              <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 38, lineHeight: 1, color: "#4C7A2F" }}>{unaided}%</div>
              <div style={{ fontSize: 10, fontWeight: 800, color: "#9B7B5B" }}>UNAIDED</div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 16, fontSize: 11, fontWeight: 800, marginTop: 6 }}>
            <span style={{ color: "#4C7A2F" }}>● Solo</span>
            <span style={{ color: "#B9A98C" }}>● With help</span>
          </div>
        </section>
      </div>

      {/* pattern coverage pegboard */}
      <section style={{ ...card, padding: 24 }}>
        <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 2px" }}>Pattern Coverage</h2>
        <p style={{ margin: "0 0 20px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>Pegboard heatmap — more pegs lit means stronger mastery.</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {coverage.map((c) => (
            <div key={c.zone_slug} style={{ display: "flex", alignItems: "center", gap: 18 }} className="acad-coverage-row">
              <div style={{ width: 150, flex: "none", fontFamily: FREDOKA, fontWeight: 600, fontSize: 14 }}>{c.pattern}</div>
              <div style={{ display: "flex", gap: 12, background: "#F3E7CC", border: "3px solid #2E2620", borderRadius: 14, padding: "9px 14px" }}>
                {[0, 1, 2, 3, 4].map((i) => {
                  const on = i < c.level;
                  return (
                    <span
                      key={i}
                      style={{
                        width: 26,
                        height: 26,
                        borderRadius: "50%",
                        border: "3px solid #2E2620",
                        background: on ? pegColor(c.level) : "#E4D6B8",
                        boxShadow: on ? "inset 0 -3px 0 rgba(46,38,32,.15)" : "none",
                      }}
                    />
                  );
                })}
              </div>
              <div style={{ fontSize: 12, fontWeight: 800, color: "#B0794A" }}>
                Lv {c.level} · {c.solved}/{c.total}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
