import type { Metadata } from "next";
import { ProfileRoute } from "@/components/academy/routes/ProfileRoute";

export const metadata: Metadata = { title: "Profile" };

export default function Page() {
  return <ProfileRoute />;
}
