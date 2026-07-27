/**
 * What every in-browser runner has to provide.
 *
 * These are the "Run" button's engines, one per language that is cheap enough
 * to execute locally. They exist to keep the overwhelming majority of executions
 * off the server: a toy iterating on a broken function runs it a dozen times
 * before it works, and those runs cost nothing here.
 *
 * None of them is a judge. They run the visible example cases only, their
 * verdict is never transmitted, and they earn no charge. `lib/api.ts` submitting
 * to the server is the only thing that decides whether a problem is solved —
 * which is also why a language with no local runner loses nothing but the fast
 * feedback loop.
 */

import type { TestCase } from "../types";

export type RunCaseResult = {
  ordinal: number;
  label: string;
  passed: boolean;
  args: unknown[];
  expected: unknown;
  actual: unknown;
  stdout: string;
  error: string | null;
};

/** What a runner reports per case, before the comparison the registry does. */
export type RawCaseResult = {
  ordinal: number;
  actual: unknown;
  stdout: string;
  error: string | null;
};

export type RunRequest = {
  code: string;
  entrypoint: string;
  preamble: string;
  cases: TestCase[];
  timeoutMs?: number;
};

export type LocalRunner = {
  language: string;
  /** Warm the engine up. Safe to call more than once. */
  preload: () => Promise<unknown>;
  /** Throw the engine away — the only way to stop a runaway loop in a browser. */
  reset: () => void;
  run: (request: RunRequest) => Promise<RawCaseResult[]>;
};

/**
 * Structural equality over the plain-JSON shapes a test case can hold.
 *
 * Comparison happens here rather than inside the language, so every runner's
 * semantics match the server's grader — which also compares on the outside.
 */
export function sameValue(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== typeof b) return false;
  if (Array.isArray(a) && Array.isArray(b)) {
    return a.length === b.length && a.every((v, i) => sameValue(v, b[i]));
  }
  if (a !== null && b !== null && typeof a === "object" && typeof b === "object") {
    const ka = Object.keys(a as object);
    const kb = Object.keys(b as object);
    return (
      ka.length === kb.length &&
      ka.every((k) =>
        sameValue((a as Record<string, unknown>)[k], (b as Record<string, unknown>)[k])
      )
    );
  }
  return false;
}
