"""The language-neutral half of the sandbox contract.

Assembling a program is per-language and lives in `languages/`. What's here is
everything that is the same whatever the toy wrote in: the case payload that
goes in, and the results that come back out.

**Expected values never enter the sandbox.** Only arguments go in; the guest
reports what the toy's function actually returned, and the host compares. That
is the property that makes the verdict trustworthy: submitted code shares a
process with the driver and could print anything it likes to stdout, but with no
expected values in reach, forging a pass means emitting the correct answers —
which is just solving the problem. It holds for every language because every
pack's driver speaks this same wire format and no other.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# Re-exported so the judge's oldest import path still works. `build_program` is
# the Python pack's, which is what it always was.
from app.judge.languages.python import (
    DEFAULT_ADAPTERS,
    DRIVER,
    ENTRYPOINT_SLOT,
    build_program,
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


__all__ = [
    "DEFAULT_ADAPTERS",
    "DRIVER",
    "ENTRYPOINT_SLOT",
    "CaseOutcome",
    "RunResult",
    "build_program",
    "build_stdin",
    "parse_results",
]
