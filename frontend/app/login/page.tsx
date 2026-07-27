import type { Metadata } from "next";
import { AuthRoute } from "@/components/AuthRoute";

export const metadata: Metadata = { title: "Log in" };

export default function Page() {
  return <AuthRoute mode="login" />;
}
