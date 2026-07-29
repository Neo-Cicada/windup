"use client";

import { useEffect, useRef, useState } from "react";
import { api, errorMessage, post } from "@/lib/api";
import type { Duel } from "@/lib/types";

const DUEL_FALLBACK_SECONDS = 900;

export type DuelGame = {
  duel: Duel | null;
  /** Ticked down locally between polls; every server response re-syncs it. */
  remaining: number;
  /** False until the first `/duels/current` has settled, so the screen can wait. */
  ready: boolean;
  pending: boolean;
  error: string | null;
  create: () => Promise<void>;
  join: (code: string) => Promise<void>;
  forfeit: () => Promise<void>;
  cancel: () => Promise<void>;
  refresh: () => Promise<void>;
  /** The id to tag a submission with, or null when no round could be cleared by one. */
  activeId: string | null;
};

type Options = {
  /** A duel that reached a verdict — the caller celebrates and moves the topbar. */
  onFinish: (duel: Duel) => void;
  /** Sprocket's line. */
  say: (message: string) => void;
};

const isLive = (d: Duel | null) => d !== null && (d.status === "waiting" || d.status === "active");

/**
 * The duel: its clock, its poll, and the id a submission has to carry.
 *
 * Like the boss fight this has to live above the routes. A round only clears if the
 * submission carries the duel's id, and that id is read from the *problem* route —
 * following a round straight to `/academy/problem/two-sum`, or opening a bookmark, is
 * a perfectly normal way in and never touches the duel screen at all.
 *
 * The other half is the poll. Unlike the boss, a duel changes because of something the
 * *other* toy did, so there is no local event to hang a refresh on: watching their chips
 * light up is the entire game, and only the server knows.
 */
export function useDuel({ onFinish, say }: Options): DuelGame {
  const [duel, setDuel] = useState<Duel | null>(null);
  const [ready, setReady] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [remaining, setRemaining] = useState(DUEL_FALLBACK_SECONDS);

  // Whether the last state we saw was still being fought over. Compared inside the poll
  // callback rather than derived during render — reading it while rendering would make
  // the render impure, and the compiler rejects that.
  const wasLive = useRef(false);
  // One request at a time. A slow response must not let the next tick stack another.
  const inFlight = useRef(false);

  function adopt(next: Duel | null) {
    setDuel(next);
    setRemaining(next?.remaining_seconds ?? DUEL_FALLBACK_SECONDS);
    if (next !== null && wasLive.current && !isLive(next)) onFinish(next);
    wasLive.current = isLive(next);
  }

  // The poll below must not list `adopt` as a dependency: `onFinish` is an inline
  // closure over the caller's resources, so `adopt` changes identity most renders, and
  // a dependency on it would tear down and rebuild the interval before it ever fired.
  // Reaching it through a ref, assigned in an effect rather than during render, keeps
  // the interval keyed on the duel alone while still calling the current version.
  const adoptRef = useRef(adopt);
  useEffect(() => {
    adoptRef.current = adopt;
  });

  // Unconditional, on mount — the same reason the boss fight does it. Setting state
  // from the promise callback, never synchronously in the effect body.
  useEffect(() => {
    let cancelled = false;
    api<Duel | null>("/duels/current")
      .then((current) => {
        if (cancelled) return;
        setDuel(current);
        setRemaining(current?.remaining_seconds ?? DUEL_FALLBACK_SECONDS);
        wasLive.current = isLive(current);
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

  // The poll. Cadence comes from the server (`poll_after_ms`) rather than from a
  // constant here, so "2s while racing, 5s while waiting, stop when it's over" is
  // decided in one place. A zero means there is nothing left to watch.
  const duelId = duel?.id ?? null;
  const pollAfter = duel?.poll_after_ms ?? 0;
  useEffect(() => {
    if (duelId === null || pollAfter <= 0) return;
    let cancelled = false;

    const id = setInterval(() => {
      // A backgrounded tab has nobody looking at it; the next visible tick re-syncs.
      if (document.visibilityState === "hidden" || inFlight.current) return;
      inFlight.current = true;
      api<Duel>(`/duels/${duelId}`)
        .then((next) => {
          if (!cancelled) adoptRef.current(next);
        })
        .catch(() => {
          // A dropped poll changes nothing — the next tick tries again.
        })
        .finally(() => {
          inFlight.current = false;
        });
    }, pollAfter);

    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, [duelId, pollAfter]);

  // The on-screen countdown is cosmetic. The server derives the real remaining time
  // from when the duel started, so a refresh or a second tab can't stretch it — and
  // both toys are reading the same clock.
  useEffect(() => {
    if (duel?.status !== "active") return;
    const id = setInterval(() => setRemaining((r) => Math.max(0, r - 1)), 1000);
    return () => clearInterval(id);
  }, [duel?.status]);

  async function refresh() {
    if (duel === null) return;
    try {
      adopt(await api<Duel>(`/duels/${duel.id}`));
    } catch (err) {
      setError(errorMessage(err));
    }
  }

  async function run(work: () => Promise<Duel>, line?: string) {
    setPending(true);
    setError(null);
    try {
      adopt(await work());
      if (line) say(line);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setPending(false);
    }
  }

  return {
    duel,
    remaining,
    ready,
    pending,
    error,
    create: () =>
      run(
        () => post<Duel>("/duels"),
        "Challenge open! Send that code to another toy."
      ),
    join: (code: string) =>
      run(
        () => post<Duel>(`/duels/by-code/${encodeURIComponent(code.trim())}/join`),
        "Race is on — first to fix them all takes it!"
      ),
    forfeit: () =>
      run(() => post<Duel>(`/duels/${duel?.id}/actions`, { action: "forfeit" })),
    cancel: () => run(() => post<Duel>(`/duels/${duel?.id}/actions`, { action: "cancel" })),
    refresh,
    // Only an active duel can have a round cleared, so only an active duel is worth
    // tagging a submission with. The server checks this again anyway.
    activeId: duel !== null && duel.status === "active" ? duel.id : null,
  };
}
