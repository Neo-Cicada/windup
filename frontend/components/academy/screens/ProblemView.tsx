"use client";

import type { ReactNode } from "react";
import { FREDOKA, MONO, difficultyTone } from "../data";
import type { ChestTier, ProblemDetail } from "@/lib/types";

type Props = {
  problem: ProblemDetail;
  code: string;
  onCodeChange: (code: string) => void;
  /** The tier currently being opened, so its chest can show a pending state. */
  unlocking: ChestTier | null;
  submitting: boolean;
  error: string | null;
  onUnlock: (tier: ChestTier) => void;
  onSubmit: () => void;
};

const card = {
  background: "#fff",
  border: "4px solid #2E2620",
  borderRadius: 24,
  boxShadow: "0 8px 0 #E0CBA0",
} as const;

const codeBlock = {
  fontFamily: MONO,
  fontSize: 13,
  lineHeight: 1.65,
  whiteSpace: "pre-wrap" as const,
  margin: 0,
};

type ChestBtnProps = { color: string; lid: string; title: string; sub: string; pending: boolean; onClick: () => void };

function LockedChest({ color, lid, title, sub, pending, onClick }: ChestBtnProps) {
  return (
    <button
      className="tap"
      onClick={onClick}
      disabled={pending}
      style={{ display: "flex", alignItems: "center", gap: 13, width: "100%", textAlign: "left", background: "#FCF6E9", border: "3px dashed #C9A96A", borderRadius: 16, padding: 14, opacity: pending ? 0.6 : 1 }}
    >
      <span style={{ width: 44, height: 36, flex: "none", background: color, border: "3px solid #2E2620", borderRadius: "8px 8px 6px 6px", position: "relative" }}>
        <span style={{ position: "absolute", top: -6, left: 4, right: 4, height: 12, background: lid, border: "3px solid #2E2620", borderRadius: "8px 8px 0 0" }} />
        <span style={{ position: "absolute", top: 9, left: "50%", transform: "translateX(-50%)", width: 8, height: 8, background: "#F7C948", border: "2px solid #2E2620", borderRadius: "50%" }} />
      </span>
      <div style={{ flex: 1 }}>
        <div style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>{title}</div>
        <div style={{ fontSize: 11, fontWeight: 700, color: "#9B7B5B" }}>{pending ? "Prising the lid off…" : sub}</div>
      </div>
      <span style={{ fontSize: 11, fontWeight: 800, color: "#D8443D" }}>−bonus</span>
    </button>
  );
}

function OpenedChest({ tone, accent, title, children }: { tone: { bg: string; text: string }; accent: string; title: string; children: ReactNode }) {
  return (
    <div style={{ background: tone.bg, border: "3px solid #2E2620", borderRadius: 16, padding: 15, animation: "pop .35s ease both" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
        <span style={{ width: 24, height: 24, background: accent, border: "3px solid #2E2620", borderRadius: 7 }} />
        <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>{title}</span>
        <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 800, color: tone.text }}>OPENED</span>
      </div>
      <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: tone.text, whiteSpace: "pre-wrap" }}>{children}</p>
    </div>
  );
}

export function ProblemView({ problem, code, onCodeChange, unlocking, submitting, error, onUnlock, onSubmit }: Props) {
  const { chests, help_shelf: help } = problem;
  const tone = difficultyTone(problem.difficulty);

  return (
    <div data-screen-label="Problem View" style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 22, maxWidth: 1180, margin: "0 auto", alignItems: "start" }} className="acad-problem">
      {/* LEFT: problem + workspace */}
      <section style={{ display: "flex", flexDirection: "column", gap: 22 }}>
        <div style={{ ...card, padding: 24 }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 18 }}>
            <div style={{ flex: "none", textAlign: "center" }}>
              <div style={{ width: 70, height: 70, background: problem.zone_color, border: "4px solid #2E2620", borderRadius: 18, boxShadow: "0 6px 0 #2E2620", position: "relative" }}>
                <span style={{ position: "absolute", inset: 14, border: "3px dashed #2E2620", borderRadius: 10 }} />
              </div>
              <div style={{ marginTop: 9, fontSize: 10, fontWeight: 800, color: "#B0794A" }}>{problem.weight_label}</div>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: "flex", gap: 8, marginBottom: 8, flexWrap: "wrap" }}>
                <span style={{ background: "#EAF6FD", border: `2px solid ${problem.zone_color}`, color: "#2C6E9C", fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20 }}>
                  {problem.zone_name.toUpperCase()}
                </span>
                <span style={{ background: tone.bg, border: `2px solid ${tone.border}`, color: tone.color, fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20, textTransform: "capitalize" }}>
                  {problem.difficulty}
                </span>
                {problem.solved && (
                  <span style={{ background: "#EAF7D9", border: "2px solid #6FBF73", color: "#4C7A2F", fontWeight: 800, fontSize: 11, padding: "3px 10px", borderRadius: 20 }}>
                    ✓ Already fixed
                  </span>
                )}
              </div>
              <h1 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 26, margin: "0 0 8px" }}>{problem.title}</h1>
              <p style={{ margin: 0, fontSize: 14.5, lineHeight: 1.5, color: "#5C4A3C", whiteSpace: "pre-wrap" }}>{problem.prompt}</p>
            </div>
          </div>
          <div style={{ marginTop: 18, background: "#2E2620", borderRadius: 14, padding: "16px 18px", fontFamily: MONO, fontSize: 13, color: "#EAF7D9", lineHeight: 1.6 }}>
            <div style={{ color: "#F7C948" }}>Example</div>
            <div style={{ whiteSpace: "pre-wrap" }}>Input:&nbsp;&nbsp;{problem.example_input}</div>
            <div style={{ whiteSpace: "pre-wrap" }}>Output: {problem.example_output}</div>
          </div>
        </div>

        <div style={{ ...card, padding: 20 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 17, margin: 0 }}>Your Workbench</h2>
            <span style={{ fontSize: 11, fontWeight: 800, color: "#9B7B5B", textTransform: "capitalize" }}>{problem.language}</span>
          </div>
          <textarea
            value={code}
            onChange={(e) => onCodeChange(e.target.value)}
            spellCheck={false}
            style={{
              width: "100%",
              minHeight: 180,
              resize: "vertical",
              background: "#FBF4E4",
              border: "3px solid #2E2620",
              borderRadius: 14,
              padding: 16,
              fontFamily: MONO,
              fontSize: 13,
              color: "#5C4A3C",
              lineHeight: 1.7,
            }}
          />
          <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
            <button
              className="tap"
              onClick={onSubmit}
              disabled={submitting}
              style={{ border: "3px solid #2E2620", borderRadius: 15, background: "#6FBF73", color: "#173d19", fontWeight: 700, fontSize: 15, padding: "11px 22px", boxShadow: "0 5px 0 #2E2620", fontFamily: FREDOKA, opacity: submitting ? 0.7 : 1 }}
            >
              {submitting ? "Testing the springs…" : "Run & Submit"}
            </button>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 12, fontWeight: 800, color: "#9B7B5B" }}>Unaided bonus:</span>
              <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 15, color: problem.unaided ? "#4C7A2F" : "#B9A98C", textDecoration: problem.unaided ? "none" : "line-through" }}>
                +{problem.unaided_bonus} charge
              </span>
            </div>
          </div>
          {error && (
            <div style={{ marginTop: 14, background: "#FDECEC", border: "3px solid #2E2620", borderRadius: 14, padding: "11px 14px", fontSize: 13, fontWeight: 700, color: "#B4342D" }} role="alert">
              {error}
            </div>
          )}
        </div>
      </section>

      {/* RIGHT: tiered resource panel */}
      <section style={{ ...card, padding: 22 }}>
        <h2 style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 19, margin: "0 0 4px" }}>Help Shelf</h2>
        <p style={{ margin: "0 0 18px", fontSize: 12, color: "#9B7B5B", fontWeight: 700 }}>Open a chest for help — but peeking past the explainer forfeits your unaided bonus.</p>

        {/* Tier 1 always open */}
        <div style={{ background: "#EAF7D9", border: "3px solid #2E2620", borderRadius: 16, padding: 15, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: 8 }}>
            <span style={{ width: 24, height: 24, background: "#6FBF73", border: "3px solid #2E2620", borderRadius: 7 }} />
            <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14 }}>Tier 1 · Pattern Explainer</span>
            <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 800, color: "#4C7A2F" }}>FREE · OPEN</span>
          </div>
          <p style={{ margin: 0, fontSize: 13, lineHeight: 1.5, color: "#4C5A3C", whiteSpace: "pre-wrap" }}>{help.explainer}</p>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          {chests.hint && help.hint !== null ? (
            <OpenedChest tone={{ bg: "#EAF6FD", text: "#2C4A5C" }} accent="#4FB0E5" title="Tier 2 · Hint">
              {help.hint}
            </OpenedChest>
          ) : (
            <LockedChest color="#4FB0E5" lid="#63BCEC" title="Tier 2 · Hint" sub="A nudge in the right direction" pending={unlocking === "hint"} onClick={() => onUnlock("hint")} />
          )}

          {chests.approach && help.approach !== null ? (
            <OpenedChest tone={{ bg: "#FDF3D6", text: "#7A5A2C" }} accent="#E08A3C" title="Tier 3 · Full Approach">
              {help.approach}
            </OpenedChest>
          ) : (
            <LockedChest color="#E08A3C" lid="#EC9C54" title="Tier 3 · Full Approach" sub="Step-by-step walkthrough" pending={unlocking === "approach"} onClick={() => onUnlock("approach")} />
          )}

          {chests.solution && help.solution !== null ? (
            <div style={{ background: "#2E2620", borderRadius: 16, padding: 16, animation: "pop .35s ease both", color: "#EAF7D9" }}>
              <div style={{ color: "#F7C948", fontFamily: FREDOKA, fontWeight: 700, marginBottom: 8 }}>Tier 4 · Full Solution</div>
              <pre style={codeBlock}>{help.solution}</pre>
            </div>
          ) : (
            <LockedChest color="#EF5B54" lid="#F26E68" title="Tier 4 · Full Solution" sub="The complete answer" pending={unlocking === "solution"} onClick={() => onUnlock("solution")} />
          )}
        </div>
      </section>
    </div>
  );
}
