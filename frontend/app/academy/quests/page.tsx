import type { Metadata } from "next";
import { QuestsRoute } from "@/components/academy/routes/QuestsRoute";

export const metadata: Metadata = { title: "Quest Map" };

export default function Page() {
  return <QuestsRoute />;
}
