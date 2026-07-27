import type { Metadata } from "next";
import { DashboardRoute } from "@/components/academy/routes/DashboardRoute";

export const metadata: Metadata = { title: "Playroom" };

export default function Page() {
  return <DashboardRoute />;
}
