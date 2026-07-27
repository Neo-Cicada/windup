import type { Metadata } from "next";
import { AnalyticsRoute } from "@/components/academy/routes/AnalyticsRoute";

export const metadata: Metadata = { title: "Analytics" };

export default function Page() {
  return <AnalyticsRoute />;
}
