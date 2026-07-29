"use client";

import { useEffect, type ReactNode } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { Winding } from "./ScreenState";

/**
 * Gate for signed-in screens. The token check happens on the client, so children are
 * never rendered until the API has confirmed the session — an unauthenticated visitor
 * gets the winding screen and then the landing page, never a flash of the academy.
 */
export function RequireAuth({ children }: { children: ReactNode }) {
  const { status } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (status !== "anon") return;
    // Carry where they were headed. A duel invite is the case that makes this matter:
    // the link is shared with a friend precisely when that friend may not be signed in
    // yet, and dropping them on the landing page loses the code entirely.
    router.replace(`/login?next=${encodeURIComponent(pathname)}`);
  }, [status, pathname, router]);

  if (status !== "authed") {
    return (
      <div style={{ minHeight: "100vh", background: "#FCF6E9", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Winding label={status === "anon" ? "Finding your key…" : "Checking your key…"} />
      </div>
    );
  }

  return <>{children}</>;
}
