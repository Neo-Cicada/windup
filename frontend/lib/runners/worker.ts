/**
 * The request/reply plumbing every worker-backed runner shares.
 *
 * Each engine lives at a plain file in public/runners/ and is loaded by URL —
 * no bundler involvement, so nothing here depends on how Next chooses to handle
 * workers, and a heavy runtime is fetched only when a toy first presses Run.
 *
 * Protocol (the same for every language):
 *   in : {id, program, entrypoint, cases: [{ordinal, args}]}
 *   out: {id, ready} | {id, results: [{ordinal, actual, stdout, error}]} | {id, fatal}
 */

import type { RawCaseResult } from "./types";

export type WorkerReply = {
  id: number;
  ready?: boolean;
  results?: RawCaseResult[];
  fatal?: string;
};

let nextId = 1;

/** One worker per script URL, created on first use and thrown away on a runaway. */
export class WorkerChannel {
  private worker: Worker | null = null;

  constructor(private readonly url: string) {}

  reset() {
    if (this.worker !== null) {
      this.worker.terminate();
      this.worker = null;
    }
  }

  ask(message: Record<string, unknown>, timeoutMs: number): Promise<WorkerReply> {
    if (this.worker === null) {
      this.worker = new Worker(this.url, { type: "module" });
    }
    const w = this.worker;
    const id = nextId++;

    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        cleanup();
        // A runaway loop can't be interrupted from outside, so the worker is
        // thrown away rather than waited on.
        this.reset();
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
}
