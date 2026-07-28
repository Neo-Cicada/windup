"""Turning a sandbox run into a verdict.

This is the half of the judge the guest never sees. Expected values live only
here, which is what stops submitted code from claiming a pass it didn't earn.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.judge.harness import RunResult
from app.models.enums import SubmissionStatus, TestVisibility


@dataclass
class Verdict:
    status: SubmissionStatus
    tests_passed: int
    tests_total: int
    runtime_ms: int
    failure: dict[str, Any] | None = None


def _same(actual: Any, expected: Any) -> bool:
    """Structural equality that does not let `True` stand in for `1`.

    Python treats `True == 1` as true, so a plain `==` lets a problem asking for
    a count accept a boolean. The check has to recurse: the answer to most of
    these problems is a *list*, so guarding only the top level would still accept
    `[True, 2]` for `[1, 2]`.
    """
    if isinstance(expected, bool) != isinstance(actual, bool):
        return False
    if isinstance(expected, list) and isinstance(actual, list):
        return len(actual) == len(expected) and all(
            _same(a, e) for a, e in zip(actual, expected, strict=True)
        )
    if isinstance(expected, dict) and isinstance(actual, dict):
        return actual.keys() == expected.keys() and all(
            _same(actual[k], expected[k]) for k in expected
        )
    return actual == expected


def _matches(actual: Any, expected: Any, compare_mode: str) -> bool:
    if compare_mode == "unordered":
        # For problems where any ordering of the answer is correct. Sort both
        # sides, then compare with the same type-aware check rather than `==`.
        try:
            ordered_actual = sorted(actual, key=repr)
            ordered_expected = sorted(expected, key=repr)
        except TypeError:
            return _same(actual, expected)
        return _same(ordered_actual, ordered_expected)
    return _same(actual, expected)


def grade(
    run: RunResult,
    cases: list[dict[str, Any]],
    *,
    compare_mode: str = "exact",
) -> Verdict:
    """Compare what the guest produced against what the cases expect.

    A case the guest never reported is a failure, not a skip — that is how a
    fuel trap or a crash halfway through the batch is accounted for.
    """
    total = len(cases)
    passed = 0
    failure: dict[str, Any] | None = None

    for case in cases:
        outcome = run.outcomes.get(case["ordinal"])
        hidden = case.get("visibility") == TestVisibility.HIDDEN

        if outcome is not None and outcome.reported and outcome.error is None:
            if _matches(outcome.actual, case["expected"], compare_mode):
                passed += 1
                continue

        if failure is not None:
            continue

        # First failure only, and only ever enough of it to debug with.
        failure = {
            "ordinal": case["ordinal"],
            "label": case.get("label") or f"case {case['ordinal'] + 1}",
            "hidden": hidden,
            "args": case["args"],
            "actual": outcome.actual if outcome and outcome.reported else None,
            "stdout": (outcome.stdout if outcome else "") or "",
            "error": (outcome.error if outcome else None)
            or (None if outcome and outcome.reported else _why_missing(run)),
        }
        # Handing back a hidden case's expected value would turn the hidden
        # tests into a lookup table. The toy's own output stays visible.
        if not hidden:
            failure["expected"] = case["expected"]

    if run.timed_out:
        status = SubmissionStatus.TIMEOUT
    elif run.fatal is not None and passed == 0:
        status = SubmissionStatus.ERROR
    elif passed == total and total > 0:
        status = SubmissionStatus.PASSED
    else:
        status = SubmissionStatus.FAILED

    return Verdict(
        status=status,
        tests_passed=passed,
        tests_total=total,
        runtime_ms=run.runtime_ms,
        failure=failure,
    )


def _why_missing(run: RunResult) -> str:
    """Explain a case the guest never reported on.

    What the language said outranks how the host classified it: "SyntaxError:
    invalid syntax" is something a toy can act on, where "exited with status 1"
    and a wasm backtrace are not.
    """
    if run.timed_out:
        return "ran out of winding before this case finished"
    if run.stderr.strip():
        return run.stderr.strip().splitlines()[-1][:400]
    if run.fatal:
        return run.fatal
    return "the toy never reported on this case"
