"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Landing } from "@/components/Landing";
import { Winding } from "@/components/ScreenState";
import { useAuth } from "@/lib/auth";
import { pageBg } from "@/components/publicBg";

export function LandingRoute() {
  const router = useRouter();
  const { status } = useAuth();

  // Already wound up? The pitch has nothing to offer — go straight to the academy.
  useEffect(() => {
    if (status === "authed") router.replace("/academy");
  }, [status, router]);

  // A confirmed session is on its way out of this route, so don't paint the pitch at it.
  // "loading" still shows the landing page: with no stored token the check resolves in a
  // tick, and a spinner in front of the public page would flicker for every new visitor.
  if (status === "authed") {
    return (
      <div style={{ minHeight: "100vh", background: pageBg, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Winding label="Off to the academy…" />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: pageBg }}>
      <Landing onLogin={() => router.push("/login")} onSignup={() => router.push("/signup")} />
    </div>
  );
}
