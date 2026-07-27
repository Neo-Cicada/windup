/**
 * JavaScript in the browser, in a plain Worker.
 *
 * The engine is the one already running the page, so this runner downloads
 * nothing — pressing Run on a JavaScript problem is instant from the first
 * press, unlike Python's ~11MB Pyodide fetch.
 */

import type { LocalRunner, RawCaseResult, RunRequest } from "./types";
import { WorkerChannel } from "./worker";

/** The adapters the harness assumes. Mirrors the JavaScript pack in backend/app/judge/languages/. */
const DEFAULT_ADAPTERS = `function _build(args) {
  return args;
}

function _dump(value) {
  return value;
}
`;

const channel = new WorkerChannel("/runners/js.worker.js");

export const javascriptRunner: LocalRunner = {
  language: "javascript",

  preload: () => channel.ask({}, 10_000),

  reset: () => channel.reset(),

  async run({ code, entrypoint, preamble, cases, timeoutMs = 10_000 }: RunRequest) {
    const program = [DEFAULT_ADAPTERS, preamble ?? "", code].join("\n");
    const reply = await channel.ask(
      { program, entrypoint, cases: cases.map((c) => ({ ordinal: c.ordinal, args: c.args })) },
      timeoutMs
    );
    if (reply.fatal !== undefined) throw new Error(reply.fatal);
    return (reply.results ?? []) as RawCaseResult[];
  },
};
