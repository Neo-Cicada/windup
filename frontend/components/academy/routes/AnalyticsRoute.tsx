"use client";

import { ScreenState } from "@/components/ScreenState";
import { Analytics } from "@/components/academy/screens/Analytics";
import { useResource } from "@/lib/useResource";
import type { AnalyticsSummary } from "@/lib/types";

export function AnalyticsRoute() {
  const analytics = useResource<AnalyticsSummary>("/analytics");

  if (analytics.data === null) {
    return (
      <ScreenState
        loading={analytics.loading}
        error={analytics.error}
        onRetry={analytics.reload}
        label="Counting the charge…"
      />
    );
  }

  return <Analytics data={analytics.data} />;
}
