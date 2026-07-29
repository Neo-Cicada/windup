"use client";

import { useState } from "react";
import { FREDOKA } from "../data";
import type { Duel } from "@/lib/types";

type Props = {
  /** A challenge already open and waiting for someone to accept, if there is one. */
  waiting: Duel | null;
  pending: boolean;
  error: string | null;
  onCreate: () => void;
  onJoin: (code: string) => void;
  onCancel: () => void;
};

const CARD = {
  background: "#FBF4E4",
  border: "4px solid #2E2620",
  borderRadius: 22,
  padding: 26,
  boxShadow: "0 8px 0 #2E2620",
} as const;

export function DuelLobby({ waiting, pending, error, onCreate, onJoin, onCancel }: Props) {
  const [code, setCode] = useState("");
  const [copied, setCopied] = useState(false);

  function copyLink() {
    if (waiting === null) return;
    const url = `${window.location.origin}${waiting.invite_path}`;
    navigator.clipboard
      .writeText(url)
      .then(() => setCopied(true))
      .catch(() => setCopied(false));
  }

  if (waiting !== null) {
    return (
      <div data-screen-label="Duel" style={{ maxWidth: 720, margin: "0 auto" }}>
        <div style={{ ...CARD, textAlign: "center" }}>
          <div style={{ fontSize: 11, fontWeight: 800, color: "#B0794A", letterSpacing: 2 }}>
            WAITING FOR A CHALLENGER
          </div>
          <div
            className="acad-duel-code"
            style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 52, letterSpacing: 8, color: "#EF5B54", margin: "10px 0 4px" }}
          >
            {waiting.code}
          </div>
          <p style={{ margin: "0 0 20px", color: "#7A6A57", fontSize: 13, fontWeight: 700 }}>
            Send this to another toy. The clock starts the moment they accept — and neither
            of you sees the problems until then.
          </p>

          <div style={{ display: "flex", justifyContent: "center", gap: 12, flexWrap: "wrap" }}>
            <button
              className="tap"
              onClick={copyLink}
              style={{ border: "4px solid #2E2620", borderRadius: 18, background: "#F7C948", color: "#2E2620", fontWeight: 700, fontSize: 16, padding: "13px 26px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA }}
            >
              {copied ? "Link copied!" : "Copy invite link"}
            </button>
            <button
              className="tap"
              onClick={onCancel}
              disabled={pending}
              style={{ border: "4px solid #C9B79A", borderRadius: 18, background: "transparent", color: "#7A6A57", fontWeight: 700, fontSize: 16, padding: "13px 22px", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
            >
              Call it off
            </button>
          </div>

          {error && <ErrorBanner message={error} />}

          <div style={{ marginTop: 22, display: "flex", justifyContent: "center", gap: 8, alignItems: "center" }}>
            <span style={{ display: "inline-block", width: 10, height: 10, borderRadius: "50%", background: "#6FBF73", animation: "pop 1.2s ease-in-out infinite" }} />
            <span style={{ fontSize: 12, fontWeight: 800, color: "#7A6A57" }}>
              Listening for a challenger…
            </span>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div data-screen-label="Duel" style={{ maxWidth: 860, margin: "0 auto" }}>
      <div className="acad-duel-lobby" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <div style={{ ...CARD, textAlign: "center" }}>
          <div style={{ fontSize: 34 }}>⚔️</div>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 22, margin: "6px 0 8px", color: "#2E2620" }}>
            Open a challenge
          </h2>
          <p style={{ margin: "0 0 20px", color: "#7A6A57", fontSize: 13, fontWeight: 700, lineHeight: 1.5 }}>
            You&apos;ll get a code to share. Same problems, same clock — first to fix them
            all takes it.
          </p>
          <button
            className="tap"
            onClick={onCreate}
            disabled={pending}
            style={{ border: "4px solid #2E2620", borderRadius: 18, background: "#EF5B54", color: "#fff", fontWeight: 700, fontSize: 17, padding: "13px 30px", boxShadow: "0 5px 0 #A9302B", fontFamily: FREDOKA, opacity: pending ? 0.7 : 1 }}
          >
            {pending ? "Winding…" : "Start a duel"}
          </button>
        </div>

        <div style={{ ...CARD, textAlign: "center" }}>
          <div style={{ fontSize: 34 }}>🎟️</div>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 22, margin: "6px 0 8px", color: "#2E2620" }}>
            Got a code?
          </h2>
          <p style={{ margin: "0 0 16px", color: "#7A6A57", fontSize: 13, fontWeight: 700, lineHeight: 1.5 }}>
            Type the six letters a friend sent you.
          </p>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (code.trim()) onJoin(code);
            }}
            style={{ display: "flex", flexDirection: "column", gap: 12, alignItems: "center" }}
          >
            <input
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="ABC234"
              maxLength={8}
              aria-label="Duel code"
              style={{ width: "100%", maxWidth: 240, textAlign: "center", fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, letterSpacing: 6, padding: "10px 12px", border: "4px solid #2E2620", borderRadius: 14, background: "#fff", color: "#2E2620" }}
            />
            <button
              className="tap"
              type="submit"
              disabled={pending || code.trim().length === 0}
              style={{ border: "4px solid #2E2620", borderRadius: 18, background: "#4FB0E5", color: "#fff", fontWeight: 700, fontSize: 17, padding: "13px 30px", boxShadow: "0 5px 0 #2C7BA6", fontFamily: FREDOKA, opacity: pending || !code.trim() ? 0.6 : 1 }}
            >
              Accept
            </button>
          </form>
        </div>
      </div>

      {error && <ErrorBanner message={error} />}
    </div>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      role="alert"
      style={{ margin: "20px auto 0", maxWidth: 520, background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#B4342D" }}
    >
      {message}
    </div>
  );
}
