import { FREDOKA, ACHIEVEMENTS } from "../data";

export function Achievements() {
  const earned = ACHIEVEMENTS.filter((a) => a.earned).length;

  return (
    <div data-screen-label="Achievements" style={{ maxWidth: 1120, margin: "0 auto" }}>
      {/* merit sash banner */}
      <div style={{ position: "relative", background: "#EF5B54", border: "4px solid #2E2620", borderRadius: 24, padding: "22px 28px", marginBottom: 26, boxShadow: "0 8px 0 #A9302B", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: 0, bottom: 0, left: 0, width: 14, background: "repeating-linear-gradient(#F7C948 0 12px,#2E2620 12px 16px)" }} />
        <div style={{ position: "absolute", top: 0, bottom: 0, right: 0, width: 14, background: "repeating-linear-gradient(#F7C948 0 12px,#2E2620 12px 16px)" }} />
        <div style={{ display: "flex", alignItems: "center", gap: 18, padding: "0 20px" }}>
          <div style={{ width: 60, height: 60, flex: "none", background: "#F7C948", border: "4px solid #2E2620", borderRadius: "50%", boxShadow: "0 4px 0 #2E2620", position: "relative" }}>
            <span style={{ position: "absolute", inset: 12, border: "3px solid #2E2620", borderRadius: "50%" }} />
          </div>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, color: "#fff", margin: 0 }}>Bramble&apos;s Merit Sash</h1>
            <p style={{ margin: "2px 0 0", color: "#FFE3E1", fontWeight: 700, fontSize: 13 }}>Every badge is a toy you helped come to life.</p>
          </div>
          <div style={{ textAlign: "center", color: "#fff" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 34, lineHeight: 1 }}>
              {earned}
              <span style={{ fontSize: 18, color: "#FFD1CE" }}>/{ACHIEVEMENTS.length}</span>
            </div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#FFD1CE" }}>EARNED</div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(170px,1fr))", gap: 20 }}>
        {ACHIEVEMENTS.map((a) => (
          <div
            key={a.name}
            style={{
              position: "relative",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 9,
              padding: "18px 12px",
              borderRadius: 20,
              border: "4px solid #2E2620",
              textAlign: "center",
              background: a.earned ? "#fff" : "#EFE6D2",
              boxShadow: a.earned ? "0 7px 0 #E0CBA0" : "0 6px 0 #DCCBAA",
              opacity: a.earned ? 1 : 0.72,
              animation: a.earned ? "pop .4s ease both" : undefined,
            }}
          >
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: "50%",
                border: "4px solid #2E2620",
                position: "relative",
                background: a.earned ? a.color : "#C9BCA0",
                boxShadow: a.earned ? "0 4px 0 #2E2620" : "none",
                filter: a.earned ? "none" : "grayscale(1)",
              }}
            >
              <span style={{ position: "absolute", top: "50%", left: "50%", transform: "translate(-50%,-50%)", width: 26, height: 26, border: "3px solid rgba(46,38,32,.5)", borderRadius: 8 }} />
            </div>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, color: a.earned ? "#3A2E27" : "#8B7B63" }}>{a.name}</div>
            <div style={{ fontSize: 11, fontWeight: 700, color: a.earned ? "#9B7B5B" : "#A99A80" }}>{a.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
