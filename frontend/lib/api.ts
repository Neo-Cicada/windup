// Fetch client for the FastAPI backend.
//
// Tokens live in localStorage because the API is a stateless bearer-token service —
// there is no cookie session to ride on. That trades XSS exposure for simplicity; if
// the backend ever grows an httpOnly-cookie flow, this is the only file that changes.

import type { TokenPair } from "./types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

const ACCESS_KEY = "windup_access";
const REFRESH_KEY = "windup_refresh";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** The toy-voiced detail the API sends, or a fallback in the same register. */
export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error && err.message) return err.message;
  return "Sprocket couldn't reach the workshop. Is the API running?";
}

// ---- token storage ----------------------------------------------------------

let access: string | null = null;
let refresh: string | null = null;
let hydrated = false;

function hydrate(): void {
  if (hydrated || typeof window === "undefined") return;
  access = window.localStorage.getItem(ACCESS_KEY);
  refresh = window.localStorage.getItem(REFRESH_KEY);
  hydrated = true;
}

export function getAccessToken(): string | null {
  hydrate();
  return access;
}

export function setTokens(pair: TokenPair): void {
  hydrate();
  access = pair.access_token;
  refresh = pair.refresh_token;
  if (typeof window !== "undefined") {
    window.localStorage.setItem(ACCESS_KEY, pair.access_token);
    window.localStorage.setItem(REFRESH_KEY, pair.refresh_token);
  }
}

export function clearTokens(): void {
  hydrate();
  access = null;
  refresh = null;
  if (typeof window !== "undefined") {
    window.localStorage.removeItem(ACCESS_KEY);
    window.localStorage.removeItem(REFRESH_KEY);
  }
}

/** Notifies the auth provider when a refresh fails and the session is really gone. */
const expiryListeners = new Set<() => void>();

export function onSessionExpired(fn: () => void): () => void {
  expiryListeners.add(fn);
  return () => {
    expiryListeners.delete(fn);
  };
}

function expireSession(): void {
  clearTokens();
  expiryListeners.forEach((fn) => fn());
}

// ---- requests ---------------------------------------------------------------

async function detailOf(res: Response): Promise<string> {
  try {
    const body = await res.json();
    const detail = body?.detail;
    if (typeof detail === "string") return detail;
    // 422 from FastAPI: a list of validation errors.
    if (Array.isArray(detail) && detail.length > 0 && typeof detail[0]?.msg === "string") {
      return detail[0].msg;
    }
  } catch {
    // fall through to the status text
  }
  return res.statusText || "Something jammed in the gears.";
}

let refreshInFlight: Promise<boolean> | null = null;

/** Single-flight token refresh: parallel 401s wait on the same round trip. */
async function refreshTokens(): Promise<boolean> {
  if (!refresh) return false;
  if (!refreshInFlight) {
    const token = refresh;
    refreshInFlight = (async () => {
      try {
        const res = await fetch(`${API_BASE}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: token }),
        });
        if (!res.ok) return false;
        setTokens((await res.json()) as TokenPair);
        return true;
      } catch {
        return false;
      } finally {
        refreshInFlight = null;
      }
    })();
  }
  return refreshInFlight;
}

type Options = RequestInit & {
  /** Skip the Authorization header — for signup / login / refresh. */
  anon?: boolean;
};

async function request<T>(path: string, options: Options, canRetry: boolean): Promise<T> {
  hydrate();
  const { anon = false, ...init } = options;

  const headers = new Headers(init.headers);
  if (init.body !== undefined && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!anon && access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${API_BASE}${path}`, { ...init, headers });

  // A 401 on a request we authenticated means the access token died. Try the refresh
  // token once; if that is dead too, the session is over. A 401 with no token attached
  // is an ordinary failure (bad login), so it falls through to the error path below.
  if (res.status === 401 && !anon && access) {
    if (canRetry && (await refreshTokens())) return request<T>(path, options, false);
    expireSession();
    throw new ApiError(401, "Your session wound down — log in again.");
  }

  if (!res.ok) throw new ApiError(res.status, await detailOf(res));
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export function api<T>(path: string, options: Options = {}): Promise<T> {
  return request<T>(path, options, true);
}

/** POST a JSON body. */
export function post<T>(path: string, body?: unknown, options: Options = {}): Promise<T> {
  return api<T>(path, { ...options, method: "POST", body: JSON.stringify(body ?? {}) });
}

/** PATCH a JSON body. */
export function patch<T>(path: string, body: unknown, options: Options = {}): Promise<T> {
  return api<T>(path, { ...options, method: "PATCH", body: JSON.stringify(body) });
}
