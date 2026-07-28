"use client";

import type { CSSProperties } from "react";
import { FEATURES, STATS, STEPS, FREDOKA } from "./data";
import { PushButton } from "./PushButton";

const abs = (s: CSSProperties): CSSProperties => ({ position: "absolute", ...s });

/** Green/yellow wind-up clock toy that floats in the hero shelf. */
function HeroAvatar() {
  return (
    <div style={abs({ left: 44, top: 60, width: 150, height: 170, animation: "floaty 4s ease-in-out infinite" })}>
      <div style={abs({ bottom: -4, left: "50%", transform: "translateX(-50%)", width: 110, height: 16, background: "rgba(46,38,32,.16)", borderRadius: "50%" })} />
      <div style={abs({ bottom: 8, left: "50%", transform: "translateX(-50%)", width: 110, height: 78, background: "#6FBF73", border: "4px solid #2E2620", borderRadius: 24 })} />
      <div style={abs({ bottom: 24, left: "50%", transform: "translateX(-50%)", width: 50, height: 48, background: "#EAF7D9", border: "4px solid #2E2620", borderRadius: 13 })} />
      <div style={abs({ top: 8, left: "50%", transform: "translateX(-50%)", width: 98, height: 88, background: "#F7C948", border: "4px solid #2E2620", borderRadius: 30 })} />
      <div style={abs({ top: 0, left: 26, width: 22, height: 22, background: "#EF5B54", border: "4px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 0, right: 26, width: 22, height: 22, background: "#EF5B54", border: "4px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 42, left: 36, width: 14, height: 14, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 42, right: 36, width: 14, height: 14, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 58, left: 28, width: 15, height: 10, background: "#F4A0A0", borderRadius: "50%", opacity: 0.85 })} />
      <div style={abs({ top: 58, right: 28, width: 15, height: 10, background: "#F4A0A0", borderRadius: "50%", opacity: 0.85 })} />
      <div style={abs({ top: 60, left: "50%", transform: "translateX(-50%)", width: 28, height: 14, border: "3px solid #2E2620", borderTop: 0, borderRadius: "0 0 15px 15px" })} />
    </div>
  );
}

/** Blue robot "Sprocket" with a spinning wind-up key. */
function HeroSprocket() {
  return (
    // Hidden on the narrowest screens (see `.hero-sprocket`), where the shelf isn't
    // wide enough for two toys to stand on it without overlapping.
    <div className="hero-sprocket" style={abs({ right: 40, top: 96, width: 120, height: 150, animation: "floaty2 3.4s ease-in-out infinite" })}>
      <div style={abs({ bottom: -2, left: "50%", transform: "translateX(-50%)", width: 96, height: 14, background: "rgba(46,38,32,.16)", borderRadius: "50%" })} />
      <div style={abs({ top: 4, left: "50%", transform: "translateX(-50%)", width: 10, height: 20, background: "#B0794A", border: "2px solid #2E2620" })} />
      <div style={abs({ top: -6, left: "50%", transform: "translateX(-50%)", width: 15, height: 15, background: "#EF5B54", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 18, left: "50%", transform: "translateX(-50%)", width: 88, height: 70, background: "#9FCFEC", border: "4px solid #2E2620", borderRadius: 20 })} />
      <div style={abs({ top: 38, left: 24, width: 20, height: 20, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 38, right: 24, width: 20, height: 20, background: "#fff", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 44, left: 31, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 44, right: 31, width: 7, height: 7, background: "#2E2620", borderRadius: "50%" })} />
      <div style={abs({ top: 66, left: "50%", transform: "translateX(-50%)", width: 26, height: 7, background: "#2E2620", borderRadius: 4 })} />
      <div style={abs({ bottom: 8, left: "50%", transform: "translateX(-50%)", width: 70, height: 52, background: "#EF5B54", border: "4px solid #2E2620", borderRadius: 14 })} />
      <div style={abs({ bottom: 20, left: "50%", transform: "translateX(-50%)", width: 26, height: 26, background: "#F7C948", border: "3px solid #2E2620", borderRadius: "50%" })} />
      <div style={abs({ bottom: 22, right: -10, width: 24, height: 24, border: "3px solid #2E2620", borderRadius: "50%", animation: "spin 3s linear infinite", background: "#C9A96A" })}>
        <div style={abs({ top: "50%", left: "50%", width: 24, height: 4, background: "#2E2620", transform: "translate(-50%,-50%)", borderRadius: 2 })} />
      </div>
    </div>
  );
}

function LogoMark() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 11, flex: "none" }}>
      <div style={{ width: 42, height: 42, background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 12, position: "relative", boxShadow: "0 4px 0 #2E2620" }}>
        <div style={abs({ inset: 8, border: "3px solid #FBE7C6", borderRadius: 6 })} />
        <div style={abs({ top: "50%", left: "50%", width: 9, height: 9, transform: "translate(-50%,-50%)", background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" })} />
      </div>
      <div style={{ lineHeight: 1 }}>
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 16 }}>WINDUP</div>
        <div style={{ fontFamily: FREDOKA, fontWeight: 500, fontSize: 10, letterSpacing: 3, color: "#B0794A" }}>ACADEMY</div>
      </div>
    </div>
  );
}

type Props = {
  onLogin: () => void;
  onSignup: () => void;
};

export function Landing({ onLogin, onSignup }: Props) {
  return (
    <div>
      {/* NAV */}
      <nav className="pub-nav" style={{ position: "sticky", top: 0, zIndex: 50, display: "flex", alignItems: "center", gap: 16, padding: "16px 40px", background: "rgba(243,227,195,.82)", backdropFilter: "blur(8px)", borderBottom: "3px solid #2E2620" }}>
        <LogoMark />
        <div style={{ flex: 1 }} />
        <div className="nav-links">
          <a href="#feat">Features</a>
          <a href="#how">How it works</a>
        </div>
        <PushButton onClick={onLogin} bg="#fff" color="#3A2E27" shadow="#2E2620" style={{ borderRadius: 13, fontSize: 14, padding: "9px 18px", borderWidth: 3 }}>
          Log in
        </PushButton>
        <PushButton onClick={onSignup} bg="#EF5B54" color="#fff" shadow="#2E2620" style={{ borderRadius: 13, fontSize: 14, padding: "9px 18px", borderWidth: 3 }}>
          Sign up free
        </PushButton>
      </nav>

      {/* HERO */}
      <header className="hero-grid pub-section" style={{ maxWidth: 1180, margin: "0 auto", padding: "56px 40px 40px", display: "grid", gridTemplateColumns: "1.05fr .95fr", gap: 40, alignItems: "center" }}>
        <div>
          <h1 className="pub-h1" style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 56, lineHeight: 1.02, margin: "0 0 18px" }}>
            Ace your coding interview.
            <br />
            <span style={{ color: "#EF5B54" }}>One toy at a time.</span>
          </h1>
          <p style={{ margin: "0 0 28px", fontSize: 17, lineHeight: 1.55, color: "#5C4A3C", maxWidth: 500 }}>
            A secret training academy run by toys. Fix broken gadgets, climb the shelves, battle boss toys, and earn merit badges, all while mastering real data-structure and algorithm patterns.
          </p>
          <div style={{ display: "flex", gap: 14, flexWrap: "wrap", marginBottom: 26 }}>
            <PushButton onClick={onSignup} bg="#6FBF73" color="#173d19" shadow="#2E2620" style={{ borderRadius: 17, fontSize: 17, padding: "14px 28px", borderWidth: 4, boxShadowY: 6 }}>
              Start playing free
            </PushButton>
            <PushButton onClick={onLogin} bg="#fff" color="#3A2E27" shadow="#E0CBA0" style={{ borderRadius: 17, fontSize: 17, padding: "14px 28px", borderWidth: 4, boxShadowY: 6 }}>
              I have an account
            </PushButton>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 14, fontSize: 13, fontWeight: 700, color: "#8B7358" }}>
            <div style={{ display: "flex" }}>
              <span style={{ width: 32, height: 32, background: "#6FBF73", border: "3px solid #2E2620", borderRadius: 9 }} />
              <span style={{ width: 32, height: 32, background: "#4FB0E5", border: "3px solid #2E2620", borderRadius: 9, marginLeft: -10 }} />
              <span style={{ width: 32, height: 32, background: "#F7C948", border: "3px solid #2E2620", borderRadius: 9, marginLeft: -10 }} />
              <span style={{ width: 32, height: 32, background: "#8B6FD6", border: "3px solid #2E2620", borderRadius: 9, marginLeft: -10 }} />
            </div>
            Join <b style={{ color: "#3A2E27" }}>40,000+</b> toys already in training
          </div>
        </div>

        {/* hero illustration: shelf with toys */}
        <div className="hero-art" style={{ position: "relative", height: 420 }}>
          <div style={{ position: "absolute", inset: 0, background: "#FBF4E4", border: "4px solid #2E2620", borderRadius: 28, boxShadow: "0 12px 0 #E0CBA0", overflow: "hidden" }}>
            <div style={abs({ top: -30, right: -30, width: 150, height: 150, background: "#FDF0CE", borderRadius: "50%" })} />
            <HeroAvatar />
            <HeroSprocket />
            {/* speech bubble */}
            <div style={abs({ top: 30, right: 30, background: "#fff", border: "3px solid #2E2620", borderRadius: 14, padding: "9px 12px", fontSize: 12, fontWeight: 700, color: "#2C6E9C", boxShadow: "0 4px 0 #E0CBA0" })}>
              Welcome, recruit!
            </div>
            {/* shelf */}
            <div style={abs({ left: 24, right: 24, bottom: 40, height: 16, background: "repeating-linear-gradient(90deg,#C9A96A 0 18px,#BE9C5C 18px 21px)", border: "4px solid #2E2620", borderRadius: 9 })} />
            {/* charge chip */}
            <div style={abs({ left: 34, bottom: 66, display: "flex", alignItems: "center", gap: 8, background: "#fff", border: "3px solid #2E2620", borderRadius: 12, padding: "6px 11px", boxShadow: "0 4px 0 #E0CBA0", animation: "floaty 5s ease-in-out infinite" })}>
              <span style={{ width: 20, height: 20, background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%", animation: "spin 5s linear infinite" }} />
              <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 13 }}>+40 charge</span>
            </div>
          </div>
        </div>
      </header>

      {/* STATS STRIP */}
      <section className="pub-section" style={{ maxWidth: 1180, margin: "0 auto", padding: "14px 40px 30px" }}>
        <div className="stats-grid acad-card" style={{ background: "#2E2620", borderRadius: 22, padding: "26px 30px", display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 20, textAlign: "center" }}>
          {STATS.map((s) => (
            <div key={s.label}>
              <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 32, color: s.color }}>{s.value}</div>
              <div style={{ fontSize: 12, fontWeight: 800, color: "#D6C7B4" }}>{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section id="feat" className="pub-section" style={{ maxWidth: 1180, margin: "0 auto", padding: "40px 40px" }}>
        <h2 className="pub-h2" style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 38, textAlign: "center", margin: "0 0 8px" }}>Practice that feels like playtime</h2>
        <p style={{ textAlign: "center", fontSize: 16, color: "#8B7358", fontWeight: 700, margin: "0 0 36px" }}>Every serious interview skill, wrapped in something you actually want to open.</p>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(min(250px,100%),1fr))", gap: 22 }}>
          {FEATURES.map((f) => (
            <div key={f.title} style={{ background: "#fff", border: "4px solid #2E2620", borderRadius: 22, padding: 24, boxShadow: "0 8px 0 #E0CBA0" }}>
              <div style={{ width: 52, height: 52, background: f.color, border: "4px solid #2E2620", borderRadius: 15, boxShadow: "0 5px 0 #2E2620" }} />
              <h3 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 20, margin: "16px 0 8px" }}>{f.title}</h3>
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "#6B5A4A" }}>{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="pub-section" style={{ maxWidth: 1180, margin: "0 auto", padding: "30px 40px 50px" }}>
        <h2 className="pub-h2" style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 38, textAlign: "center", margin: "0 0 36px" }}>Three steps to Interview Ready</h2>
        <div className="steps-grid" style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 22 }}>
          {STEPS.map((s) => (
            <div key={s.n} style={{ textAlign: "center", background: "#FBF4E4", border: "4px solid #2E2620", borderRadius: 22, padding: "28px 22px", boxShadow: "0 8px 0 #E0CBA0" }}>
              <div style={{ width: 56, height: 56, margin: "0 auto 16px", background: s.color, border: "4px solid #2E2620", borderRadius: "50%", boxShadow: "0 4px 0 #2E2620", fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, color: "#2E2620", display: "flex", alignItems: "center", justifyContent: "center" }}>{s.n}</div>
              <h3 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 8px" }}>{s.title}</h3>
              <p style={{ margin: 0, fontSize: 14, lineHeight: 1.5, color: "#6B5A4A" }}>{s.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FINAL CTA */}
      <section id="join" className="pub-section" style={{ maxWidth: 1180, margin: "0 auto", padding: "0 40px 60px" }}>
        <div className="acad-card" style={{ background: "#EF5B54", border: "4px solid #2E2620", borderRadius: 28, padding: 48, textAlign: "center", boxShadow: "0 12px 0 #A9302B", position: "relative", overflow: "hidden" }}>
          <div style={abs({ top: -40, left: -40, width: 160, height: 160, background: "rgba(255,255,255,.12)", borderRadius: "50%" })} />
          <div style={abs({ bottom: -50, right: -30, width: 180, height: 180, background: "rgba(255,255,255,.10)", borderRadius: "50%" })} />
          <h2 className="pub-h2" style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 40, color: "#fff", margin: "0 0 12px", position: "relative" }}>The toybox is open. Come play.</h2>
          <p style={{ color: "#FFE3E1", fontSize: 16, fontWeight: 700, margin: "0 0 28px", position: "relative" }}>Every shelf, every quest, every boss. No batteries required.</p>
          <PushButton onClick={onSignup} bg="#F7C948" color="#2E2620" shadow="#2E2620" style={{ borderRadius: 18, fontSize: 19, padding: "16px 40px", borderWidth: 4, boxShadowY: 6, position: "relative" }}>
            Create your toy
          </PushButton>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="pub-footer" style={{ borderTop: "3px solid #2E2620", padding: "26px 40px", display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap", fontSize: 13, fontWeight: 700, color: "#8B7358" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <div style={{ width: 30, height: 30, background: "#EF5B54", border: "3px solid #2E2620", borderRadius: 9 }} />
          <span style={{ fontFamily: FREDOKA, fontWeight: 700, color: "#3A2E27" }}>Windup Academy</span>
        </div>
        <div style={{ flex: 1 }} />
        <span>© 2026 · Made with wind-up love · Not affiliated with any real toys</span>
      </footer>
    </div>
  );
}
