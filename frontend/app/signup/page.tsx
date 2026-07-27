import type { Metadata } from "next";
import { AuthRoute } from "@/components/AuthRoute";

export const metadata: Metadata = { title: "Sign up" };

export default function Page() {
  return <AuthRoute mode="signup" />;
}
