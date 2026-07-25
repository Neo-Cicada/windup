"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { api, clearTokens, getAccessToken, onSessionExpired, post, setTokens } from "./api";
import type { TokenPair, User } from "./types";

/** "loading" until the stored token has been checked against the API. */
export type AuthStatus = "loading" | "authed" | "anon";

type AuthValue = {
  status: AuthStatus;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  signup: (toyName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  /** Replace the cached toy after a profile save. */
  setUser: (user: User) => void;
};

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  // Bootstrap: a stored token is only a claim until /me confirms it. Both branches
  // resolve asynchronously so the first paint is always the same "loading" markup,
  // server and client alike.
  useEffect(() => {
    let cancelled = false;
    const bootstrap = getAccessToken() ? api<User>("/me") : Promise.resolve(null);
    bootstrap
      .then((me) => {
        if (cancelled) return;
        setUser(me);
        setStatus(me === null ? "anon" : "authed");
      })
      .catch(() => {
        if (cancelled) return;
        clearTokens();
        setUser(null);
        setStatus("anon");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // A refresh that fails mid-session drops us straight back to anonymous.
  useEffect(
    () =>
      onSessionExpired(() => {
        setUser(null);
        setStatus("anon");
      }),
    []
  );

  const adopt = useCallback((pair: TokenPair) => {
    setTokens(pair);
    setUser(pair.user);
    setStatus(pair.user ? "authed" : "anon");
  }, []);

  const login = useCallback(
    async (email: string, password: string) => {
      adopt(await post<TokenPair>("/auth/login", { email, password }, { anon: true }));
    },
    [adopt]
  );

  const signup = useCallback(
    async (toyName: string, email: string, password: string) => {
      adopt(
        await post<TokenPair>("/auth/signup", { toy_name: toyName, email, password }, { anon: true })
      );
    },
    [adopt]
  );

  const logout = useCallback(async () => {
    try {
      await post("/auth/logout");
    } catch {
      // Tokens are stateless — dropping them locally is what logging out means.
    }
    clearTokens();
    setUser(null);
    setStatus("anon");
  }, []);

  const value = useMemo<AuthValue>(
    () => ({ status, user, login, signup, logout, setUser }),
    [status, user, login, signup, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const ctx = useContext(AuthContext);
  if (ctx === null) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
