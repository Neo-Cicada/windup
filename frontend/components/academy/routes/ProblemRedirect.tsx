"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { EmptyPanel, Winding } from "@/components/ScreenState";
import { useAcademy } from "@/components/academy/AcademyProvider";

/**
 * `/academy/problem` with nothing picked — take the first of today's quests.
 *
 * The sidebar keeps the bare href so the tab is always clickable; this is what turns it
 * into a real problem. `replace`, so Back doesn't land here and bounce forward again.
 */
export function ProblemRedirect() {
  const router = useRouter();
  const { dashboard } = useAcademy();

  const first = dashboard.data?.quests[0]?.slug ?? null;

  useEffect(() => {
    if (first !== null) router.replace(`/academy/problem/${first}`);
  }, [first, router]);

  if (first !== null || dashboard.loading) return <Winding label="Fetching the toy…" />;

  return (
    <EmptyPanel
      title="An empty workbench"
      message="Nothing is clamped in the vice yet. Pick a toy corner and choose something to fix."
      actionLabel="Open the Quest Map"
      onAction={() => router.push("/academy/quests")}
    />
  );
}
