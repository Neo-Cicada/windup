"use client";

import { Winding } from "@/components/ScreenState";
import { BossBattle } from "@/components/academy/screens/BossBattle";
import { useAcademy } from "@/components/academy/AcademyProvider";
import { fmtTime } from "@/components/academy/data";

export function BossRoute() {
  const { boss } = useAcademy();

  if (!boss.ready) return <Winding label="Waking the boss…" />;

  return (
    <BossBattle
      session={boss.session}
      timeFmt={fmtTime(boss.remaining)}
      pct={
        boss.session === null
          ? 100
          : Math.round((boss.remaining / boss.session.total_seconds) * 100)
      }
      running={boss.session?.status === "running"}
      label={boss.label}
      pending={boss.pending}
      error={boss.error}
      onToggle={boss.toggle}
      onComplete={boss.complete}
      onAbandon={boss.abandon}
    />
  );
}
