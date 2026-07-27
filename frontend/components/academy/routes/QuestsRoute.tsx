"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { ScreenState } from "@/components/ScreenState";
import { QuestMap } from "@/components/academy/screens/QuestMap";
import { useResource } from "@/lib/useResource";
import type { Problem, Zone } from "@/lib/types";

export function QuestsRoute() {
  const router = useRouter();

  // The open corner is a `?zone=` param rather than local state, so it survives walking off
  // to a problem and pressing Back — and the map is linkable with a corner already open.
  const zoneParam = useSearchParams().get("zone");
  const openZone = zoneParam === null || zoneParam === "" ? null : zoneParam;

  const zones = useResource<Zone[]>("/zones");
  const zoneProblems = useResource<Problem[]>(
    `/zones/${openZone ?? ""}/problems`,
    openZone !== null
  );

  // replaceState, not router.replace: toggling a corner shouldn't stack a history entry
  // for every click, and there's nothing on the server to re-run.
  function selectZone(slug: string) {
    const next = openZone === slug ? null : slug;
    window.history.replaceState(
      null,
      "",
      next === null ? "/academy/quests" : `/academy/quests?zone=${encodeURIComponent(next)}`
    );
  }

  if (zones.data === null) {
    return (
      <ScreenState
        loading={zones.loading}
        error={zones.error}
        onRetry={zones.reload}
        label="Unrolling the map…"
      />
    );
  }

  return (
    <QuestMap
      zones={zones.data}
      openZone={openZone}
      problems={zoneProblems.data ?? []}
      problemsLoading={zoneProblems.loading}
      problemsError={zoneProblems.error}
      onSelectZone={selectZone}
      onOpenProblem={(slug) => router.push(`/academy/problem/${slug}`)}
    />
  );
}
