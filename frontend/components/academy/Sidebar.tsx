import type { CSSProperties } from "react";
import { NAV, FREDOKA, type ScreenKey } from "./data";

type Props = {
  active: ScreenKey;
  onNavigate: (key: ScreenKey) => void;
  sprocketMsg: string;
};

export function Sidebar({ active, onNavigate, sprocketMsg }: Props) {
  return (
    <aside
      style={{
        width: 246,
        flex: "none",
        position: "sticky",
        top: 0,
        alignSelf: "flex-start",
        height: "100vh",
        background: "#FBF4E4",
        borderRight: "4px solid #2E2620",
        display: "flex",
        flexDirection: "column",
        padding: "22px 16px",
        gap: 6,
        boxShadow: "6px 0 0 rgba(46,38,32,.06)",
      }}
    >
      {/* brand */}
      <div style={{ display: "flex", alignItems: "center", gap: 11, padding: "2px 6px 18px" }}>
        <div style={{ width: 44, height: 44, flex: "none", background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 13, position: "relative", boxShadow: "0 4px 0 #2E2620" }}>
          <div style={{ position: "absolute", inset: 8, border: "3px solid #FBE7C6", borderRadius: 7 }} />
          <div style={{ position: "absolute", top: "50%", left: "50%", width: 10, height: 10, transform: "translate(-50%,-50%)", background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" }} />
        </div>
        <div style={{ lineHeight: 1 }}>
          <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 16, letterSpacing: ".3px" }}>WINDUP</div>
          <div style={{ fontFamily: FREDOKA, fontWeight: 500, fontSize: 11, letterSpacing: 3, color: "#B0794A" }}>ACADEMY</div>
        </div>
      </div>

      {/* nav */}
      {NAV.map((n) => {
        const isActive = n.key === active;
        const btnStyle: CSSProperties = {
          display: "flex",
          alignItems: "center",
          gap: 11,
          width: "100%",
          textAlign: "left",
          padding: "9px 11px",
          borderRadius: 14,
          cursor: "pointer",
          transition: ".12s",
          background: isActive ? "#FDECEC" : "transparent",
          border: isActive ? "3px solid #2E2620" : "3px solid transparent",
          boxShadow: isActive ? "0 4px 0 #2E2620" : "none",
        };
        return (
          <button key={n.key} className="tap" onClick={() => onNavigate(n.key)} style={btnStyle}>
            <span style={{ width: 24, height: 24, flex: "none", borderRadius: 8, border: "3px solid #2E2620", background: n.color, opacity: isActive ? 1 : 0.9 }} />
            <span style={{ display: "flex", flexDirection: "column", alignItems: "flex-start", lineHeight: 1.15 }}>
              <span style={{ fontFamily: FREDOKA, fontWeight: 600, fontSize: 14.5 }}>{n.label}</span>
              <span style={{ fontSize: 10.5, color: "#9B7B5B", fontWeight: 700 }}>{n.sub}</span>
            </span>
          </button>
        );
      })}

      {/* sprocket says */}
      <div style={{ marginTop: "auto", background: "#F2E6CC", border: "3px dashed #C9A96A", borderRadius: 16, padding: "12px 13px" }}>
        <div style={{ fontFamily: FREDOKA, fontWeight: 600, fontSize: 12, color: "#B0794A", marginBottom: 6 }}>SPROCKET SAYS</div>
        <div style={{ fontSize: 12, lineHeight: 1.4, color: "#5C4A3C" }}>{sprocketMsg}</div>
      </div>
    </aside>
  );
}
