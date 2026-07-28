/**
 * In-browser JavaScript for the "Run" button.
 *
 * The cheapest runner in the academy: the engine is already here, so pressing
 * Run on a JavaScript problem downloads nothing at all.
 *
 * This runs the toy's code against the *visible example cases only*, on the
 * user's own CPU. It is a fast feedback loop, not a judge: the verdict it
 * produces is never sent anywhere and never earns charge. Grading happens
 * server-side, in app/judge/, against hidden cases this worker never sees.
 *
 * Deliberately a plain file in public/ rather than a bundled module — it is
 * loaded by URL with no bundler involvement, so nothing here depends on how
 * Next chooses to handle workers.
 *
 * Protocol
 *   in : {id, program, entrypoint, cases: [{ordinal, args}]}
 *   out: {id, ready} | {id, results: [{ordinal, actual, stdout, error}]} | {id, fatal}
 */

/**
 * Refuse anything JSON can't hold, mirroring the `allow_nan=False` check in the
 * Python driver. `JSON.stringify` alone is too forgiving: it turns NaN into
 * null and drops undefined, either of which would quietly become a wrong answer
 * that looks like a right one.
 */
function plain(value, seen) {
  if (value === null) return value;
  const kind = typeof value;
  if (kind === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("returned a number JSON can't hold: " + value);
    }
    return value;
  }
  if (kind === "string" || kind === "boolean") return value;
  if (kind === "undefined") throw new TypeError("returned nothing at all");
  if (kind !== "object") {
    throw new TypeError("returned something that isn't plain data: " + kind);
  }
  if (seen.has(value)) throw new TypeError("returned something that points at itself");
  seen.add(value);
  const out = Array.isArray(value)
    ? value.map((item) => plain(item, seen))
    : Object.fromEntries(Object.entries(value).map(([k, v]) => [k, plain(v, seen)]));
  seen.delete(value);
  return out;
}

function describe(err) {
  if (err instanceof Error) return (err.name + ": " + err.message).trim();
  return String(err);
}

self.onmessage = (event) => {
  const { id, program, entrypoint, cases } = event.data ?? {};
  if (program === undefined) {
    // Nothing to warm up — the engine is the one already running this.
    self.postMessage({ id, ready: true });
    return;
  }

  let bench;
  try {
    // A fresh scope per run, so a previous attempt's definitions can't make a
    // broken one look like it works. The adapters are returned alongside the
    // entrypoint because the preamble may have replaced them.
    bench = new Function(
      '"use strict";\n' +
        program +
        "\nreturn {" +
        "  entry: typeof " + entrypoint + ' === "function" ? ' + entrypoint + " : undefined," +
        "  build: _build," +
        "  dump: _dump," +
        "};"
    )();
  } catch (err) {
    self.postMessage({ id, fatal: describe(err) });
    return;
  }

  if (typeof bench.entry !== "function") {
    self.postMessage({ id, fatal: "No function called " + entrypoint + " to try." });
    return;
  }

  const realLog = console.log;
  const results = (cases ?? []).map((testCase) => {
    const row = { ordinal: testCase.ordinal, actual: null, stdout: "", error: null };
    // The toy's own logging is captured rather than allowed onto the result
    // stream — it gets handed back as debugging output instead.
    const captured = [];
    console.log = (...parts) => captured.push(parts.map(String).join(" "));
    try {
      row.actual = plain(bench.dump(bench.entry(...bench.build(testCase.args.slice()))), new Set());
    } catch (err) {
      row.error = describe(err);
    } finally {
      console.log = realLog;
    }
    row.stdout = captured.join("\n").slice(0, 2000);
    return row;
  });

  self.postMessage({ id, results });
};
