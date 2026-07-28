"use client";

import type { ReactNode } from "react";
import { usePathname } from "next/navigation";
import { Confetti } from "@/components/Confetti";
import { RequireAuth } from "@/components/RequireAuth";
import { AcademyProvider, useAcademy } from "./AcademyProvider";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";
import { titleForPath, streakColors } from "./data";

const EMPTY_STREAK = Array<number>(36).fill(0);

/**
 * The furniture every academy screen sits in.
 *
 * It's a layout rather than part of a page so it survives navigation: the provider inside
 * keeps the toy's charge, the boss clock and any in-flight judge poll alive while the
 * screen under it is swapped out.
 */
export function AcademyShell({ children }: { children: ReactNode }) {
  return (
    <RequireAuth>
      <AcademyProvider>
        <Chrome>{children}</Chrome>
      </AcademyProvider>
    </RequireAuth>
  );
}

function Chrome({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { dashboard, streak, sprocketMsg, winding, windUp, confetti } = useAcademy();
  const progress = dashboard.data?.progress ?? null;

  return (
    <div
      style={{
        display: "flex",
        minHeight: "100vh",
        background:
          "repeating-linear-gradient(96deg,#E9D2A6 0px,#E9D2A6 46px,#E4CB9C 46px,#E4CB9C 48px)",
      }}
      className="acad-shell"
    >
      <Sidebar sprocketMsg={sprocketMsg} />

      <main
        style={{
          flex: 1,
          minWidth: 0,
          display: "flex",
          flexDirection: "column",
          background: "#FCF6E9",
        }}
      >
        <Topbar
          title={titleForPath(pathname)}
          level={progress?.level ?? 1}
          levelName={progress?.level_name ?? "Freshly Unboxed"}
          xp={progress?.xp ?? 0}
          xpMax={progress?.xp_max ?? 500}
          xpPct={progress?.xp_pct ?? 0}
          streak={progress?.streak ?? 0}
          coins={progress?.coins ?? 0}
          streakCells={streakColors(streak.data?.cells ?? EMPTY_STREAK)}
          windAvailable={dashboard.data?.wind_up_available ?? false}
          winding={winding}
          onWind={windUp}
        />

        <div className="acad-main" style={{ padding: "26px 30px 60px", flex: 1 }}>{children}</div>
      </main>

      <Confetti pieces={confetti} />
    </div>
  );
}
