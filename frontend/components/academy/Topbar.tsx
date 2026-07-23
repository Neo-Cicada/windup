import { FREDOKA } from "./data";

type Props = {
  title: string;
  level: number;
  levelName: string;
  xp: number;
  xpMax: number;
  xpPct: number;
  streak: number;
  coins: number;
  streakCells: string[];
  onWind: () => void;
};

const pill = {
  display: "flex",
  alignItems: "center",
  background: "#fff",
  border: "3px solid #2E2620",
  borderRadius: 16,
  boxShadow: "0 4px 0 #E0CBA0",
} as const;

export function Topbar({ title, level, levelName, xp, xpMax, xpPct, streak, coins, streakCells, onWind }: Props) {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 40,
        display: "flex",
        alignItems: "center",
        gap: 16,
        flexWrap: "wrap",
        padding: "14px 26px",
        background: "#FCF6E9",
        borderBottom: "4px solid #2E2620",
      }}
    >
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 20, flex: "none" }}>{title}</div>
      <div style={{ flex: 1 }} />

      {/* level shelves mini */}
      <div style={{ ...pill, gap: 9, padding: "6px 12px" }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <div style={{ width: 20, height: 4, borderRadius: 3, background: "#C9A96A" }} />
          <div style={{ width: 20, height: 4, borderRadius: 3, background: "#C9A96A" }} />
          <div style={{ width: 20, height: 4, borderRadius: 3, background: "#EF5B54" }} />
        </div>
        <div style={{ lineHeight: 1.05 }}>
          <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>Lv {level}</div>
          <div style={{ fontSize: 9.5, fontWeight: 800, color: "#B0794A", whiteSpace: "nowrap" }}>{levelName}</div>
        </div>
      </div>

      {/* wind-up charge meter */}
      <div style={{ ...pill, gap: 10, padding: "6px 14px 6px 8px" }}>
        <div style={{ width: 26, height: 26, flex: "none", border: "3px solid #2E2620", borderRadius: "50%", position: "relative", animation: "spin 6s linear infinite", background: "#F7C948" }}>
          <div style={{ position: "absolute", top: -4, left: "50%", width: 6, height: 11, transform: "translateX(-50%)", background: "#EF5B54", border: "2px solid #2E2620", borderRadius: 3 }} />
          <div style={{ position: "absolute", bottom: -4, left: "50%", width: 6, height: 11, transform: "translateX(-50%)", background: "#EF5B54", border: "2px solid #2E2620", borderRadius: 3 }} />
        </div>
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, fontSize: 10, fontWeight: 800, color: "#B0794A", marginBottom: 3 }}>
            <span>CHARGE</span>
            <span>{xp}/{xpMax}</span>
          </div>
          <div style={{ width: 150, height: 13, background: "#EFE1C2", border: "2px solid #2E2620", borderRadius: 8, overflow: "hidden" }}>
            <div style={{ height: "100%", width: `${xpPct}%`, background: "repeating-linear-gradient(45deg,#6FBF73 0 8px,#63AF67 8px 16px)", borderRight: "2px solid #2E2620" }} />
          </div>
        </div>
      </div>

      {/* streak spinning top */}
      <div style={{ ...pill, gap: 11, padding: "6px 13px 6px 11px" }}>
        <div style={{ display: "grid", gridAutoFlow: "column", gridTemplateRows: "repeat(3,1fr)", gap: 3 }}>
          {streakCells.map((c, i) => (
            <span key={i} style={{ width: 9, height: 9, borderRadius: 2, background: c }} />
          ))}
        </div>
        <div style={{ lineHeight: 1.05 }}>
          <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>{streak}🔥</div>
          <div style={{ fontSize: 9.5, fontWeight: 800, color: "#B0794A" }}>DAY STREAK</div>
        </div>
      </div>

      {/* coins */}
      <div style={{ ...pill, gap: 7, padding: "7px 13px" }}>
        <div style={{ width: 20, height: 20, background: "#F7C948", border: "3px solid #2E2620", borderRadius: "50%" }} />
        <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15 }}>{coins}</span>
      </div>

      <button
        className="tap"
        onClick={onWind}
        style={{ border: "3px solid #2E2620", borderRadius: 15, background: "#EF5B54", color: "#fff", fontWeight: 600, fontSize: 13.5, padding: "9px 15px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA }}
      >
        Wind up +40
      </button>
    </header>
  );
}
