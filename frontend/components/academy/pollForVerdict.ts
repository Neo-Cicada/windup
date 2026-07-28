import { api } from "@/lib/api";
import { TERMINAL_STATUSES } from "@/lib/types";
import type { SubmissionResult } from "@/lib/types";

/** How long to wait on the judge before telling the toy something is wrong. */
const JUDGE_PATIENCE_MS = 45_000;
const POLL_CEILING_MS = 2_000;

/** What the workbench shows between "queued" and the verdict. */
export const PENDING_RESULT: SubmissionResult = {
  submission_id: "",
  status: "pending",
  language: "",
  unaided: true,
  xp_awarded: null,
  coins_awarded: null,
  leveled_up: null,
  sprocket_message: "",
  confetti: 0,
  newly_earned: [],
  progress: null,
  tests_passed: 0,
  tests_total: 0,
  runtime_ms: null,
  failure: null,
  stalled: false,
};

const sleep = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Poll a submission until the judge rules on it.
 *
 * Returns null if `stillWanted` goes false (the toy moved on) or patience runs
 * out. The backoff keeps a busy queue from being hammered by every open tab.
 */
export async function pollForVerdict(
  submissionId: string,
  firstDelayMs: number,
  stillWanted: () => boolean
): Promise<SubmissionResult | null> {
  const deadline = Date.now() + JUDGE_PATIENCE_MS;
  let delay = firstDelayMs > 0 ? firstDelayMs : 400;

  while (Date.now() < deadline) {
    await sleep(delay);
    if (!stillWanted()) return null;

    const result = await api<SubmissionResult>(`/submissions/${submissionId}`);
    if (TERMINAL_STATUSES.includes(result.status)) return result;

    // The server has decided this has waited too long to be normal — usually
    // because no judge worker is running. It knows why; waiting out the rest of
    // the deadline would only delay a message we already have.
    if (result.stalled) throw new Error(result.sprocket_message);

    delay = Math.min(Math.round(delay * 1.4), POLL_CEILING_MS);
  }

  throw new Error("Sprocket is taking an unusually long time. Your run is still queued.");
}
