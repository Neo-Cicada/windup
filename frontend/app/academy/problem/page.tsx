import type { Metadata } from "next";
import { ProblemRedirect } from "@/components/academy/routes/ProblemRedirect";

export const metadata: Metadata = { title: "Problem View" };

export default function Page() {
  return <ProblemRedirect />;
}
