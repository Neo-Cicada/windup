"""Assembling the program that runs inside the sandbox, and reading it back.

Layout of the assembled program:

    1. default `_build` / `_dump` adapters (identity)
    2. the problem's `harness_preamble`, which may override them and define
       whatever structures the problem needs (ListNode, TreeNode)
    3. the toy's own code
    4. the driver, which reads cases from stdin and writes results to stdout

**Expected values never enter the sandbox.** Only arguments go in; the guest
reports what the toy's function actually returned, and the host compares. That
is the property that makes the verdict trustworthy: submitted code shares a
process with the driver and could print anything it likes to stdout, but with no
expected values in reach, forging a pass means emitting the correct answers —
which is just solving the problem.
"""

from __future__ import annotations

import json
import keyword
from dataclasses import dataclass, field
from typing import Any

DEFAULT_ADAPTERS = '''\
def _build(args):
    """Turn the JSON argument list into the real call arguments."""
    return args


def _dump(value):
    """Turn the return value back into something JSON can hold."""
    return value
'''

# Runs after the toy's code. Each case is reported on its own line and flushed,
# so if the fuel runs out mid-run the cases that already finished still arrive
# and the timeout can be pinned to a specific case.
#
# The entrypoint is substituted by plain replacement, not str.format — the
# driver is full of dict literals and subscripts that format() would try to
# interpret as fields.
ENTRYPOINT_SLOT = "__WINDUP_ENTRYPOINT__"

DRIVER = '''\

def __windup_main():
    import io as _io
    import json as _json
    import sys as _sys
    import traceback as _traceback

    _real_stdout = _sys.stdout
    _payload = _json.load(_sys.stdin)

    for _case in _payload["tests"]:
        _result = {"ordinal": _case["ordinal"], "actual": None, "stdout": "", "error": None}
        # The toy's own prints are captured rather than allowed onto the result
        # stream — they get handed back as debugging output instead.
        _captured = _io.StringIO()
        _sys.stdout = _captured
        try:
            _value = _dump(__WINDUP_ENTRYPOINT__(*_build(list(_case["args"]))))
            try:
                _json.dumps(_value, allow_nan=False)
            except (TypeError, ValueError):
                raise TypeError(
                    "returned something that isn't plain data: " + type(_value).__name__
                )
            _result["actual"] = _value
        except Exception:
            _lines = _traceback.format_exception_only(*_sys.exc_info()[:2])
            _result["error"] = "".join(_lines).strip()
        except BaseException:
            # RecursionError arrives as an Exception, but a bare `raise SystemExit`
            # in submitted code should not look like a clean finish.
            _result["error"] = "the toy stopped itself mid-run"
        finally:
            _sys.stdout = _real_stdout
        _result["stdout"] = _captured.getvalue()[:2000]
        _real_stdout.write(_json.dumps(_result) + "\\n")
        _real_stdout.flush()


__windup_main()
'''


def build_program(*, entrypoint: str, preamble: str, code: str) -> str:
    """Assemble the full guest program for one submission."""
    # `"class".isidentifier()` is True, so the keyword check is not redundant —
    # without it a mis-seeded entrypoint produces a program that cannot compile
    # and shows up as every submission failing rather than as a config mistake.
    if not entrypoint.isidentifier() or keyword.iskeyword(entrypoint):
        raise ValueError(f"entrypoint {entrypoint!r} is not a usable Python identifier")
    return "\n".join(
        [
            DEFAULT_ADAPTERS,
            preamble or "",
            code,
            DRIVER.replace(ENTRYPOINT_SLOT, entrypoint),
        ]
    )


def build_stdin(cases: list[dict[str, Any]]) -> str:
    """The case payload — arguments only, never expected values."""
    return json.dumps({"tests": [{"ordinal": c["ordinal"], "args": c["args"]} for c in cases]})


@dataclass
class CaseOutcome:
    ordinal: int
    actual: Any = None
    stdout: str = ""
    error: str | None = None
    reported: bool = False  # False means the guest never got this far


@dataclass
class RunResult:
    """What the host learns from one guest invocation."""

    outcomes: dict[int, CaseOutcome] = field(default_factory=dict)
    timed_out: bool = False
    runtime_ms: int = 0
    # Anything the guest wrote to stderr — a syntax error, usually.
    stderr: str = ""
    # Set when the program could not run at all (didn't compile, crashed on import).
    fatal: str | None = None


def parse_results(stdout: str) -> dict[int, CaseOutcome]:
    """Read the driver's JSONL back.

    Tolerant by design: a partial final line is what a fuel trap mid-write looks
    like, and unparseable noise is what submitted code printing to fd 1 directly
    looks like. Either way we keep whatever well-formed results we got and the
    caller treats the missing ordinals as unfinished.
    """
    outcomes: dict[int, CaseOutcome] = {}
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            row = json.loads(line)
        except ValueError:
            continue
        if not isinstance(row, dict) or not isinstance(row.get("ordinal"), int):
            continue
        if row["ordinal"] in outcomes:
            # First report for a case wins. Submitted code can write to fd 1
            # directly, and without this it could overwrite a result the driver
            # already produced. It gains nothing by doing so — the expected
            # values are not in the sandbox — but there is no reason to allow it.
            continue
        outcomes[row["ordinal"]] = CaseOutcome(
            ordinal=row["ordinal"],
            actual=row.get("actual"),
            stdout=row.get("stdout") or "",
            error=row.get("error"),
            reported=True,
        )
    return outcomes
