import { FREDOKA, difficultyTone } from "../data";
import { Winding } from "../../ScreenState";
import type { Problem, Zone } from "@/lib/types";

type Props = {
  zones: Zone[];
  /** Slug of the opened corner, or null when the map is collapsed. */
  openZone: string | null;
  problems: Problem[];
  problemsLoading: boolean;
  problemsError: string | null;
  onSelectZone: (slug: string) => void;
  onOpenProblem: (slug: string) => void;
};

export function QuestMap({ zones, openZone, problems, problemsLoading, problemsError, onSelectZone, onOpenProblem }: Props) {
  const zone = zones.find((z) => z.slug === openZone) ?? null;

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
        {zones.map((z) => {
          const pct = z.total > 0 ? Math.round((z.done / z.total) * 100) : 0;
          const open = z.slug === openZone;
          return (
            <button
              key={z.slug}
              className="tap"
              onClick={() => onSelectZone(z.slug)}
              style={{
                textAlign: "left",
                background: "#fff",
                border: "4px solid #2E2620",
                borderRadius: 24,
                padding: 20,
                boxShadow: open ? "0 8px 0 #C9A96A" : "0 8px 0 #E0CBA0",
                outline: open ? `3px solid ${z.color}` : "none",
                outlineOffset: open ? 3 : 0,
                display: "flex",
                flexDirection: "column",
                gap: 14,
              }}
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

      {/* the picked corner's shelf of toys */}
      {zone && (
        <section style={{ marginTop: 26, background: "#fff", border: "4px solid #2E2620", borderRadius: 24, padding: 24, boxShadow: "0 8px 0 #E0CBA0", animation: "pop .35s ease both" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 13, marginBottom: 4 }}>
            <span style={{ width: 30, height: 30, flex: "none", borderRadius: 10, border: "3px solid #2E2620", background: zone.color }} />
            <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 21, margin: 0 }}>{zone.name}</h2>
            <span style={{ fontSize: 12, fontWeight: 800, color: "#9B7B5B" }}>{zone.pattern}</span>
          </div>
          <p style={{ margin: "0 0 18px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>
            {zone.done} of {zone.total} toys back in working order.
          </p>

          {problemsLoading && <Winding label="Opening the toy box…" />}
          {problemsError && (
            <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#B4342D" }}>{problemsError}</p>
          )}

          {!problemsLoading && !problemsError && (
            <div style={{ display: "flex", flexDirection: "column", gap: 11 }}>
              {problems.length === 0 && (
                <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#9B7B5B" }}>
                  This corner is still being unpacked — no toys on the shelf yet.
                </p>
              )}
              {problems.map((p) => {
                const tone = difficultyTone(p.difficulty);
                return (
                  <div key={p.slug} style={{ display: "flex", alignItems: "center", gap: 14, background: "#FCF6E9", border: "3px solid #2E2620", borderRadius: 18, padding: "12px 15px" }}>
                    <span
                      style={{ width: 30, height: 30, flex: "none", borderRadius: 10, border: "3px solid #2E2620", background: p.solved ? "#6FBF73" : "#EFE1C2", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: "#173d19" }}
                      title={p.solved ? "Fixed" : "Still broken"}
                    >
                      {p.solved ? "✓" : ""}
                    </span>
                    <div style={{ flex: 1, minWidth: 0, fontFamily: FREDOKA, fontWeight: 600, fontSize: 16 }}>{p.title}</div>
                    <span style={{ background: tone.bg, border: `2px solid ${tone.border}`, color: tone.color, fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20, textTransform: "capitalize" }}>
                      {p.difficulty}
                    </span>
                    <span style={{ fontSize: 12, fontWeight: 800, color: "#B0794A", width: 74, textAlign: "right" }}>+{p.xp_reward} charge</span>
                    <button className="tap" onClick={() => onOpenProblem(p.slug)} style={{ border: "3px solid #2E2620", borderRadius: 13, background: "#6FBF73", color: "#173d19", fontWeight: 700, fontSize: 13, padding: "8px 15px", boxShadow: "0 4px 0 #2E2620", fontFamily: FREDOKA }}>
                      {p.solved ? "Replay" : "Fix it"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </section>
      )}
    </div>
  );
}
