import { FREDOKA, buildShelves } from "../data";
import { BuddyAvatar, SprocketBot } from "../illustrations";
import type { DailyQuest } from "@/lib/types";

type Props = {
  toyName: string;
  traineeNo: string;
  avBody: string;
  avHead: string;
  avAccent: string;
  ready: number;
  level: number;
  solved: number;
  unaidedRate: number;
  badgesLabel: string;
  rank: number | null;
  sprocketMessage: string;
  quests: DailyQuest[];
  questsDone: number;
  onOpenProblem: (slug: string) => void;
};

const card = {
  background: "#fff",
  border: "4px solid #2E2620",
  borderRadius: 24,
  boxShadow: "0 8px 0 #E0CBA0",
} as const;

export function Dashboard({ toyName, traineeNo, avBody, avHead, avAccent, ready, level, solved, unaidedRate, badgesLabel, rank, sprocketMessage, quests, questsDone, onOpenProblem }: Props) {
  const shelves = buildShelves(level);

  return (
    <div data-screen-label="Dashboard" style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: 22, maxWidth: 1180, margin: "0 auto" }} className="acad-dash">
      {/* HERO */}
      <section
        style={{
          gridColumn: "1 / -1",
          display: "flex",
          gap: 26,
          alignItems: "center",
          background: "#fff",
          border: "4px solid #2E2620",
          borderRadius: 28,
          padding: "26px 30px",
          boxShadow: "0 10px 0 #E0CBA0,0 18px 30px rgba(46,38,32,.14)",
          position: "relative",
          overflow: "hidden",
        }}
        className="acad-hero"
      >
        <div style={{ position: "absolute", right: -40, top: -40, width: 180, height: 180, background: "#FDF0CE", borderRadius: "50%", opacity: 0.7 }} />
        <BuddyAvatar body={avBody} head={avHead} accent={avAccent} />

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "inline-block", background: "#FDECEC", border: "2px solid #EF5B54", color: "#D8443D", fontWeight: 800, fontSize: 11, padding: "4px 11px", borderRadius: 20, marginBottom: 9 }}>
            TRAINEE TOY · No. {traineeNo}
          </div>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 30, margin: "0 0 4px" }}>Welcome back, {toyName}!</h1>
          <p style={{ margin: "0 0 16px", color: "#6B5A4A", fontSize: 14.5, maxWidth: 460 }}>{sprocketMessage}</p>
          <div style={{ maxWidth: 460 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, fontWeight: 800, color: "#B0794A", marginBottom: 5 }}>
              <span>INTERVIEW READY</span>
              <span>{ready}%</span>
            </div>
            <div style={{ height: 18, background: "#EFE1C2", border: "3px solid #2E2620", borderRadius: 11, overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${ready}%`, background: "repeating-linear-gradient(45deg,#EF5B54 0 10px,#E2504A 10px 20px)", transition: "width .4s ease" }} />
            </div>
          </div>
        </div>

        {/* sprocket bubble */}
        <div className="acad-hero-side" style={{ flex: "none", width: 170, alignSelf: "stretch", display: "flex", flexDirection: "column", justifyContent: "center", gap: 12 }}>
          <div style={{ position: "relative", background: "#EAF6FD", border: "3px solid #2E2620", borderRadius: 16, padding: "11px 13px", fontSize: 12.5, fontWeight: 700, color: "#2C6E9C", lineHeight: 1.35 }}>
            Keep winding — Lv&nbsp;{level + 1} is one shelf away.
            <div style={{ position: "absolute", bottom: -11, left: 26, width: 14, height: 14, background: "#EAF6FD", borderRight: "3px solid #2E2620", borderBottom: "3px solid #2E2620", transform: "rotate(45deg)" }} />
          </div>
          <div style={{ display: "flex", justifyContent: "center" }}>
            <SprocketBot />
          </div>
        </div>
      </section>

      {/* TODAY'S QUESTS */}
      <section style={{ ...card, padding: "22px 24px" }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 21, margin: 0 }}>Today&apos;s Quests</h2>
          <span style={{ fontSize: 12, fontWeight: 800, color: "#B0794A" }}>{questsDone} / {quests.length} done</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 13 }}>
          {quests.length === 0 && (
            <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: "#9B7B5B" }}>
              No quests on the board yet — Sprocket rolls a fresh set each morning.
            </p>
          )}
          {quests.map((q) => (
            <div key={q.id} style={{ display: "flex", alignItems: "center", gap: 15, background: "#FCF6E9", border: "3px solid #2E2620", borderRadius: 18, padding: "12px 14px" }}>
              <span style={{ width: 34, height: 34, flex: "none", borderRadius: 11, border: "3px solid #2E2620", background: q.color }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                  <span style={{ fontFamily: FREDOKA, fontWeight: 600, fontSize: 15.5 }}>{q.name}</span>
                  <span style={{ fontSize: 11, fontWeight: 800, color: "#9B7B5B" }}>{q.zone}</span>
                </div>
                <div style={{ marginTop: 6, height: 11, background: "#EFE1C2", border: "2px solid #2E2620", borderRadius: 7, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: `${q.pct}%`, background: q.color, transition: "width .35s ease" }} />
                </div>
              </div>
              <div style={{ fontSize: 12, fontWeight: 800, color: "#B0794A", width: 34, textAlign: "right" }}>{q.pct}%</div>
              <button className="tap" onClick={() => onOpenProblem(q.slug)} style={{ border: "3px solid #2E2620", borderRadius: 13, background: q.completed ? "#D9C4A0" : "#6FBF73", color: q.completed ? "#5C4A3C" : "#173d19", fontWeight: 700, fontSize: 13, padding: "8px 15px", boxShadow: "0 4px 0 #2E2620", fontFamily: FREDOKA }}>
                {q.completed ? "Replay" : "Play"}
              </button>
            </div>
          ))}
        </div>
      </section>

      {/* RIGHT COLUMN */}
      <section style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        {/* climbing shelves */}
        <div style={{ ...card, padding: "20px 22px" }}>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 4px" }}>The Climbing Shelves</h2>
          <p style={{ margin: "0 0 16px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>Reach the top shelf to graduate.</p>
          <div style={{ position: "relative", height: 196 }}>
            {shelves.map((s) => (
              <div key={s.label} style={{ position: "absolute", left: 0, right: 0, top: s.top, height: 48 }}>
                <span style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 12, borderRadius: 6, background: "repeating-linear-gradient(90deg,#C9A96A 0 14px,#BE9C5C 14px 16px)", border: "3px solid #2E2620" }} />
                <span style={{ position: "absolute", left: 12, bottom: 17, fontSize: 10, fontWeight: 800, color: "#B0794A", letterSpacing: 1 }}>{s.label}</span>
                {s.here && (
                  <span style={{ position: "absolute", right: 16, bottom: 8, width: 30, height: 34, background: "#F7C948", border: "3px solid #2E2620", borderRadius: "11px 11px 9px 9px", animation: "floaty 3s ease-in-out infinite" }}>
                    <span style={{ position: "absolute", top: 9, left: 6, width: 5, height: 5, background: "#2E2620", borderRadius: "50%" }} />
                    <span style={{ position: "absolute", top: 9, right: 6, width: 5, height: 5, background: "#2E2620", borderRadius: "50%" }} />
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* quick stats */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
          <div style={{ background: "#EAF6FD", border: "3px solid #2E2620", borderRadius: 18, padding: 15, boxShadow: "0 5px 0 #C9DEEC" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26 }}>{solved}</div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#2C6E9C" }}>TOYS FIXED</div>
          </div>
          <div style={{ background: "#EAF7D9", border: "3px solid #2E2620", borderRadius: 18, padding: 15, boxShadow: "0 5px 0 #CFE4B6" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26 }}>{unaidedRate}%</div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#4C7A2F" }}>SOLVED UNAIDED</div>
          </div>
          <div style={{ background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 18, padding: 15, boxShadow: "0 5px 0 #EFCFCF" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26 }}>{badgesLabel}</div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#D8443D" }}>MERIT BADGES</div>
          </div>
          <div style={{ background: "#FDF3D6", border: "3px solid #2E2620", borderRadius: 18, padding: 15, boxShadow: "0 5px 0 #EBD9A6" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26 }}>{rank === null ? "—" : `#${rank}`}</div>
            <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A" }}>SHELF OF FAME</div>
          </div>
        </div>
      </section>
    </div>
  );
}
