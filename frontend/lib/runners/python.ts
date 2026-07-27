/**
 * Python in the browser, via Pyodide in a Worker.
 *
 * The ~11MB runtime is gitignored, copied into public/pyodide/ by
 * scripts/copy-pyodide.mjs, and fetched only when a toy first presses Run.
 */

import type { LocalRunner, RawCaseResult, RunRequest } from "./types";
import { WorkerChannel } from "./worker";

/** The adapters the harness assumes. Mirrors the Python pack in backend/app/judge/languages/. */
const DEFAULT_ADAPTERS = `def _build(args):
    return args


def _dump(value):
    return value
`;

const channel = new WorkerChannel("/pyodide/runner.worker.js");

export const pythonRunner: LocalRunner = {
  language: "python",

  preload: () => channel.ask({}, 120_000),

  reset: () => channel.reset(),

  async run({ code, entrypoint, preamble, cases, timeoutMs = 20_000 }: RunRequest) {
    const program = [DEFAULT_ADAPTERS, preamble ?? "", code].join("\n");
    const reply = await channel.ask(
      { program, entrypoint, cases: cases.map((c) => ({ ordinal: c.ordinal, args: c.args })) },
      timeoutMs
    );
    if (reply.fatal !== undefined) throw new Error(reply.fatal);
    return (reply.results ?? []) as RawCaseResult[];
  },
};
