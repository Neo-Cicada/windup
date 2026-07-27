"use client";

import { useRouter } from "next/navigation";
import { ScreenState } from "@/components/ScreenState";
import { Dashboard } from "@/components/academy/screens/Dashboard";
import { useAcademy } from "@/components/academy/AcademyProvider";

export function DashboardRoute() {
  const router = useRouter();
  const { dashboard } = useAcademy();

  if (dashboard.data === null) {
    return (
      <ScreenState
        loading={dashboard.loading}
        error={dashboard.error}
        onRetry={dashboard.reload}
        label="Opening the playroom…"
      />
    );
  }

  const d = dashboard.data;
  return (
    <Dashboard
      toyName={d.toy_name}
      traineeNo={d.trainee_no}
      avBody={d.avatar_body}
      avHead={d.avatar_head}
      avAccent={d.avatar_accent}
      ready={d.progress.interview_ready}
      level={d.progress.level}
      solved={d.progress.solved_count}
      unaidedRate={d.progress.unaided_rate}
      badgesLabel={d.badges_label}
      rank={d.rank}
      sprocketMessage={d.sprocket_message}
      quests={d.quests}
      questsDone={d.quests_done}
      onOpenProblem={(slug) => router.push(`/academy/problem/${slug}`)}
    />
  );
}
