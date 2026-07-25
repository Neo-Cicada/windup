"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Landing } from "@/components/Landing";
import { Auth, type AuthMode, type AuthValues } from "@/components/Auth";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";
import { errorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth";

type View = "landing" | AuthMode;

const pageBg =
  "radial-gradient(circle at 80% -5%,#FBEBD0,transparent 45%),radial-gradient(circle at 5% 20%,#F7E0C4,transparent 40%),#F3E3C3";

export default function Page() {
  const router = useRouter();
  const { status, login, signup } = useAuth();
  const [view, setView] = useState<View>("landing");
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

  // Already wound up? The forms have nothing to offer — go straight to the academy.
  useEffect(() => {
    if (status === "authed" && view !== "landing") router.replace("/academy");
  }, [status, view, router]);

  const go = useCallback((next: View) => {
    setView(next);
    setShowWelcome(false);
    setError(null);
    if (typeof window !== "undefined") window.scrollTo(0, 0);
  }, []);

  const burst = useCallback((n: number) => {
    setConfetti(makeBurst(n));
    if (clearTimer.current) clearTimeout(clearTimer.current);
    clearTimer.current = setTimeout(() => setConfetti([]), 2400);
  }, []);

  const submit = useCallback(
    async ({ toyName, email, password }: AuthValues) => {
      setPending(true);
      setError(null);
      try {
        if (view === "signup") {
          await signup(toyName, email, password);
        } else {
          await login(email, password);
        }
        burst(view === "signup" ? 70 : 34);
        setShowWelcome(true);
        if (navTimer.current) clearTimeout(navTimer.current);
        navTimer.current = setTimeout(() => router.push("/academy"), 950);
      } catch (err) {
        setError(errorMessage(err));
        setPending(false);
      }
    },
    [burst, view, router, login, signup]
  );

  return (
    <div style={{ minHeight: "100vh", background: pageBg }}>
      {view === "landing" ? (
        <Landing onLogin={() => go("login")} onSignup={() => go("signup")} />
      ) : (
        <Auth
          mode={view}
          showWelcome={showWelcome}
          pending={pending}
          error={error}
          onBack={() => go("landing")}
          onSubmit={submit}
          onSwitchMode={() => go(view === "signup" ? "login" : "signup")}
        />
      )}
      <Confetti pieces={confetti} />
    </div>
  );
}
