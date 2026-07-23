"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Landing } from "@/components/Landing";
import { Auth, type AuthMode } from "@/components/Auth";
import { Confetti, makeBurst, type ConfettiPiece } from "@/components/Confetti";

type View = "landing" | AuthMode;

const pageBg =
  "radial-gradient(circle at 80% -5%,#FBEBD0,transparent 45%),radial-gradient(circle at 5% 20%,#F7E0C4,transparent 40%),#F3E3C3";

export default function Page() {
  const router = useRouter();
  const [view, setView] = useState<View>("landing");
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([]);
  const [showWelcome, setShowWelcome] = useState(false);

  const clearTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const navTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (clearTimer.current) clearTimeout(clearTimer.current);
      if (navTimer.current) clearTimeout(navTimer.current);
    };
  }, []);

  const go = useCallback((next: View) => {
    setView(next);
    setShowWelcome(false);
    if (typeof window !== "undefined") window.scrollTo(0, 0);
  }, []);

  const burst = useCallback((n: number) => {
    setConfetti(makeBurst(n));
    if (clearTimer.current) clearTimeout(clearTimer.current);
    clearTimer.current = setTimeout(() => setConfetti([]), 2400);
  }, []);

  const submit = useCallback(() => {
    burst(view === "signup" ? 70 : 34);
    setShowWelcome(true);
    if (navTimer.current) clearTimeout(navTimer.current);
    navTimer.current = setTimeout(() => router.push("/academy"), 950);
  }, [burst, view, router]);

  return (
    <div style={{ minHeight: "100vh", background: pageBg }}>
      {view === "landing" ? (
        <Landing onLogin={() => go("login")} onSignup={() => go("signup")} />
      ) : (
        <Auth
          mode={view}
          showWelcome={showWelcome}
          onBack={() => go("landing")}
          onSubmit={submit}
          onSwitchMode={() => go(view === "signup" ? "login" : "signup")}
        />
      )}
      <Confetti pieces={confetti} />
    </div>
  );
}
