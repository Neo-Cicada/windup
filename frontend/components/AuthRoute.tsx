"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Auth, type AuthMode, type AuthValues } from "@/components/Auth";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { Winding } from "@/components/ScreenState";
import { pageBg } from "@/components/publicBg";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export function AuthRoute({ mode }: { mode: AuthMode }) {
  const router = useRouter();
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
    if (status === "authed" && !showWelcome) router.replace("/academy");
  }, [status, showWelcome, router]);

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
      navTimer.current = setTimeout(() => router.push("/academy"), 950);
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
