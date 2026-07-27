"use client";

import { ScreenState } from "@/components/ScreenState";
import { Achievements } from "@/components/academy/screens/Achievements";
import { useAuth } from "@/lib/auth";
import { useResource } from "@/lib/useResource";
import type { AchievementsSummary } from "@/lib/types";

export function AchievementsRoute() {
  const { user } = useAuth();
  const achievements = useResource<AchievementsSummary>("/achievements");

  if (achievements.data === null) {
    return (
      <ScreenState
        loading={achievements.loading}
        error={achievements.error}
        onRetry={achievements.reload}
        label="Polishing badges…"
      />
    );
  }

  return <Achievements toyName={user?.toy_name ?? "Your"} data={achievements.data} />;
}
