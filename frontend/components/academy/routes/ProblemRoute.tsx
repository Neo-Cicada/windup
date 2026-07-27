"use client";

import { useEffect, useRef, useState } from "react";
import { ErrorPanel, Winding } from "@/components/ScreenState";
import { ProblemView } from "@/components/academy/screens/ProblemView";
import { useAcademy } from "@/components/academy/AcademyProvider";
import { clearDraft, readDraft, writeDraft } from "@/components/academy/drafts";
import { PENDING_RESULT, pollForVerdict } from "@/components/academy/pollForVerdict";
import { api, errorMessage, post } from "@/lib/api";
import { runExamples, type RunCaseResult } from "@/lib/pyodide";
import type {
  ChestTier,
  ChestUnlockResult,
  ProblemDetail,
  SubmissionAccepted,
  SubmissionResult,
} from "@/lib/types";

export function ProblemRoute({ slug }: { slug: string }) {
  const { boss, dashboard, streak, burst, say } = useAcademy();

  const [problem, setProblem] = useState<ProblemDetail | null>(null);
  const [loadError, setLoadError] = useState<{ slug: string; message: string } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [code, setCode] = useState("");
  const [unlocking, setUnlocking] = useState<ChestTier | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [running, setRunning] = useState(false);
  const [localResults, setLocalResults] = useState<RunCaseResult[] | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmissionResult | null>(null);
  const [problemNonce, setProblemNonce] = useState(0);

  // Bumped on every submit; a poll loop whose nonce is stale stops touching state,
  // so switching problems mid-judge can't drop a verdict onto the wrong screen.
  const submitNonce = useRef(0);

  // Next reuses this component between `/academy/problem/a` and `/academy/problem/b`, so
  // state outlives the slug and everything below has to be guarded on it.
  useEffect(() => {
    let cancelled = false;
    api<ProblemDetail>(`/problems/${slug}`)
      .then((detail) => {
        if (cancelled) return;
        setProblem(detail);
        // Whatever was half-written when the toy wandered off, else the starter code.
        setCode(readDraft(slug) ?? detail.starter_code);
        // Results belong to the problem that produced them.
        setLocalResults(null);
        setSubmitResult(null);
      })
      .catch((err) => {
        if (!cancelled) setLoadError({ slug, message: errorMessage(err) });
      });
    return () => {
      cancelled = true;
    };
  }, [slug, problemNonce]);

  function changeCode(next: string) {
    setCode(next);
    writeDraft(slug, next);
  }

  function reloadProblem() {
    setLoadError(null);
    setProblemNonce((n) => n + 1);
  }

  async function unlockChest(tier: ChestTier) {
    if (problem === null) return;
    setUnlocking(tier);
    setActionError(null);
    try {
      const opened = await post<ChestUnlockResult>(`/problems/${problem.slug}/chests/${tier}`);
      setProblem((p) =>
        p === null
          ? p
          : {
              ...p,
              chests: opened.chests,
              unaided: opened.unaided,
              help_shelf: { ...p.help_shelf, [tier]: opened.content },
            }
      );
      say(opened.message);
      burst(18);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setUnlocking(null);
    }
  }

  /** Try the visible examples in the browser. Earns nothing; grades nothing. */
  async function runProblem() {
    if (problem === null) return;
    setRunning(true);
    setActionError(null);
    setSubmitResult(null);
    try {
      const results = await runExamples({
        code,
        entrypoint: problem.entrypoint,
        preamble: problem.harness_preamble,
        cases: problem.example_tests,
      });
      setLocalResults(results);
      const held = results.filter((r) => r.passed).length;
      say(
        held === results.length
          ? "Examples all held! Press Submit and I'll try the hidden springs."
          : `${held} of ${results.length} examples held — have another look.`
      );
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setRunning(false);
    }
  }

  /**
   * Hand the code to the judge, then poll for its verdict.
   *
   * Submitting no longer returns a result — the server queues the code and a judge worker
   * runs it — so everything that used to fire off the response (confetti, the dashboard
   * refresh, the boss round) now fires off the verdict.
   *
   * The poll is deliberately not cancelled on unmount: `say`, `burst` and the reloads all
   * belong to the layout's provider, so walking off to another screen mid-judge still gets
   * you your charge and your confetti.
   */
  async function submitProblem() {
    if (problem === null) return;
    const nonce = ++submitNonce.current;
    setSubmitting(true);
    setActionError(null);
    setLocalResults(null);
    try {
      const accepted = await post<SubmissionAccepted>(`/problems/${problem.slug}/submit`, {
        code,
        language: problem.language,
        // Tagging the submission is what lets a boss round actually clear.
        boss_session_id: boss.session?.status === "running" ? boss.session.id : null,
      });
      if (submitNonce.current !== nonce) return;
      setSubmitResult({
        ...PENDING_RESULT,
        submission_id: accepted.submission_id,
        status: accepted.status,
      });

      const verdict = await pollForVerdict(accepted.submission_id, accepted.poll_after_ms, () =>
        submitNonce.current === nonce
      );
      if (verdict === null || submitNonce.current !== nonce) return;

      setSubmitResult(verdict);
      say(verdict.sprocket_message);
      burst(verdict.confetti);
      if (verdict.status === "passed") {
        setProblem((p) => (p === null ? p : { ...p, solved: true }));
        // Reopening a solved problem should show the code that solved it, not a stale draft.
        clearDraft(problem.slug);
      }
      dashboard.reload();
      streak.reload();
      if (boss.session !== null) boss.refresh();
    } catch (err) {
      if (submitNonce.current === nonce) {
        setActionError(errorMessage(err));
        setSubmitResult(null);
      }
    } finally {
      if (submitNonce.current === nonce) setSubmitting(false);
    }
  }

  if (problem !== null && problem.slug === slug) {
    return (
      <ProblemView
        problem={problem}
        code={code}
        onCodeChange={changeCode}
        unlocking={unlocking}
        submitting={submitting}
        running={running}
        localResults={localResults}
        result={submitResult}
        error={actionError}
        onUnlock={unlockChest}
        onRun={runProblem}
        onSubmit={submitProblem}
      />
    );
  }

  if (loadError !== null && loadError.slug === slug) {
    return <ErrorPanel message={loadError.message} onRetry={reloadProblem} />;
  }

  return <Winding label="Fetching the toy…" />;
}
