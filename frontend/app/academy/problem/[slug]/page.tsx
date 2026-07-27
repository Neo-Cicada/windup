import type { Metadata } from "next";
import { ProblemRoute } from "@/components/academy/routes/ProblemRoute";

// Naming the actual problem here isn't possible: generateMetadata runs on the server and
// the toy's token lives in localStorage.
export const metadata: Metadata = { title: "Problem View" };

export default async function Page(props: PageProps<"/academy/problem/[slug]">) {
  const { slug } = await props.params;
  return <ProblemRoute slug={slug} />;
}
