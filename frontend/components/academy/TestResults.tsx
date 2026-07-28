"use client";

import { FREDOKA, MONO } from "./data";
import type { RunCaseResult } from "@/lib/runners";
import type { SubmissionResult } from "@/lib/types";

const codeBlock = {
  fontFamily: MONO,
  fontSize: 12.5,
  lineHeight: 1.6,
  whiteSpace: "pre-wrap" as const,
  wordBreak: "break-word" as const,
  margin: 0,
};

/** Plain JSON, rendered the way the problem prompt writes it. */
function show(value: unknown): string {
  if (value === undefined) return "—";
  return JSON.stringify(value);
}

function Panel({
  tone,
  title,
  badge,
  children,
}: {
  tone: { bg: string; border: string; text: string };
  title: string;
  badge?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      style={{
        marginTop: 16,
        background: tone.bg,
        border: `3px solid ${tone.border}`,
        borderRadius: 16,
        padding: 15,
        animation: "pop .3s ease both",
      }}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 9, marginBottom: children ? 10 : 0 }}>
        <span style={{ fontFamily: FREDOKA, fontWeight: 700, fontSize: 14, color: tone.text }}>
          {title}
        </span>
        {badge !== undefined && (
          <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 800, color: tone.text }}>
            {badge}
          </span>
        )}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value, mono = true }: { label: string; value: string; mono?: boolean }) {
  return (
    <div style={{ display: "flex", gap: 10, marginTop: 6, alignItems: "baseline" }}>
      <span
        style={{
          fontSize: 11,
          fontWeight: 800,
          color: "#9B7B5B",
          minWidth: 62,
          flex: "none",
          textTransform: "uppercase",
        }}
      >
        {label}
      </span>
      <span style={mono ? codeBlock : { fontSize: 13, margin: 0 }}>{value}</span>
    </div>
  );
}

/** Little pass/fail pip per case. */
function Pips({ results }: { results: { passed: boolean }[] }) {
  return (
    <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
      {results.map((r, i) => (
        <span
          key={i}
          title={`Case ${i + 1}: ${r.passed ? "held" : "jammed"}`}
          style={{
            width: 18,
            height: 18,
            borderRadius: 6,
            border: "2px solid #2E2620",
            background: r.passed ? "#6FBF73" : "#EF5B54",
            display: "inline-block",
          }}
        />
      ))}
    </div>
  );
}

// ---- local run (the "Run" button) -------------------------------------------
export function LocalRunResults({ results }: { results: RunCaseResult[] }) {
  const passed = results.filter((r) => r.passed).length;
  const allGood = passed === results.length;
  const firstBad = results.find((r) => !r.passed);

  const tone = allGood
    ? { bg: "#EAF7D9", border: "#6FBF73", text: "#4C7A2F" }
    : { bg: "#FDF3D6", border: "#E08A3C", text: "#7A5A2C" };

  return (
    <Panel
      tone={tone}
      title={allGood ? "Examples all held" : "Examples jammed"}
      badge={`${passed}/${results.length} · TRIED HERE, NOT GRADED`}
    >
      <Pips results={results} />
      {firstBad !== undefined && (
        <div style={{ marginTop: 12, borderTop: "2px dashed #C9A96A", paddingTop: 10 }}>
          <Row label="Input" value={firstBad.args.map(show).join(", ")} />
          <Row label="Expected" value={show(firstBad.expected)} />
          <Row
            label="Got"
            value={firstBad.error !== null ? firstBad.error : show(firstBad.actual)}
          />
          {firstBad.stdout.trim() !== "" && <Row label="Printed" value={firstBad.stdout.trim()} />}
        </div>
      )}
      {allGood && (
        <p style={{ margin: "10px 0 0", fontSize: 12.5, color: tone.text, lineHeight: 1.5 }}>
          Nice. These are only the examples — press Submit and Sprocket will try the
          {" "}hidden springs too.
        </p>
      )}
    </Panel>
  );
}

// ---- judged submission (the "Submit" button) --------------------------------
const VERDICT_TONE: Record<string, { bg: string; border: string; text: string; title: string }> = {
  passed: { bg: "#EAF7D9", border: "#6FBF73", text: "#4C7A2F", title: "Every spring held!" },
  failed: { bg: "#FDECEC", border: "#EF5B54", text: "#B4342D", title: "Some springs jammed" },
  error: { bg: "#FDECEC", border: "#EF5B54", text: "#B4342D", title: "The workbench jammed" },
  timeout: { bg: "#FDF3D6", border: "#E08A3C", text: "#7A5A2C", title: "Ran out of winding" },
  pending: { bg: "#EAF6FD", border: "#4FB0E5", text: "#2C6E9C", title: "Sprocket is testing…" },
  running: { bg: "#EAF6FD", border: "#4FB0E5", text: "#2C6E9C", title: "Sprocket is testing…" },
};

export function SubmissionResults({ result }: { result: SubmissionResult }) {
  const tone = VERDICT_TONE[result.status] ?? VERDICT_TONE.pending;
  const judging = result.status === "pending" || result.status === "running";
  const failure = result.failure;

  return (
    <Panel
      tone={tone}
      title={tone.title}
      badge={
        judging
          ? "JUDGING"
          : `${result.tests_passed}/${result.tests_total} SPRINGS` +
            (result.runtime_ms !== null ? ` · ${result.runtime_ms}MS` : "")
      }
    >
      {judging ? (
        <p style={{ margin: 0, fontSize: 13, color: tone.text }}>
          Your code is on the test rig. This takes a moment…
        </p>
      ) : (
        <>
          {result.tests_total > 0 && (
            <Pips
              results={Array.from({ length: result.tests_total }, (_, i) => ({
                passed: i < result.tests_passed,
              }))}
            />
          )}

          {result.status === "passed" && (result.xp_awarded ?? 0) > 0 && (
            <p
              style={{
                margin: "12px 0 0",
                fontFamily: FREDOKA,
                fontWeight: 700,
                fontSize: 20,
                color: "#4C7A2F",
              }}
            >
              +{result.xp_awarded} charge
              {result.leveled_up === true && " · LEVEL UP!"}
            </p>
          )}

          {failure !== null && (
            <div style={{ marginTop: 12, borderTop: "2px dashed #C9A96A", paddingTop: 10 }}>
              <Row label="Case" value={failure.label} mono={false} />
              <Row label="Input" value={failure.args.map(show).join(", ")} />
              {failure.hidden ? (
                <div style={{ marginTop: 6, fontSize: 12, color: "#9B7B5B", fontStyle: "italic" }}>
                  This is one of the hidden springs, so Sprocket won&apos;t show you what it
                  should have been — but here&apos;s what your toy did.
                </div>
              ) : (
                <Row label="Expected" value={show(failure.expected)} />
              )}
              <Row
                label="Got"
                value={
                  failure.error !== null && failure.error !== ""
                    ? failure.error
                    : show(failure.actual)
                }
              />
              {failure.stdout.trim() !== "" && (
                <Row label="Printed" value={failure.stdout.trim()} />
              )}
            </div>
          )}

          {result.newly_earned.length > 0 && (
            <div style={{ marginTop: 12, display: "flex", gap: 8, flexWrap: "wrap" }}>
              {result.newly_earned.map((badge) => (
                <span
                  key={badge.slug}
                  style={{
                    background: badge.color,
                    border: "3px solid #2E2620",
                    borderRadius: 20,
                    padding: "4px 12px",
                    fontSize: 12,
                    fontWeight: 800,
                    color: "#2E2620",
                  }}
                >
                  ★ {badge.name}
                </span>
              ))}
            </div>
          )}
        </>
      )}
    </Panel>
  );
}
