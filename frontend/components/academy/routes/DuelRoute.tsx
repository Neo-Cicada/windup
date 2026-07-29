"use client";

import { Winding } from "@/components/ScreenState";
import { DuelArena } from "@/components/academy/screens/DuelArena";
import { DuelLobby } from "@/components/academy/screens/DuelLobby";
import { useAcademy } from "@/components/academy/AcademyProvider";
import { fmtTime } from "@/components/academy/data";

export function DuelRoute() {
  const { duel } = useAcademy();

  if (!duel.ready) return <Winding label="Looking for a challenger…" />;

  const current = duel.duel;

  // A finished duel still shows its arena — the result is the point of the screen —
  // until the toy asks for another, which drops them back to the lobby.
  if (current !== null && current.status !== "waiting") {
    return (
      <DuelArena
        duel={current}
        timeFmt={fmtTime(duel.remaining)}
        pct={
          current.total_seconds === 0
            ? 0
            : Math.round((duel.remaining / current.total_seconds) * 100)
        }
        pending={duel.pending}
        error={duel.error}
        onForfeit={duel.forfeit}
        onLeave={duel.create}
      />
    );
  }

  return (
    <DuelLobby
      waiting={current}
      pending={duel.pending}
      error={duel.error}
      onCreate={duel.create}
      onJoin={duel.join}
      onCancel={duel.cancel}
    />
  );
}
