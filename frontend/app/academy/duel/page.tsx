import type { Metadata } from "next";
import { DuelRoute } from "@/components/academy/routes/DuelRoute";

export const metadata: Metadata = { title: "Duel" };

export default function Page() {
  return <DuelRoute />;
}
