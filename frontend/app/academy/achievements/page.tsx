import type { Metadata } from "next";
import { AchievementsRoute } from "@/components/academy/routes/AchievementsRoute";

export const metadata: Metadata = { title: "Merit Sash" };

export default function Page() {
  return <AchievementsRoute />;
}
