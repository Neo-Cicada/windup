"use client";

import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { errorMessage, post } from "@/lib/api";
import { useResource, type Resource } from "@/lib/useResource";
import type { DashboardData, StreakSummary } from "@/lib/types";
import { useBossFight, type BossFight } from "./useBossFight";

type AcademyValue = {
  /** The toy's charge, level and today's quests — read by the topbar on every screen. */
  dashboard: Resource<DashboardData>;
  streak: Resource<StreakSummary>;
  boss: BossFight;
  confetti: ConfettiPiece[];
  burst: (n: number) => void;
  /** Give Sprocket a new line. */
  say: (message: string) => void;
  sprocketMsg: string;
  winding: boolean;
  windUp: () => Promise<void>;
};

const AcademyContext = createContext<AcademyValue | null>(null);

/**
 * Everything the academy shares across screens.
 *
 * It lives in the layout, which doesn't unmount as you move between routes — so a leaf
 * calling `dashboard.reload()` after a solve still moves the topbar, a verdict that lands
 * after you've wandered off still throws its confetti, and a running boss fight is still
 * known to the problem route.
 */
export function AcademyProvider({ children }: { children: ReactNode }) {
  const dashboard = useResource<DashboardData>("/dashboard");
  const streak = useResource<StreakSummary>("/analytics/streak");

  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  // Sprocket's line: the last thing that actually happened, falling back to the server's.
  const [sprocketSaid, setSprocketSaid] = useState<string | null>(null);
  const [winding, setWinding] = useState(false);

  const confettiTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (confettiTimer.current) clearTimeout(confettiTimer.current);
    };
  }, []);

  function burst(n: number) {
    if (n <= 0) return;
    setConfetti(makeBurst(n));
    if (confettiTimer.current) clearTimeout(confettiTimer.current);
    confettiTimer.current = setTimeout(() => setConfetti([]), 2400);
  }

  function say(message: string) {
    setSprocketSaid(message);
  }

  const boss = useBossFight({
    say,
    onWin: (session) => {
      say(`Boss down! +${session.xp_awarded} charge for beating the clock.`);
      burst(80);
      dashboard.reload();
      streak.reload();
    },
  });

  async function windUp() {
    setWinding(true);
    try {
      const next = await post<DashboardData>("/me/wind-up");
      dashboard.set(next);
      streak.reload();
      say("Wound up tight — that's +40 charge on the meter!");
      burst(24);
    } catch (err) {
      say(errorMessage(err));
    } finally {
      setWinding(false);
    }
  }

  const value: AcademyValue = {
    dashboard,
    streak,
    boss,
    confetti,
    burst,
    say,
    sprocketMsg: sprocketSaid ?? dashboard.data?.sprocket_message ?? "Sprocket is oiling the gears…",
    winding,
    windUp,
  };

  return <AcademyContext.Provider value={value}>{children}</AcademyContext.Provider>;
}

export function useAcademy(): AcademyValue {
  const ctx = useContext(AcademyContext);
  if (ctx === null) throw new Error("useAcademy must be used inside <AcademyProvider>");
  return ctx;
}
