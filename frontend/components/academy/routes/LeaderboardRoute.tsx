"use client";

import { ScreenState } from "@/components/ScreenState";
import { Leaderboard } from "@/components/academy/screens/Leaderboard";
import { useResource } from "@/lib/useResource";
import type { LeaderboardSummary } from "@/lib/types";

export function LeaderboardRoute() {
  const leaderboard = useResource<LeaderboardSummary>("/leaderboard");

  if (leaderboard.data === null) {
    return (
      <ScreenState
        loading={leaderboard.loading}
        error={leaderboard.error}
        onRetry={leaderboard.reload}
        label="Dusting the shelf…"
      />
    );
  }

  return <Leaderboard data={leaderboard.data} />;
}
