import { FREDOKA, PLANS, TOGGLES, type NotifKey } from "../data";

type Props = {
  toyName: string;
  avHead: string;
  email: string;
  pass: string;
  plan: string;
  notif: Record<NotifKey, boolean>;
  flash: boolean;
  flashMsg: string;
  onSetEmail: (v: string) => void;
  onSetPass: (v: string) => void;
  onPickPlan: (key: string) => void;
  onFlipToggle: (key: NotifKey) => void;
  onSave: () => void;
  onLogout: () => void;
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

export function Profile({ toyName, avHead, email, pass, plan, notif, flash, flashMsg, onSetEmail, onSetPass, onPickPlan, onFlipToggle, onSave, onLogout }: Props) {
  return (
    <div data-screen-label="Profile" style={{ maxWidth: 1060, margin: "0 auto" }}>
      {/* profile banner */}
      <div style={{ background: "#4FB0E5", border: "4px solid #2E2620", borderRadius: 24, padding: "20px 26px", marginBottom: 24, display: "flex", alignItems: "center", gap: 16, boxShadow: "0 8px 0 #2C7CB0" }}>
        <div style={{ width: 52, height: 52, flex: "none", background: avHead, border: "3px solid #2E2620", borderRadius: 14, boxShadow: "0 4px 0 #2E2620", position: "relative" }}>
          <span style={{ position: "absolute", top: 14, left: 12, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" }} />
          <span style={{ position: "absolute", top: 14, right: 12, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" }} />
          <span style={{ position: "absolute", top: 28, left: "50%", transform: "translateX(-50%)", width: 16, height: 8, border: "2px solid #2E2620", borderTop: 0, borderRadius: "0 0 9px 9px" }} />
        </div>
        <div>
          <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 24, margin: 0, color: "#fff" }}>{toyName}</h1>
          <p style={{ margin: "2px 0 0", fontSize: 13, color: "#E6F4FD", fontWeight: 700 }}>TRAINEE TOY · No. 0471</p>
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
            <label style={labelStyle}>Email</label>
            <input className="acct-input" value={email} onChange={(e) => onSetEmail(e.target.value)} type="email" style={inputStyle} />
          </div>
          <div>
            <label style={labelStyle}>Password</label>
            <input className="acct-input" value={pass} onChange={(e) => onSetPass(e.target.value)} type="password" placeholder="••••••••" style={inputStyle} />
          </div>
        </div>

        {/* plans */}
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, margin: "24px 0 10px" }}>Subscription tier</div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 14 }} className="acad-plan-grid">
          {PLANS.map((p) => {
            const on = plan === p.key;
            return (
              <button
                key={p.key}
                className="tap"
                onClick={() => onPickPlan(p.key)}
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
              </button>
            );
          })}
        </div>

        {/* notifications */}
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, margin: "24px 0 10px" }}>Notifications</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {TOGGLES.map((t) => {
            const on = notif[t.key];
            return (
              <button key={t.key} className="tap" onClick={() => onFlipToggle(t.key)} style={{ display: "flex", alignItems: "center", gap: 13, width: "100%", textAlign: "left", background: "#FCF6E9", border: "3px solid #2E2620", borderRadius: 16, padding: "12px 15px" }}>
                <span style={{ width: 44, height: 26, flex: "none", border: "3px solid #2E2620", borderRadius: 14, position: "relative", transition: ".15s", background: on ? "#6FBF73" : "#E4D6B8" }}>
                  <span style={{ position: "absolute", top: 2, left: on ? 20 : 2, width: 16, height: 16, background: "#fff", border: "2px solid #2E2620", borderRadius: "50%", transition: ".15s" }} />
                </span>
                <span style={{ flex: 1, fontWeight: 700, fontSize: 14, color: "#5C4A3C" }}>{t.label}</span>
              </button>
            );
          })}
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 26, flexWrap: "wrap" }}>
          <button className="tap" onClick={onSave} style={{ border: "4px solid #2E2620", borderRadius: 16, background: "#4FB0E5", color: "#fff", fontWeight: 700, fontSize: 16, padding: "13px 26px", boxShadow: "0 6px 0 #2E2620", fontFamily: FREDOKA }}>
            Save account
          </button>
          <button className="tap" onClick={onLogout} style={{ border: "4px solid #2E2620", borderRadius: 16, background: "#fff", color: "#D8443D", fontWeight: 700, fontSize: 16, padding: "13px 26px", boxShadow: "0 6px 0 #EFCFCF", fontFamily: FREDOKA }}>
            Log out
          </button>
          {flash && <span style={{ fontWeight: 800, fontSize: 14, color: "#2C6E9C", animation: "pop .35s ease both" }}>{flashMsg}</span>}
        </div>
      </section>
    </div>
  );
}
