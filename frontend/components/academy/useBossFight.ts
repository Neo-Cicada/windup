"use client";

import { useEffect, useState } from "react";
import { api, errorMessage, post } from "@/lib/api";
import type { BossAction, BossSession } from "@/lib/types";

const BOSS_FALLBACK_SECONDS = 900;

export type BossFight = {
  session: BossSession | null;
  /** Ticked down locally between requests; every server response re-syncs it. */
  remaining: number;
  /** False until the first `/boss/current` has settled, so the screen can wait. */
  ready: boolean;
  pending: boolean;
  error: string | null;
  /** What pressing the main button will actually do. */
  label: string;
  /** No fight to resume — the button starts a new one. */
  spent: boolean;
  toggle: () => Promise<void>;
  complete: () => Promise<void>;
  abandon: () => Promise<void>;
  refresh: () => Promise<void>;
};

type Options = {
  /** A fight that was actually beaten — the caller pays out and celebrates. */
  onWin: (session: BossSession) => void;
  /** Sprocket's line. */
  say: (message: string) => void;
};

/**
 * The boss clock, lifted out of any one screen.
 *
 * This has to live above the routes: a submission is only counted towards a round if it
 * carries the running session's id, and that id is read from the *problem* route. Fetch it
 * only when the boss screen is open and every fight silently stops clearing.
 */
export function useBossFight({ onWin, say }: Options): BossFight {
  const [session, setSession] = useState<BossSession | null>(null);
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remaining, setRemaining] = useState(BOSS_FALLBACK_SECONDS);

  function adopt(next: BossSession | null) {
    setSession(next);
    setRemaining(next?.remaining_seconds ?? BOSS_FALLBACK_SECONDS);
  }

  // Unconditional, on mount. A toy can land straight on a problem link with a fight already
  // running — nothing forces them through the boss screen first.
  useEffect(() => {
    let cancelled = false;
    api<BossSession | null>("/boss/current")
      .then((current) => {
        if (cancelled) return;
        setSession(current);
        setRemaining(current?.remaining_seconds ?? BOSS_FALLBACK_SECONDS);
        setReady(true);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(errorMessage(err));
        setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // The on-screen countdown is cosmetic. The server computes the real remaining time
  // from when the fight was last resumed, so a refresh or a second tab can't stretch it.
  useEffect(() => {
    if (session?.status !== "running") return;
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(id);
  }, [session?.status]);

  // Out of time on screen: let the server settle the session and tell us the verdict.
  useEffect(() => {
    if (session?.status !== "running" || remaining > 0) return;
    let cancelled = false;
    api<BossSession | null>("/boss/current")
      .then((settled) => {
        if (cancelled) return;
        setSession(settled);
        setRemaining(settled?.remaining_seconds ?? 0);
      })
      .catch(() => {
        // The clock already reads zero on screen; a failed poll changes nothing.
      });
    return () => {
      cancelled = true;
    };
  }, [session?.status, remaining]);

  async function refresh() {
    try {
      adopt(await api<BossSession | null>("/boss/current"));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function act(action: BossAction) {
    if (session === null) return;
    setPending(true);
    setError(null);
    try {
      const next = await post<BossSession>(`/boss/sessions/${session.id}`, { action });
      adopt(next);
      if (action === "complete" && next.status === "completed") onWin(next);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  async function start() {
    setPending(true);
    setError(null);
    try {
      adopt(await post<BossSession>("/boss/sessions"));
      say("The Jack-in-the-Box is winding up. Fix the rounds before it springs!");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  const spent =
    session === null ||
    remaining <= 0 ||
    session.status === "completed" ||
    session.status === "expired";

  // Derived from the same fields the server labels with, so the button always says what
  // clicking it will do — the server's own label reads "Begin battle" for a fight paused
  // on its first second, which would then resume rather than start.
  const label = spent
    ? session === null
      ? "Begin battle"
      : "Rematch"
    : session.status === "running"
      ? "Pause fight"
      : "Resume fight";

  function toggle() {
    if (spent) return start();
    return act(session.status === "running" ? "pause" : "resume");
  }

  return {
    session,
    remaining,
    ready,
    pending,
    error,
    label,
    spent,
    toggle,
    complete: () => act("complete"),
    abandon: () => act("abandon"),
    refresh,
  };
}
