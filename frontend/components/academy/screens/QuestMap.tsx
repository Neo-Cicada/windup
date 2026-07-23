import { FREDOKA, ZONES } from "../data";

type Props = { onOpenProblem: () => void };

export function QuestMap({ onOpenProblem }: Props) {
  return (
    <div data-screen-label="Quest Map" style={{ maxWidth: 1180, margin: "0 auto" }}>
      <div style={{ background: "#F3E7CC", border: "4px solid #2E2620", borderRadius: 24, padding: "18px 22px", marginBottom: 22, display: "flex", alignItems: "center", gap: 16, boxShadow: "0 8px 0 #E0CBA0" }}>
        <div style={{ width: 46, height: 46, flex: "none", background: "#4FB0E5", border: "3px solid #2E2620", borderRadius: 13, boxShadow: "0 4px 0 #2E2620" }} />
        <div>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 24, margin: 0 }}>Explore the Playroom</h1>
          <p style={{ margin: "2px 0 0", fontSize: 13, color: "#8B7358", fontWeight: 700 }}>Every corner is a coding pattern. Pick a toy and start fixing.</p>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(340px,1fr))", gap: 22 }}>
        {ZONES.map((z) => {
          const pct = Math.round((z.done / z.total) * 100);
          return (
            <button
              key={z.name}
              className="tap"
              onClick={onOpenProblem}
              style={{ textAlign: "left", background: "#fff", border: "4px solid #2E2620", borderRadius: 24, padding: 20, boxShadow: "0 8px 0 #E0CBA0", display: "flex", flexDirection: "column", gap: 14 }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
                <span style={{ width: 52, height: 52, flex: "none", borderRadius: 15, border: "4px solid #2E2620", background: z.color, boxShadow: "0 5px 0 #2E2620" }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 20 }}>{z.name}</div>
                  <div style={{ fontSize: 12, fontWeight: 800, color: "#9B7B5B", letterSpacing: ".5px" }}>{z.pattern}</div>
                </div>
                <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 22, color: "#B0794A" }}>{pct}%</div>
              </div>
              <p style={{ margin: 0, fontSize: 13, color: "#8B7358", fontWeight: 700 }}>{z.blurb}</p>
              <div>
                <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontWeight: 800, color: "#B0794A", marginBottom: 5 }}>
                  <span>PROGRESS</span>
                  <span>{z.done}/{z.total}</span>
                </div>
                <div style={{ height: 14, background: "#EFE1C2", border: "3px solid #2E2620", borderRadius: 9, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${pct}%`, background: z.color }} />
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
