"use client";

import { useState } from "react";
import { FREDOKA, TOGGLES, type NotifKey } from "../data";
import type { PlanOption, User } from "@/lib/types";

export type AccountValues = {
  toyName: string;
  email: string;
  currentPassword: string;
  newPassword: string;
  notif: Record<NotifKey, boolean>;
};

type Props = {
  user: User;
  plans: PlanOption[];
  saving: boolean;
  flash: string | null;
  error: string | null;
  /** Resolves true when the save stuck, so the password fields can be wiped. */
  onSave: (values: AccountValues) => Promise<boolean>;
  onLogout: () => void;
  onEdit: () => void;
};

const labelStyle = { display: "block", fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, marginBottom: 8 } as const;
const inputStyle = {
  width: "100%",
  border: "3px solid #2E2620",
  borderRadius: 14,
  background: "#FCF6E9",
  padding: "11px 14px",
  fontSize: 15,
  fontWeight: 600,
  color: "#3A2E27",
} as const;
const hintStyle = { margin: "6px 0 0", fontSize: 11.5, fontWeight: 700, color: "#9B7B5B" } as const;

export function Profile({ user, plans, saving, flash, error, onSave, onLogout, onEdit }: Props) {
  // The form is seeded from the toy on mount — leaving the screen and coming back
  // re-seeds it from whatever the server last confirmed.
  const [toyName, setToyName] = useState(user.toy_name);
  const [email, setEmail] = useState(user.email);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [notif, setNotif] = useState<Record<NotifKey, boolean>>(user.notifications);
  const [planNote, setPlanNote] = useState<string | null>(null);

  const credentialChange = email.trim().toLowerCase() !== user.email || newPassword.length > 0;

  function edited() {
    setPlanNote(null);
    onEdit();
  }

  async function handleSave() {
    const saved = await onSave({ toyName, email, currentPassword, newPassword, notif });
    if (saved) {
      setCurrentPassword("");
      setNewPassword("");
    }
  }

  function pickPlan(key: string) {
    setPlanNote(
      key === user.plan
        ? null
        : "Tier changes need a trip to the till — Sprocket hasn't built the checkout yet."
    );
  }

  return (
    <div data-screen-label="Profile" style={{ maxWidth: 1060, margin: "0 auto" }}>
      {/* profile banner */}
      <div style={{ background: "#4FB0E5", border: "4px solid #2E2620", borderRadius: 24, padding: "20px 26px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16, boxShadow: "0 8px 0 #2C7CB0" }}>
        <div style={{ width: 52, height: 52, flex: "none", background: user.avatar.head, border: "3px solid #2E2620", borderRadius: 14, boxShadow: "0 4px 0 #2E2620", position: "relative" }}>
          <span style={{ position: "absolute", top: 14, left: 12, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" }} />
          <span style={{ position: "absolute", top: 14, right: 12, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" }} />
          <span style={{ position: "absolute", top: 28, left: "50%", transform: "translateX(-50%)", width: 16, height: 8, border: "2px solid #2E2620", borderTop: 0, borderRadius: "0 0 9px 9px" }} />
        </div>
        <div>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 24, margin: 0, color: "#fff" }}>{user.toy_name}</h1>
          <p style={{ margin: "2px 0 0", fontSize: 13, color: "#E6F4FD", fontWeight: 700 }}>TRAINEE TOY · No. {user.trainee_no}</p>
        </div>
      </div>

      {/* account panel */}
      <section style={{ background: "#fff", border: "4px solid #2E2620", borderRadius: 24, padding: 26, boxShadow: "0 8px 0 #E0CBA0" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 6 }}>
          <div style={{ width: 34, height: 34, flex: "none", background: "#4FB0E5", border: "3px solid #2E2620", borderRadius: 10, boxShadow: "0 3px 0 #2E2620" }} />
          <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 20, margin: 0 }}>Account</h2>
        </div>
        <p style={{ margin: "0 0 22px", fontSize: 13, color: "#9B7B5B", fontWeight: 700 }}>Your login details and plan. Keep them safe from the humans.</p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "20px 24px" }} className="acad-acct-grid">
          <div>
            <label style={labelStyle} htmlFor="acct-toy-name">Toy name</label>
            <input
              id="acct-toy-name"
              className="acct-input"
              value={toyName}
              onChange={(e) => { setToyName(e.target.value); edited(); }}
              maxLength={60}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle} htmlFor="acct-email">Email</label>
            <input
              id="acct-email"
              className="acct-input"
              value={email}
              onChange={(e) => { setEmail(e.target.value); edited(); }}
              type="email"
              autoComplete="email"
              style={inputStyle}
            />
          </div>
          <div>
            <label style={labelStyle} htmlFor="acct-new-password">New password</label>
            <input
              id="acct-new-password"
              className="acct-input"
              value={newPassword}
              onChange={(e) => { setNewPassword(e.target.value); edited(); }}
              type="password"
              autoComplete="new-password"
              placeholder="Leave blank to keep it"
              style={inputStyle}
            />
            <p style={hintStyle}>At least 8 characters.</p>
          </div>
          <div>
            <label style={labelStyle} htmlFor="acct-current-password">Current password</label>
            <input
              id="acct-current-password"
              className="acct-input"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              style={{ ...inputStyle, borderColor: credentialChange && !currentPassword ? "#EF5B54" : "#2E2620" }}
            />
            <p style={hintStyle}>
              {credentialChange
                ? "Required — changing an email or password re-checks who you are."
                : "Only needed when you change your email or password."}
            </p>
          </div>
        </div>

        {/* plans */}
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, margin: "24px 0 10px" }}>Subscription tier</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }} className="acad-plan-grid">
          {plans.map((p) => {
            const on = user.plan === p.key;
            return (
              <button
                key={p.key}
                className="tap"
                onClick={() => pickPlan(p.key)}
                style={{
                  textAlign: "center",
                  border: "3px solid #2E2620",
                  borderRadius: 16,
                  padding: "14px 10px",
                  background: on ? "#EAF6FD" : "#FCF6E9",
                  boxShadow: on ? "0 4px 0 #C9DEEC" : "0 4px 0 #E0CBA0",
                  outline: on ? "3px solid #4FB0E5" : "none",
                  outlineOffset: on ? 2 : 0,
                }}
              >
                <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 16 }}>{p.name}</div>
                <div style={{ fontSize: 12, fontWeight: 800, color: on ? "#2C6E9C" : "#B0794A" }}>{p.price}</div>
                <div style={{ fontSize: 11, fontWeight: 700, color: "#9B7B5B", marginTop: 4 }}>{p.perk}</div>
                {on && <div style={{ fontSize: 10, fontWeight: 800, color: "#4C7A2F", marginTop: 6 }}>CURRENT</div>}
              </button>
            );
          })}
        </div>
        {planNote && (
          <p style={{ margin: "10px 0 0", fontSize: 12, fontWeight: 700, color: "#A9761F" }}>{planNote}</p>
        )}

        {/* notifications */}
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, margin: "24px 0 10px" }}>Notifications</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {TOGGLES.map((t) => {
            const on = notif[t.key];
            return (
              <button key={t.key} className="tap" onClick={() => { setNotif((s) => ({ ...s, [t.key]: !s[t.key] })); edited(); }} style={{ display: "flex", alignItems: "center", gap: 13, width: "100%", textAlign: "left", background: "#FCF6E9", border: "3px solid #2E2620", borderRadius: 16, padding: "12px 15px" }}>
                <span style={{ width: 44, height: 26, flex: "none", border: "3px solid #2E2620", borderRadius: 14, position: "relative", transition: ".15s", background: on ? "#6FBF73" : "#E4D6B8" }}>
                  <span style={{ position: "absolute", top: 2, left: on ? 20 : 2, width: 16, height: 16, background: "#fff", border: "2px solid #2E2620", borderRadius: "50%", transition: ".15s" }} />
                </span>
                <span style={{ flex: 1, fontWeight: 700, fontSize: 14, color: "#5C4A3C" }}>{t.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 26, flexWrap: "wrap" }}>
          <button
            className="tap"
            onClick={handleSave}
            disabled={saving}
            style={{ border: "4px solid #2E2620", borderRadius: 16, background: "#4FB0E5", color: "#fff", fontWeight: 700, fontSize: 16, padding: "13px 26px", boxShadow: "0 6px 0 #2E2620", fontFamily: FREDOKA, opacity: saving ? 0.7 : 1 }}
          >
            {saving ? "Tightening screws…" : "Save account"}
          </button>
          <button className="tap" onClick={onLogout} style={{ border: "4px solid #2E2620", borderRadius: 16, background: "#fff", color: "#D8443D", fontWeight: 700, fontSize: 16, padding: "13px 26px", boxShadow: "0 6px 0 #EFCFCF", fontFamily: FREDOKA }}>
            Log out
          </button>
          {flash && <span style={{ fontWeight: 800, fontSize: 14, color: "#2C6E9C", animation: "pop .35s ease both" }}>{flash}</span>}
          {error && <span style={{ fontWeight: 800, fontSize: 14, color: "#B4342D", animation: "pop .35s ease both" }} role="alert">{error}</span>}
        </div>
      </section>
    </div>
  );
}
