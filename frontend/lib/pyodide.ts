/**
 * The "Run" button's engine: Python in the browser, via Pyodide in a Worker.
 *
 * This exists to keep the overwhelming majority of executions off the server.
 * A toy iterating on a broken function runs it a dozen times before it works;
 * those runs cost nothing here, and the judge only ever sees the final Submit.
 *
 * It is explicitly *not* a judge. It runs the visible example cases only, its
 * verdict is never transmitted, and it earns no charge. `lib/api.ts` submitting
 * to the server is the only thing that decides whether a problem is solved.
 *
 * The worker lives at public/pyodide/runner.worker.js as a plain file, loaded
 * by URL — no bundler involvement, and the ~11MB runtime is fetched only when a
 * toy first presses Run, never on page load.
 */

import type { TestCase } from "./types";

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

/** The adapters the harness assumes. Mirrors DEFAULT_ADAPTERS in backend/app/judge/harness.py. */
const DEFAULT_ADAPTERS = `def _build(args):
    return args


def _dump(value):
    return value
`;

let worker: Worker | null = null;
let nextId = 1;

/** Terminates the worker — the only way to stop a runaway loop in the browser. */
export function resetRunner() {
  if (worker !== null) {
    worker.terminate();
    worker = null;
  }
}

function getWorker(): Worker {
  if (worker === null) {
    worker = new Worker("/pyodide/runner.worker.js", { type: "module" });
  }
  return worker;
}

type WorkerReply = {
  id: number;
  ready?: boolean;
  results?: { ordinal: number; actual: unknown; stdout: string; error: string | null }[];
  fatal?: string;
};

function ask(message: Record<string, unknown>, timeoutMs: number): Promise<WorkerReply> {
  const w = getWorker();
  const id = nextId++;

  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      // A runaway loop can't be interrupted from outside, so the worker is
      // thrown away rather than waited on.
      resetRunner();
      reject(new Error("That run never finished — check for a loop with no way out."));
    }, timeoutMs);

    function cleanup() {
      clearTimeout(timer);
      w.removeEventListener("message", onMessage);
      w.removeEventListener("error", onError);
    }

    function onMessage(event: MessageEvent<WorkerReply>) {
      if (event.data?.id !== id) return;
      cleanup();
      resolve(event.data);
    }

    function onError(event: ErrorEvent) {
      cleanup();
      reject(new Error(event.message || "The workbench engine wouldn't start."));
    }

    w.addEventListener("message", onMessage);
    w.addEventListener("error", onError);
    w.postMessage({ id, ...message });
  });
}

/** Warm the runtime up. Safe to call more than once. */
export function preloadRunner(): Promise<unknown> {
  return ask({}, 120_000);
}

/**
 * Run `code` against the visible example cases.
 *
 * Comparison happens here rather than in Python so the semantics match the
 * server's grader, which also compares on the outside.
 */
export async function runExamples(options: {
  code: string;
  entrypoint: string;
  preamble: string;
  cases: TestCase[];
  timeoutMs?: number;
}): Promise<RunCaseResult[]> {
  const { code, entrypoint, preamble, cases, timeoutMs = 20_000 } = options;
  if (cases.length === 0) return [];

  const program = [DEFAULT_ADAPTERS, preamble ?? "", code].join("\n");
  const reply = await ask(
    {
      program,
      entrypoint,
      cases: cases.map((c) => ({ ordinal: c.ordinal, args: c.args })),
    },
    timeoutMs
  );

  if (reply.fatal !== undefined) {
    throw new Error(reply.fatal);
  }

  const byOrdinal = new Map((reply.results ?? []).map((r) => [r.ordinal, r]));
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

/** Structural equality over the plain-JSON shapes a test case can hold. */
function sameValue(a: unknown, b: unknown): boolean {
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
