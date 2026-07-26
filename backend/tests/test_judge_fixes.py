"""Regression tests for defects found while reviewing the judge.

Each of these was a real bug, so each gets a test that fails without its fix.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import settings
from app.judge.grade import _matches, grade
from app.judge.harness import RunResult, build_program, parse_results
from app.judge.worker import abandon_exhausted
from app.models import Submission, SubmissionStatus
from tests.conftest import Judge, TestSession, solution_for


# ---- a busy queue is not a broken one ---------------------------------------
async def test_a_backed_up_queue_does_not_tell_the_client_to_give_up(judge: Judge) -> None:
    """`stalled` means "stop polling", so it must not be set while the judge works.

    It used to be set in both branches, which showed the toy "Still testing, hold
    tight" as an error, stopped polling at 8s of a 45s budget, and hid the charge
    the judge went on to award.
    """
    await judge.solve("valid-anagram")  # leaves recent worker activity on the record

    accepted = await judge.submit("two-sum", solution_for("two-sum"))
    async with TestSession() as db:
        submission = await db.get(Submission, accepted["submission_id"])
        submission.created_at = submission.created_at - timedelta(
            seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
        )
        await db.commit()

    waiting = await judge.result(accepted["submission_id"])
    assert waiting["status"] == "pending"
    assert waiting["stalled"] is False, "a working judge must not be reported as stalled"
    assert "hold tight" in waiting["sprocket_message"]

    # And it still settles normally afterwards.
    await judge.drain()
    assert (await judge.result(accepted["submission_id"]))["status"] == "passed"


async def test_a_missing_worker_still_sets_stalled(judge: Judge) -> None:
    """The case that is worth interrupting for keeps interrupting."""
    accepted = await judge.submit("two-sum", solution_for("two-sum"))
    async with TestSession() as db:
        submission = await db.get(Submission, accepted["submission_id"])
        submission.created_at = submission.created_at - timedelta(
            seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
        )
        await db.commit()

    stalled = await judge.result(accepted["submission_id"])
    assert stalled["stalled"] is True
    assert "app.judge.worker" in stalled["sprocket_message"]


# ---- a run at the attempt ceiling must not be stranded ----------------------
async def test_a_run_stranded_at_the_attempt_ceiling_is_given_up_on(judge: Judge) -> None:
    """`claim_batch` skips rows at the ceiling, so nothing would ever resolve them.

    A worker killed during a submission's final attempt left it `running`
    forever: never reclaimed, never judged, and the toy told to start a worker
    that could not have helped.
    """
    accepted = await judge.submit("two-sum", solution_for("two-sum"))

    async with TestSession() as db:
        submission = await db.get(Submission, accepted["submission_id"])
        submission.status = SubmissionStatus.RUNNING
        submission.attempts = settings.JUDGE_MAX_ATTEMPTS
        submission.claimed_at = datetime.now(UTC) - timedelta(
            seconds=settings.JUDGE_STALE_CLAIM_SECONDS + 30
        )
        await db.commit()

    # A normal drain cannot touch it — that is the bug.
    assert await judge.drain() == 0
    assert (await judge.result(accepted["submission_id"]))["status"] == "running"

    async with TestSession() as db:
        assert await abandon_exhausted(db) == 1

    done = await judge.result(accepted["submission_id"])
    assert done["status"] == "error"
    assert done["xp_awarded"] == 0
    assert "gave up" in (done["failure"] or {}).get("error", "")

    # Settled, so it will not be picked up or paid later.
    async with TestSession() as db:
        row = await db.scalar(
            select(Submission).where(Submission.id == accepted["submission_id"])
        )
        assert row.settled_at is not None


async def test_abandon_exhausted_leaves_healthy_rows_alone(judge: Judge) -> None:
    accepted = await judge.submit("two-sum", solution_for("two-sum"))
    async with TestSession() as db:
        assert await abandon_exhausted(db) == 0
    await judge.drain()
    assert (await judge.result(accepted["submission_id"]))["status"] == "passed"


# ---- True must never satisfy an expected 1 ---------------------------------
@pytest.mark.parametrize(
    ("actual", "expected", "mode"),
    [
        (True, 1, "exact"),
        (1, True, "exact"),
        ([True], [1], "exact"),
        ([1, True], [1, 1], "exact"),
        ([True, 2], [1, 2], "unordered"),
        ([[True]], [[1]], "exact"),
        ({"a": True}, {"a": 1}, "exact"),
    ],
)
def test_booleans_do_not_pass_for_integers(actual, expected, mode) -> None:
    """Python says `True == 1`; a graded answer should not.

    The guard was top-level only, so a list of ints — which is what most of these
    problems return — accepted booleans, and `unordered` skipped it entirely.
    """
    assert _matches(actual, expected, mode) is False


@pytest.mark.parametrize(
    ("actual", "expected", "mode"),
    [
        ([0, 1], [0, 1], "exact"),
        (True, True, "exact"),
        ([1, 2], [2, 1], "unordered"),
        ([[1, 2], [3]], [[3], [1, 2]], "unordered"),
        (3, 3, "exact"),
        ("ab", "ab", "exact"),
        ([], [], "exact"),
    ],
)
def test_genuine_matches_still_match(actual, expected, mode) -> None:
    assert _matches(actual, expected, mode) is True


def test_unordered_falls_back_when_the_answer_cannot_be_sorted() -> None:
    assert _matches(5, 5, "unordered") is True
    assert _matches(5, 6, "unordered") is False


# ---- entrypoint validation --------------------------------------------------
@pytest.mark.parametrize("entrypoint", ["class", "def", "return", "None", "import"])
def test_a_keyword_entrypoint_is_rejected(entrypoint: str) -> None:
    """`"class".isidentifier()` is True, so the keyword check is load-bearing.

    Without it a mis-seeded entrypoint compiles to nothing and presents as every
    submission failing, rather than as the configuration mistake it is.
    """
    with pytest.raises(ValueError, match="not a usable Python identifier"):
        build_program(entrypoint=entrypoint, preamble="", code="pass")


def test_a_normal_entrypoint_is_accepted() -> None:
    program = build_program(entrypoint="twoSum", preamble="", code="def twoSum(a, b): return []")
    assert "twoSum(*_build(" in program


# ---- the driver's report cannot be overwritten ------------------------------
def test_the_first_report_for_a_case_wins() -> None:
    """Submitted code can write to fd 1; it must not be able to revise a result."""
    stdout = (
        '{"ordinal": 0, "actual": [9, 9], "stdout": "", "error": null}\n'
        '{"ordinal": 0, "actual": [0, 1], "stdout": "", "error": null}\n'
    )
    outcomes = parse_results(stdout)
    assert outcomes[0].actual == [9, 9], "a later line overwrote the driver's own result"


def test_a_forged_overwrite_cannot_turn_a_fail_into_a_pass() -> None:
    cases = [{"ordinal": 0, "args": [[2, 7], 9], "expected": [0, 1], "visibility": "hidden"}]
    run = RunResult(
        outcomes=parse_results(
            '{"ordinal": 0, "actual": [9, 9], "stdout": "", "error": null}\n'
            '{"ordinal": 0, "actual": [0, 1], "stdout": "", "error": null}\n'
        )
    )
    assert grade(run, cases).status == SubmissionStatus.FAILED
