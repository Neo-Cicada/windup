/**
 * SQL in the browser, through the Python one.
 *
 * `sqlite3` is bundled in Pyodide exactly as it is in CPython, so a SQL problem
 * needs no runtime of its own on either side — this builds the same Python
 * program the server's SQL pack builds and hands it to the Pyodide worker.
 *
 * Mirrors `backend/app/judge/languages/sql.py`; the two must agree, since the
 * whole point is that Run previews what Submit will decide.
 */

import type { LocalRunner, RawCaseResult, RunRequest } from "./types";
import { pyodideChannel } from "./python";

/** The Python pack calls this like any other entrypoint. */
const ENTRYPOINT = "__windup_sql";

/**
 * Both the schema and the toy's query are embedded as Python string literals via
 * `JSON.stringify` — JSON's escaping is a subset of Python's, so a quote or a
 * backslash in a query means itself and cannot end the literal early.
 */
function buildGuest(schema: string, query: string): string {
  return `
def ${ENTRYPOINT}(*tables):
    import sqlite3 as _sqlite3

    _conn = _sqlite3.connect(":memory:")
    try:
        _conn.executescript(${JSON.stringify(schema)})
        for _table in tables:
            _name = _table["table"]
            if not _name.isidentifier():
                raise ValueError("that isn't a table name: " + repr(_name))
            _rows = _table["rows"]
            if _rows:
                _slots = ", ".join("?" * len(_rows[0]))
                _conn.executemany("INSERT INTO " + _name + " VALUES (" + _slots + ")", _rows)
        _cursor = _conn.execute(${JSON.stringify(query)})
        return [list(_row) for _row in _cursor.fetchall()]
    finally:
        _conn.close()
`;
}

export const sqlRunner: LocalRunner = {
  language: "sql",

  preload: () => pyodideChannel.ask({}, 120_000),

  reset: () => pyodideChannel.reset(),

  async run({ code, preamble, cases, timeoutMs = 20_000 }: RunRequest) {
    const reply = await pyodideChannel.ask(
      {
        program: buildGuest(preamble ?? "", code),
        entrypoint: ENTRYPOINT,
        cases: cases.map((c) => ({ ordinal: c.ordinal, args: c.args })),
      },
      timeoutMs
    );
    if (reply.fatal !== undefined) throw new Error(reply.fatal);
    return (reply.results ?? []) as RawCaseResult[];
  },
};
