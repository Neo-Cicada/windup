"""The SQL pack — SQLite, riding inside the Python interpreter we already have.

The odd one out, twice over.

**It needs no artifact.** `sqlite3` is in CPython's standard library, so this
pack emits a *Python* program and hands it to the Python pack. The judge gains a
language and the vendor directory gains nothing. Pyodide bundles `sqlite3` too,
which is why the Run button works here with no extra download either.

**A query is not a function call.** There is no entrypoint to call and no
signature to generate a stub from. What a SQL problem has instead:

- `harness_preamble` is the schema — the `CREATE TABLE` statements the query is
  written against.
- each case's `args` is one entry per table, `{"table": ..., "rows": [[...]]}`,
  so the same query is graded against different data.
- `expected` is the result set, a list of rows.

The wire format downstream is the Python driver's, unchanged, because that is
literally what is running.
"""

from __future__ import annotations

import json

from app.judge.languages.base import ProgramSpec
from app.judge.languages.python import PACK as PYTHON_PACK
from app.judge.signature import Signature

# The Python pack calls this like any other entrypoint, and `_build`/`_dump`
# stay the identity pair, so the case arguments arrive as the table payloads and
# the result set goes back as plain JSON.
ENTRYPOINT = "__windup_sql"

SCHEMA_SLOT = "__WINDUP_SCHEMA__"
QUERY_SLOT = "__WINDUP_QUERY__"

GUEST = f'''
def {ENTRYPOINT}(*tables):
    import sqlite3 as _sqlite3

    _conn = _sqlite3.connect(":memory:")
    try:
        _conn.executescript({SCHEMA_SLOT})
        for _table in tables:
            _name = _table["table"]
            # The table name is the problem author's, not the toy's, but it is
            # the one thing here that cannot be a bound parameter.
            if not _name.isidentifier():
                raise ValueError("that isn't a table name: " + repr(_name))
            _rows = _table["rows"]
            if _rows:
                _slots = ", ".join("?" * len(_rows[0]))
                _conn.executemany("INSERT INTO " + _name + " VALUES (" + _slots + ")", _rows)
        _cursor = _conn.execute({QUERY_SLOT})
        return [list(_row) for _row in _cursor.fetchall()]
    finally:
        _conn.close()
'''


def build_guest(*, schema: str, query: str) -> str:
    """The Python program that runs one SQL submission.

    Both the schema and the toy's query are embedded as Python string literals
    via `json.dumps` — JSON's escaping is a subset of Python's, so a quote or a
    backslash in a query means itself and cannot end the literal early.
    """
    return GUEST.replace(SCHEMA_SLOT, json.dumps(schema)).replace(QUERY_SLOT, json.dumps(query))


class SqlPack:
    slug = "sql"
    label = "SQL"
    extension = "sql"
    runs_in_browser = True

    def wasm_path(self) -> str:
        # Whatever Python runs in. There is no sqlite.wasm to fetch.
        return PYTHON_PACK.wasm_path()

    def available(self) -> bool:
        return PYTHON_PACK.available()

    def build_program(
        self,
        *,
        entrypoint: str,
        preamble: str,
        code: str,
        signature: Signature | None = None,
    ) -> ProgramSpec:
        # `entrypoint` and `signature` are ignored: there is no function to call.
        return PYTHON_PACK.build_program(
            entrypoint=ENTRYPOINT,
            preamble="",
            code=build_guest(schema=preamble, query=code),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        return "SELECT\n  -- your turn, little toy…\n;\n"


PACK = SqlPack()

__all__ = ["ENTRYPOINT", "GUEST", "PACK", "SqlPack", "build_guest"]
