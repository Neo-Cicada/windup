"use client";

import { useEffect, useState } from "react";
import { api, errorMessage } from "./api";

export type Resource<T> = {
  data: T | null;
  error: string | null;
  loading: boolean;
  reload: () => void;
  /** Apply a server response we already have in hand, without a round trip. */
  set: (data: T) => void;
};

/** What the last settled request produced, tagged with the path it was for. */
type Snapshot<T> = { path: string; data: T | null; error: string | null };

/**
 * GET a path into state. Pass `enabled: false` to hold off until the screen is open,
 * so opening the Playroom doesn't also fetch the leaderboard and the merit sash.
 *
 * `loading` is derived rather than stored: a snapshot whose path doesn't match the one
 * being asked for is, by definition, a request still in flight.
 */
export function useResource<T>(path: string, enabled = true): Resource<T> {
  const [snapshot, setSnapshot] = useState<Snapshot<T>>({ path, data: null, error: null });
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    api<T>(path)
      .then((data) => {
        if (!cancelled) setSnapshot({ path, data, error: null });
      })
      .catch((err) => {
        if (!cancelled) setSnapshot({ path, data: null, error: errorMessage(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [path, enabled, nonce]);

  const current = snapshot.path === path ? snapshot : null;
  const data = current?.data ?? null;
  const error = current?.error ?? null;

  return {
    data,
    error,
    loading: enabled && data === null && error === null,
    reload: () => {
      setSnapshot({ path, data: null, error: null });
      setNonce((n) => n + 1);
    },
    set: (next: T) => setSnapshot({ path, data: next, error: null }),
  };
}
