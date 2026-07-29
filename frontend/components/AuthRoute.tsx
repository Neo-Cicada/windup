"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Auth, type AuthMode, type AuthValues } from "@/components/Auth";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { Winding } from "@/components/ScreenState";
import { pageBg } from "@/components/publicBg";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

/**
 * Where to go after signing in.
 *
 * Only same-origin academy paths are honoured. `next` arrives in a URL anyone can hand
 * to anyone, so anything else — an absolute URL, a protocol-relative `//evil.com`, a
 * path outside the academy — falls back to the playroom rather than becoming an open
 * redirect wearing our login page.
 */
function destination(next: string | null): string {
  if (next === null) return "/academy";
  if (!next.startsWith("/academy") || next.startsWith("//")) return "/academy";
  return next;
}

/**
 * Reading `next` means reading the query string, and `useSearchParams` makes a
 * prerendered page bail out to the client unless there's a boundary to bail out *to* —
 * so the form owns one rather than every page that renders it needing to remember.
 */
export function AuthRoute({ mode }: { mode: AuthMode }) {
  return (
    <Suspense
      fallback={
        <div style={{ minHeight: "100vh", background: pageBg, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Winding label="Unlocking the door…" />
        </div>
      }
    >
      <AuthForm mode={mode} />
    </Suspense>
  );
}

function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const params = useSearchParams();
  const next = destination(params.get("next"));
  const { status, login, signup } = useAuth();

  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  const [showWelcome, setShowWelcome] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const navTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (clearTimer.current) clearTimeout(clearTimer.current);
      if (navTimer.current) clearTimeout(navTimer.current);
    };
  }, []);

  // An already-authed visitor has no business on the forms. The exception is the
  // celebration below, which owns its own navigation so the confetti gets to finish.
  useEffect(() => {
    if (status === "authed" && !showWelcome) router.replace(next);
  }, [status, showWelcome, next, router]);

  function burst(n: number) {
    setConfetti(makeBurst(n));
    if (clearTimer.current) clearTimeout(clearTimer.current);
    clearTimer.current = setTimeout(() => setConfetti([]), 2400);
  }

  async function submit({ toyName, email, password }: AuthValues) {
    setPending(true);
    setError(null);
    try {
      if (mode === "signup") {
        await signup(toyName, email, password);
      } else {
        await login(email, password);
      }
      burst(mode === "signup" ? 70 : 34);
      setShowWelcome(true);
      if (navTimer.current) clearTimeout(navTimer.current);
      navTimer.current = setTimeout(() => router.push(next), 950);
    } catch (err) {
      setError(errorMessage(err));
      setPending(false);
    }
  }

  if (status === "authed" && !showWelcome) {
    return (
      <div style={{ minHeight: "100vh", background: pageBg, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Winding label="Off to the academy…" />
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", background: pageBg }}>
      <Auth
        mode={mode}
        showWelcome={showWelcome}
        pending={pending}
        error={error}
        onBack={() => router.push("/")}
        onSubmit={submit}
        onSwitchMode={() => router.push(mode === "signup" ? "/login" : "/signup")}
      />
      <Confetti pieces={confetti} />
    </div>
  );
}
