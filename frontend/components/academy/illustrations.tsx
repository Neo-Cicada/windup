import type { CSSProperties } from "react";

const abs = (s: CSSProperties): CSSProperties => ({ position: "absolute", ...s });

type BuddyProps = { body: string; head: string; accent: string };

/** The trainee toy "block buddy" — customizable body/head/accent colors. */
export function BuddyAvatar({ body, head, accent }: BuddyProps) {
  return (
    <div style={{ position: "relative", width: 140, height: 158, flex: "none", animation: "floaty 4s ease-in-out infinite" }}>
      <div style={abs({ bottom: -4, left: "50%", transform: "translateX(-50%)", width: 104, height: 16, background: "rgba(46,38,32,.16)", borderRadius: "50%" })} />
      <div style={abs({ bottom: 8, left: "50%", transform: "translateX(-50%)", width: 104, height: 74, background: body, border: "4px solid #2E2620", borderRadius: 22 })} />
      <div style={abs({ bottom: 22, left: "50%", transform: "translateX(-50%)", width: 48, height: 46, background: "#EAF7D9", border: "4px solid #2E2620", borderRadius: 13 })} />
      <div style={abs({ top: 8, left: "50%", transform: "translateX(-50%)", width: 92, height: 84, background: head, border: "4px solid #2E2620", borderRadius: 28 })} />
      <div style={abs({ top: 0, left: 24, width: 22, height: 22, background: accent, border: "4px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 0, right: 24, width: 22, height: 22, background: accent, border: "4px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 38, left: 34, width: 13, height: 13, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 38, right: 34, width: 13, height: 13, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 40, left: 37, width: 4, height: 4, background: "#fff", borderRadius: "50%" })} />
      <div style={abs({ top: 40, right: 47, width: 4, height: 4, background: "#fff", borderRadius: "50%" })} />
      <div style={abs({ top: 54, left: 26, width: 14, height: 9, background: "#F4A0A0", borderRadius: "50%", opacity: 0.85 })} />
      <div style={abs({ top: 54, right: 26, width: 14, height: 9, background: "#F4A0A0", borderRadius: "50%", opacity: 0.85 })} />
      <div style={abs({ top: 56, left: "50%", transform: "translateX(-50%)", width: 26, height: 13, border: "3px solid #2E2620", borderTop: 0, borderRadius: "0 0 14px 14px" })} />
    </div>
  );
}

/** Sprocket the blue wind-up robot coach, with a spinning key. */
export function SprocketBot() {
  return (
    <div style={{ position: "relative", width: 96, height: 118, animation: "floaty 3.4s ease-in-out infinite" }}>
      <div style={abs({ bottom: -2, left: "50%", transform: "translateX(-50%)", width: 78, height: 12, background: "rgba(46,38,32,.16)", borderRadius: "50%" })} />
      <div style={abs({ top: 2, left: "50%", transform: "translateX(-50%)", width: 9, height: 16, background: "#B0794A", border: "2px solid #2E2620" })} />
      <div style={abs({ top: -4, left: "50%", transform: "translateX(-50%)", width: 12, height: 12, background: "#EF5B54", border: "2px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 14, left: "50%", transform: "translateX(-50%)", width: 70, height: 56, background: "#9FCFEC", border: "3px solid #2E2620", borderRadius: 16 })} />
      <div style={abs({ top: 28, left: 20, width: 16, height: 16, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 28, right: 20, width: 16, height: 16, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 33, left: 26, width: 6, height: 6, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 33, right: 26, width: 6, height: 6, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 52, left: "50%", transform: "translateX(-50%)", width: 22, height: 6, background: "#2E2620", borderRadius: 3 })} />
      <div style={abs({ bottom: 6, left: "50%", transform: "translateX(-50%)", width: 56, height: 44, background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 12 })} />
      <div style={abs({ bottom: 16, left: "50%", transform: "translateX(-50%)", width: 22, height: 22, background: "#F7C948", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ bottom: 20, right: -8, width: 20, height: 20, border: "3px solid #2E2620", borderRadius: "50%", animation: "spin 3s linear infinite", background: "#C9A96A" })}>
        <div style={abs({ top: "50%", left: "50%", width: 20, height: 4, background: "#2E2620", transform: "translate(-50%,-50%)", borderRadius: 2 })} />
      </div>
    </div>
  );
}

/** The Jack-in-the-Box boss toy that wobbles atop its crate. */
export function JackBoss() {
  return (
    <div style={{ position: "relative", width: 180, height: 200, animation: "wob 2s ease-in-out infinite" }}>
      <div style={abs({ bottom: 0, left: "50%", transform: "translateX(-50%)", width: 150, height: 120, background: "#8B6FD6", border: "5px solid #F7C948", borderRadius: 16 })} />
      <div style={abs({ bottom: 40, left: "50%", transform: "translateX(-50%)", width: 100, height: 40, background: "#F7C948", border: "4px solid #2E2620", borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center", gap: 14 })}>
        <span style={{ width: 10, height: 14, background: "#2E2620", borderRadius: 3, transform: "rotate(20deg)" }} />
        <span style={{ width: 10, height: 14, background: "#2E2620", borderRadius: 3, transform: "rotate(-20deg)" }} />
      </div>
      <div style={abs({ top: 8, left: "50%", transform: "translateX(-50%)", width: 78, height: 78, background: "#EF5B54", border: "5px solid #2E2620", borderRadius: 22 })} />
      <div style={abs({ top: 30, left: "50%", transform: "translateX(-50%)", width: 44, height: 16, display: "flex", justifyContent: "space-between" })}>
        <span style={{ width: 16, height: 16, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" }} />
        <span style={{ width: 16, height: 16, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" }} />
      </div>
      <div style={abs({ top: 52, left: "50%", transform: "translateX(-50%)", width: 34, height: 10, background: "#2E2620", borderRadius: "0 0 8px 8px" })} />
    </div>
  );
}
