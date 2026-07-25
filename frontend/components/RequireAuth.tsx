"use client";

import { useEffect, type ReactNode } from "react";
import { useRouter } from "next/navigation";
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

  useEffect(() => {
    if (status === "anon") router.replace("/");
  }, [status, router]);

  if (status !== "authed") {
    return (
      <div style={{ minHeight: "100vh", background: "#FCF6E9", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Winding label={status === "anon" ? "Back to the playroom…" : "Checking your key…"} />
      </div>
    );
  }

  return <>{children}</>;
}
