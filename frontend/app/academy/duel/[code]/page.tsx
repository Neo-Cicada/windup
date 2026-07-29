import type { Metadata } from "next";
import { DuelInviteRoute } from "@/components/academy/routes/DuelInviteRoute";

// Naming the challenger here isn't possible: generateMetadata runs on the server and
// the toy's token lives in localStorage.
export const metadata: Metadata = { title: "Duel Invite" };

export default async function Page(props: PageProps<"/academy/duel/[code]">) {
  const { code } = await props.params;
  return <DuelInviteRoute code={code} />;
}
