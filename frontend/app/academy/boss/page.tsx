import type { Metadata } from "next";
import { BossRoute } from "@/components/academy/routes/BossRoute";

export const metadata: Metadata = { title: "Boss Battle" };

export default function Page() {
  return <BossRoute />;
}
