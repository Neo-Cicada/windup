"use client";

import { useState, type CSSProperties } from "react";
import { FREDOKA } from "./data";
import { PushButton } from "./PushButton";

const abs = (s: CSSProperties): CSSProperties => ({ position: "absolute", ...s });

export type AuthMode = "login" | "signup";

export type AuthValues = { toyName: string; email: string; password: string };

/** Cream-outlined Sprocket that waves from the dark brand panel. */
function PanelSprocket() {
  return (
    <div style={{ position: "relative", width: 130, height: 160, animation: "floaty2 3.6s ease-in-out infinite" }}>
      <div style={abs({ top: 4, left: "50%", transform: "translateX(-50%)", width: 10, height: 20, background: "#B0794A", border: "2px solid #F3E3C3" })} />
      <div style={abs({ top: -6, left: "50%", transform: "translateX(-50%)", width: 16, height: 16, background: "#EF5B54", border: "3px solid #F3E3C3", borderRadius: "50%" })} />
      <div style={abs({ top: 20, left: "50%", transform: "translateX(-50%)", width: 94, height: 74, background: "#9FCFEC", border: "4px solid #2E2620", borderRadius: 22, boxShadow: "0 0 0 3px #F3E3C3" })} />
      <div style={abs({ top: 42, left: 26, width: 22, height: 22, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 42, right: 26, width: 22, height: 22, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 49, left: 34, width: 8, height: 8, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 49, right: 34, width: 8, height: 8, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 72, left: "50%", transform: "translateX(-50%)", width: 28, height: 8, background: "#2E2620", borderRadius: 4 })} />
      <div style={abs({ bottom: 8, left: "50%", transform: "translateX(-50%)", width: 76, height: 54, background: "#EF5B54", border: "4px solid #2E2620", borderRadius: 15, boxShadow: "0 0 0 3px #F3E3C3" })} />
      <div style={abs({ bottom: 22, left: "50%", transform: "translateX(-50%)", width: 28, height: 28, background: "#F7C948", border: "3px solid #2E2620", borderRadius: "50%" })} />
    </div>
  );
}

const labelStyle: CSSProperties = { display: "block", fontWeight: 800, fontSize: 13, color: "#5C4A3C", marginBottom: 7 };
const inputStyle: CSSProperties = {
  width: "100%",
  border: "3px solid #2E2620",
  borderRadius: 14,
  background: "#FCF6E9",
  padding: "12px 14px",
  fontSize: 15,
  fontWeight: 600,
  color: "#3A2E27",
  marginBottom: 16,
};

const noticeStyle: CSSProperties = {
  marginTop: 16,
  border: "3px solid #2E2620",
  borderRadius: 14,
  padding: "12px 14px",
  fontSize: 13,
  fontWeight: 700,
  animation: "pop .35s ease both",
};

type Props = {
  mode: AuthMode;
  showWelcome: boolean;
  pending: boolean;
  error: string | null;
  onBack: () => void;
  onSubmit: (values: AuthValues) => void;
  onSwitchMode: () => void;
};

export function Auth({ mode, showWelcome, pending, error, onBack, onSubmit, onSwitchMode }: Props) {
  const isSignup = mode === "signup";
  const isLogin = mode === "login";

  const [toyName, setToyName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [sparePart, setSparePart] = useState(false);

  const panelTitle = isSignup ? "Join the secret academy of toys." : "Welcome back to the playroom.";
  const panelBody = isSignup
    ? "Create your toy, pick a corner, and start turning interview prep into playtime."
    : "Your shelves, streaks and merit badges are exactly where you left them.";
  const formTitle = isSignup ? "Create your toy" : "Log in";
  const formSub = isSignup ? "No batteries required." : "Wind yourself back up.";
  const submitLabel = pending
    ? isSignup
      ? "Unboxing…"
      : "Winding up…"
    : isSignup
      ? "Start playing"
      : "Log in";
  const switchText = isSignup ? "Already a toy?" : "New to the toybox?";
  const switchCta = isSignup ? "Log in" : "Sign up free";
  const welcomeMsg = isSignup
    ? "Your toy is wound up and ready. Welcome to the academy!"
    : "Welcome back! Sprocket kept your shelf warm.";

  return (
    <div className="auth-grid" style={{ minHeight: "100vh", display: "grid", gridTemplateColumns: "1fr 1fr" }}>
      {/* left: brand panel */}
      <div className="auth-brand" style={{ background: "#2E2620", padding: 48, display: "flex", flexDirection: "column", position: "relative", overflow: "hidden" }}>
        <div style={abs({ top: -40, right: -40, width: 200, height: 200, background: "rgba(239,91,84,.22)", borderRadius: "50%" })} />
        <div style={abs({ bottom: -60, left: -30, width: 220, height: 220, background: "rgba(79,176,229,.16)", borderRadius: "50%" })} />
        <div style={{ display: "flex", alignItems: "center", gap: 11, position: "relative" }}>
          <div style={{ width: 42, height: 42, background: "#EF5B54", border: "3px solid #F3E3C3", borderRadius: 12, position: "relative" }}>
            <div style={abs({ inset: 8, border: "3px solid #F3E3C3", borderRadius: 6 })} />
          </div>
          <div style={{ lineHeight: 1, color: "#fff" }}>
            <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 16 }}>WINDUP</div>
            <div style={{ fontFamily: FREDOKA, fontWeight: 500, fontSize: 10, letterSpacing: 3, color: "#C9A96A" }}>ACADEMY</div>
          </div>
        </div>
        <div style={{ margin: "auto 0", position: "relative" }}>
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 34, color: "#fff", lineHeight: 1.1, margin: "0 0 14px", maxWidth: 360 }}>{panelTitle}</h2>
          <p style={{ color: "#D6C7B4", fontSize: 15, lineHeight: 1.55, maxWidth: 340, margin: "0 0 34px" }}>{panelBody}</p>
          <PanelSprocket />
        </div>
        <div style={{ position: "relative", color: "#8B7B63", fontSize: 12, fontWeight: 700 }}>Trusted by 40,000+ toys in training</div>
      </div>

      {/* right: form */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "48px 40px" }}>
        <form
          style={{ width: "100%", maxWidth: 380 }}
          onSubmit={(e) => {
            e.preventDefault();
            if (pending) return;
            onSubmit({ toyName: toyName.trim(), email: email.trim(), password });
          }}
        >
          <button type="button" onClick={onBack} style={{ border: 0, background: "none", color: "#8B7358", fontWeight: 800, fontSize: 13, cursor: "pointer", padding: 0, marginBottom: 24 }}>
            ← Back to playroom
          </button>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 32, margin: "0 0 6px" }}>{formTitle}</h1>
          <p style={{ margin: "0 0 26px", fontSize: 14, color: "#8B7358", fontWeight: 700 }}>{formSub}</p>

          {/* social */}
          <div style={{ display: "flex", flexDirection: "column", gap: 11, marginBottom: 20 }}>
            <PushButton onClick={() => setSparePart(true)} bg="#fff" color="#3A2E27" shadow="#E0CBA0" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 10, borderRadius: 14, fontSize: 14, padding: "11px" }}>
              <span style={{ width: 18, height: 18, background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" }} />
              Continue with a spare part
            </PushButton>
          </div>
          {sparePart && (
            <div style={{ ...noticeStyle, marginTop: 0, marginBottom: 16, background: "#FDF3D6", color: "#8A6420" }}>
              Sprocket hasn&apos;t soldered that spare part on yet — use your email below.
            </div>
          )}
          <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "20px 0", color: "#B0794A", fontWeight: 800, fontSize: 12 }}>
            <span style={{ flex: 1, height: 2, background: "#D9C4A0" }} />
            OR
            <span style={{ flex: 1, height: 2, background: "#D9C4A0" }} />
          </div>

          {/* name (signup only) */}
          {isSignup && (
            <>
              <label style={labelStyle} htmlFor="toy-name">Toy name</label>
              <input
                id="toy-name"
                className="toy-input"
                placeholder="e.g. Bramble"
                value={toyName}
                onChange={(e) => setToyName(e.target.value)}
                required
                maxLength={60}
                style={inputStyle}
              />
            </>
          )}

          <label style={labelStyle} htmlFor="email">Email</label>
          <input
            id="email"
            className="toy-input"
            placeholder="you@playroom.com"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            style={inputStyle}
          />

          <label style={labelStyle} htmlFor="password">Password</label>
          <input
            id="password"
            className="toy-input"
            placeholder="••••••••"
            type="password"
            autoComplete={isSignup ? "new-password" : "current-password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={isSignup ? 8 : 1}
            style={{ ...inputStyle, marginBottom: 10 }}
          />

          {isLogin && (
            <div style={{ textAlign: "right", marginBottom: 18 }}>
              <a href="#" style={{ fontSize: 13, fontWeight: 800, color: "#3E8FC4" }}>Forgot password?</a>
            </div>
          )}
          {isSignup && (
            <div style={{ margin: "6px 0 18px", fontSize: 12, color: "#8B7358", fontWeight: 700 }}>
              At least 8 characters. By signing up you agree to keep the academy a secret from the humans.
            </div>
          )}

          <PushButton type="submit" bg="#6FBF73" color="#173d19" shadow="#2E2620" style={{ width: "100%", borderRadius: 16, fontSize: 17, padding: 14, borderWidth: 4, boxShadowY: 6, opacity: pending ? 0.75 : 1 }}>
            {submitLabel}
          </PushButton>

          {error && (
            <div style={{ ...noticeStyle, background: "#FDECEC", color: "#B4342D" }} role="alert">
              {error}
            </div>
          )}

          {showWelcome && (
            <div style={{ ...noticeStyle, background: "#EAF7D9", color: "#4C7A2F" }}>{welcomeMsg}</div>
          )}

          <div style={{ marginTop: 24, textAlign: "center", fontSize: 14, fontWeight: 700, color: "#8B7358" }}>
            {switchText}{" "}
            <button type="button" onClick={onSwitchMode} style={{ border: 0, background: "none", color: "#EF5B54", fontWeight: 800, fontSize: 14, cursor: "pointer", padding: 0 }}>
              {switchCta}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
