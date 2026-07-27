import type { Metadata } from "next";
import { LeaderboardRoute } from "@/components/academy/routes/LeaderboardRoute";

export const metadata: Metadata = { title: "Shelf of Fame" };

export default function Page() {
  return <LeaderboardRoute />;
}
