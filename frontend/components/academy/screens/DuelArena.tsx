import Link from "next/link";
import { FREDOKA } from "../data";
import { FightClock } from "./FightClock";
import type { Duel, DuelPlayer } from "@/lib/types";

type Props = {
  duel: Duel;
  /** Ticked down locally between polls; the server owns the real clock. */
  timeFmt: string;
  pct: number;
  pending: boolean;
  error: string | null;
  onForfeit: () => void;
  onLeave: () => void;
};

export function DuelArena({ duel, timeFmt, pct, pending, error, onForfeit, onLeave }: Props) {
  const running = duel.status === "active";
  const over = !running;

  return (
    <div data-screen-label="Duel" style={{ maxWidth: 960, margin: "0 auto" }}>
      <div className="acad-boss" style={{ background: "#2E2620", border: "4px solid #2E2620", borderRadius: 28, padding: 34, boxShadow: "0 12px 0 #1c1712", position: "relative", overflow: "hidden", textAlign: "center" }}>
        <div style={{ position: "absolute", inset: 0, background: "radial-gradient(circle at 50% 30%,rgba(224,86,107,.35),transparent 60%)" }} />
        <div style={{ position: "relative" }}>
          <div style={{ display: "inline-block", background: "#E0566B", border: "3px solid #F7C948", color: "#fff", fontFamily: FREDOKA, fontWeight: 700, fontSize: 13, letterSpacing: 2, padding: "6px 16px", borderRadius: 20, marginBottom: 20 }}>
            ⚔️ DUEL · CODE {duel.code} ⚔️
          </div>

          {/* Two toys, one clock between them — the whole point of the screen. */}
          <div className="acad-duel" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 26, flexWrap: "wrap", marginBottom: 22 }}>
            <Corner player={duel.you} total={duel.rounds_total} mine />
            <FightClock timeFmt={timeFmt} pct={pct} running={running} />
            <Corner player={duel.them} total={duel.rounds_total} mine={false} />
          </div>

          {/* One column per round, your chip above theirs. Watching the other row fill
              in is the game, so the two sides have to be readable at a glance. */}
          <div className="acad-duel-chips" style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
            {duel.rounds.map((round) => (
              <div key={round.ordinal} style={{ display: "flex", flexDirection: "column", gap: 6, minWidth: 132 }}>
                <Link
                  href={`/academy/problem/${round.slug}`}
                  className="tap"
                  style={{ textDecoration: "none", display: "block", background: "rgba(251,244,228,.14)", border: `3px solid ${round.you_solved ? "#6FBF73" : "#F7C948"}`, borderRadius: 14, padding: "10px 12px", color: "#fff" }}
                >
                  <div style={{ fontSize: 10, fontWeight: 800, color: round.color, letterSpacing: 1 }}>
                    ROUND {round.ordinal}
                  </div>
                  <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, lineHeight: 1.2 }}>
                    {round.title}
                  </div>
                  <div style={{ fontSize: 10, fontWeight: 800, color: round.you_solved ? "#8FD08F" : "#F7C948" }}>
                    {round.you_solved ? "✓ you fixed it" : "your turn"}
                  </div>
                </Link>
                <div style={{ border: `3px solid ${round.they_solved ? "#E0566B" : "#6B5A4A"}`, borderRadius: 12, padding: "5px 10px", fontSize: 10, fontWeight: 800, color: round.they_solved ? "#F3A0AE" : "#8E7E68" }}>
                  {round.they_solved ? "✓ they fixed it" : "they haven't"}
                </div>
              </div>
            ))}
          </div>

          {over && duel.outcome_label && (
            <div style={{ margin: "22px auto 0", maxWidth: 520, background: duel.winner === "you" ? "#EAF7D9" : "#FBF4E4", border: "3px solid #2E2620", borderRadius: 14, padding: "12px 16px", fontFamily: FREDOKA, fontWeight: 700, fontSize: 16, color: duel.winner === "you" ? "#4C7A2F" : "#7A6A57" }}>
              {duel.outcome_label}
              {duel.you.xp_awarded > 0 && ` +${duel.you.xp_awarded} charge.`}
            </div>
          )}

          <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap", marginTop: 24 }}>
            {running ? (
              <button
                className="tap"
                onClick={onForfeit}
                disabled={pending}
                style={{ border: "4px solid #6B5A4A", borderRadius: 18, background: "transparent", color: "#D6C7B4", fontWeight: 700, fontSize: 16, padding: "13px 24px", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
              >
                {pending ? "Winding…" : "Run away"}
              </button>
            ) : (
              <button
                className="tap"
                onClick={onLeave}
                disabled={pending}
                style={{ border: "4px solid #F7C948", borderRadius: 18, background: "#E0566B", color: "#fff", fontWeight: 700, fontSize: 17, padding: "13px 30px", boxShadow: "0 5px 0 #A93a4b", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
              >
                Duel again
              </button>
            )}
          </div>

          {error && (
            <div role="alert" style={{ margin: "20px auto 0", maxWidth: 520, background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#B4342D" }}>
              {error}
            </div>
          )}

          <p style={{ margin: "22px auto 0", maxWidth: 560, color: "#B9A98C", fontSize: 12, fontWeight: 700, lineHeight: 1.5 }}>
            Tap a round to open the workbench. Solving it there clears it here — for a duel
            it counts even if you&apos;ve fixed that toy before.
          </p>
        </div>
      </div>
    </div>
  );
}

function Corner({
  player,
  total,
  mine,
}: {
  player: DuelPlayer | null;
  total: number;
  mine: boolean;
}) {
  if (player === null) {
    return (
      <div className="acad-duel-side" style={{ minWidth: 132, color: "#8E7E68", fontWeight: 800, fontSize: 12 }}>
        waiting…
      </div>
    );
  }
  return (
    <div className="acad-duel-side" style={{ minWidth: 132, textAlign: "center" }}>
      <div style={{ width: 54, height: 54, margin: "0 auto 8px", borderRadius: 16, background: player.avatar_body, border: `4px solid ${player.avatar_head}`, boxShadow: "0 4px 0 rgba(0,0,0,.35)" }} />
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15, color: "#fff" }}>
        {mine ? "You" : player.toy_name}
      </div>
      <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, color: mine ? "#8FD08F" : "#F3A0AE", lineHeight: 1.1 }}>
        {player.rounds_cleared}
        <span style={{ fontSize: 14, color: "#B9A98C" }}>/{total}</span>
      </div>
      {player.forfeited && (
        <div style={{ fontSize: 10, fontWeight: 800, color: "#B9A98C" }}>ran away</div>
      )}
    </div>
  );
}
