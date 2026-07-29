"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Winding } from "@/components/ScreenState";
import { DuelInvite } from "@/components/academy/screens/DuelInvite";
import { useAcademy } from "@/components/academy/AcademyProvider";
import { api, errorMessage } from "@/lib/api";
import type { DuelInvite as Invite } from "@/lib/types";

/**
 * Where a shared invite link lands.
 *
 * The preview is fetched here rather than in `useDuel`: it belongs to a duel the toy is
 * not in yet, so it isn't part of the shared duel state and nothing above this route
 * needs it. Accepting hands off to `useDuel.join`, which is what the rest of the academy
 * reads from.
 */
export function DuelInviteRoute({ code }: { code: string }) {
  const { duel, say } = useAcademy();
  const router = useRouter();

  const [invite, setInvite] = useState<Invite | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api<Invite>(`/duels/by-code/${encodeURIComponent(code)}`)
      .then((next) => {
        if (!cancelled) setInvite(next);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err));
      });
    return () => {
      cancelled = true;
    };
  }, [code]);

  // Already in this duel — nothing to accept, go straight to the arena. Covers the back
  // button and a second tab as well as a plain refresh.
  useEffect(() => {
    if (duel.duel?.code === code && duel.duel.status === "active") {
      router.replace("/academy/duel");
    }
  }, [duel.duel?.code, duel.duel?.status, code, router]);

  async function accept() {
    await duel.join(code);
    router.replace("/academy/duel");
  }

  if (loadError !== null) {
    return (
      <div style={{ maxWidth: 520, margin: "0 auto", textAlign: "center" }}>
        <div role="alert" style={{ background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "14px 16px", fontSize: 14, fontWeight: 700, color: "#B4342D" }}>
          {loadError}
        </div>
        <button
          className="tap"
          onClick={() => router.replace("/academy/duel")}
          style={{ marginTop: 16, border: "4px solid #2E2620", borderRadius: 18, background: "#F7C948", color: "#2E2620", fontWeight: 700, fontSize: 16, padding: "12px 24px" }}
        >
          Back to duels
        </button>
      </div>
    );
  }

  if (invite === null) return <Winding label="Reading the challenge…" />;

  return (
    <DuelInvite
      invite={invite}
      pending={duel.pending}
      error={duel.error}
      onAccept={() => {
        say(`Accepting ${invite.host_name}'s challenge…`);
        void accept();
      }}
      onBack={() => router.replace("/academy/duel")}
    />
  );
}
