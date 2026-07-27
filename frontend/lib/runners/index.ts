/**
 * The "Run" button's engines, keyed by language.
 *
 * A language in here can be tried instantly on the toy's own CPU; a language
 * that isn't simply has no Run button, and Submit — the only thing that grades
 * anything — works exactly the same either way. The server says which languages
 * offer this, per problem, on `ProblemLanguage.runs_in_browser`.
 */

import { javascriptRunner } from "./javascript";
import { pythonRunner } from "./python";
import { sameValue, type LocalRunner, type RunCaseResult, type RunRequest } from "./types";

export type { RunCaseResult, RunRequest } from "./types";

const RUNNERS: Record<string, LocalRunner> = {
  [pythonRunner.language]: pythonRunner,
  [javascriptRunner.language]: javascriptRunner,
};

export function runnerFor(language: string): LocalRunner | null {
  return RUNNERS[language] ?? null;
}

export function canRunLocally(language: string): boolean {
  return language in RUNNERS;
}

/** Warm an engine up. No-op for a language with no local runner. */
export function preloadRunner(language: string): Promise<unknown> {
  return runnerFor(language)?.preload() ?? Promise.resolve(null);
}

/** Throw every engine away. */
export function resetRunners() {
  for (const runner of Object.values(RUNNERS)) runner.reset();
}

/**
 * Run `code` against the visible example cases, in `language`.
 *
 * Comparison happens here rather than inside the language, so what a toy sees
 * matches what the judge will decide — the server's grader also compares from
 * the outside, on plain JSON.
 */
export async function runExamples(
  options: RunRequest & { language: string }
): Promise<RunCaseResult[]> {
  const { language, cases } = options;
  if (cases.length === 0) return [];

  const runner = runnerFor(language);
  if (runner === null) {
    throw new Error(`Sprocket can't try ${language} here — press Submit and he'll run it.`);
  }

  const raw = await runner.run(options);
  const byOrdinal = new Map(raw.map((r) => [r.ordinal, r]));
  return cases.map((c) => {
    const got = byOrdinal.get(c.ordinal);
    return {
      ordinal: c.ordinal,
      label: c.label,
      args: c.args,
      expected: c.expected,
      actual: got?.actual ?? null,
      stdout: got?.stdout ?? "",
      error: got?.error ?? null,
      passed: got !== undefined && got.error === null && sameValue(got.actual, c.expected),
    };
  });
}
