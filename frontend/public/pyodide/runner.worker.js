/**
 * In-browser Python for the "Run" button.
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

let pyodideReady = null;

async function getPyodide() {
  if (pyodideReady === null) {
    pyodideReady = (async () => {
      const { loadPyodide } = await import("/pyodide/pyodide.mjs");
      return loadPyodide({ indexURL: "/pyodide/" });
    })();
  }
  return pyodideReady;
}

// Mirrors the driver in backend/app/judge/harness.py, so what a toy sees here
// matches what the judge will do. One difference, and it matters: the expected
// values are present in the browser (they are the visible examples), whereas
// the server's guest never receives them at all.
const DRIVER = `
def __windup_run(_cases):
    import io as _io, json as _json, sys as _sys, traceback as _traceback
    _out = []
    for _case in _cases:
        _row = {"ordinal": _case["ordinal"], "actual": None, "stdout": "", "error": None}
        _real, _cap = _sys.stdout, _io.StringIO()
        _sys.stdout = _cap
        try:
            _value = _dump(__WINDUP_ENTRYPOINT__(*_build(list(_case["args"]))))
            _json.dumps(_value)
            _row["actual"] = _value
        except Exception:
            _row["error"] = "".join(
                _traceback.format_exception_only(*_sys.exc_info()[:2])
            ).strip()
        finally:
            _sys.stdout = _real
        _row["stdout"] = _cap.getvalue()[:2000]
        _out.append(_row)
    return _json.dumps(_out)
`;

self.onmessage = async (event) => {
  const { id, program, entrypoint, cases } = event.data ?? {};
  try {
    const pyodide = await getPyodide();
    if (program === undefined) {
      self.postMessage({ id, ready: true });
      return;
    }

    const driver = DRIVER.replaceAll("__WINDUP_ENTRYPOINT__", entrypoint);

    // A fresh namespace per run, so a previous attempt's definitions can't make
    // a broken one look like it works.
    const globals = pyodide.globals.get("dict")();
    try {
      pyodide.runPython(program + "\n" + driver, { globals });
      const run = globals.get("__windup_run");
      const raw = run(pyodide.toPy(cases));
      self.postMessage({ id, results: JSON.parse(raw) });
      run.destroy();
    } finally {
      globals.destroy();
    }
  } catch (err) {
    self.postMessage({ id, fatal: String(err?.message ?? err) });
  }
};
