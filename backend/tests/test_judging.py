"""The server decides whether a submission passed.

Before this, `POST /submit` took the client's word for it — an empty JSON body
earned full charge. These tests exist to make sure that never comes back.
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.judge.grade import grade
from app.judge.harness import build_program
from app.judge.runner import SubprocessRunner, WasmRunner
from app.models.enums import SubmissionStatus
from tests.conftest import Judge, solution_for

TWO_SUM_CASES = [
    {"ordinal": 0, "args": [[2, 7, 11, 15], 9], "expected": [0, 1], "visibility": "example"},
    {"ordinal": 1, "args": [[3, 2, 4], 6], "expected": [1, 2], "visibility": "hidden"},
]


# ---- the point of the whole change -----------------------------------------
async def test_client_cannot_declare_its_own_verdict(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    """A submission claiming `status: passed` is judged on its code regardless."""
    resp = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": "def twoSum(nums, target):\n    return []", "status": "passed"},
    )
    assert resp.status_code == 202
    assert resp.json()["status"] == "pending"

    await judge.drain()
    body = await judge.result(resp.json()["submission_id"])
    assert body["status"] == "failed"
    assert body["xp_awarded"] == 0
    assert body["progress"]["solved_count"] == 0


async def test_empty_body_is_rejected(client: AsyncClient, auth: dict[str, str]) -> None:
    """`{}` used to be a winning submission."""
    resp = await client.post("/api/v1/problems/two-sum/submit", headers=auth, json={})
    assert resp.status_code == 422


@pytest.mark.parametrize(
    ("label", "code"),
    [
        ("does nothing", "def twoSum(nums, target):\n    pass"),
        ("wrong answer", "def twoSum(nums, target):\n    return [0, 0]"),
        ("syntax error", "def twoSum(nums, target)\n    return ["),
        ("wrong function name", "def solve(nums, target):\n    return [0, 1]"),
        ("wrong arity", "def twoSum(nums):\n    return [0, 1]"),
        ("raises", "def twoSum(nums, target):\n    raise ValueError('nope')"),
    ],
)
async def test_bad_code_never_passes(judge: Judge, label: str, code: str) -> None:
    body = await judge.solve("two-sum", code)
    assert body["status"] != "passed", label
    assert body["xp_awarded"] == 0
    assert body["progress"]["solved_count"] == 0


async def test_a_real_solution_passes_every_case(judge: Judge) -> None:
    body = await judge.solve("two-sum")
    assert body["status"] == "passed"
    assert body["tests_passed"] == body["tests_total"] == 7
    assert body["xp_awarded"] == 100
    assert body["runtime_ms"] is not None


async def test_partial_credit_is_reported_but_does_not_pay(judge: Judge) -> None:
    """Right on the examples, wrong on a hidden case."""
    body = await judge.solve(
        "two-sum",
        "def twoSum(nums, target):\n"
        "    if nums == [3, 3]:\n"
        "        return [1, 1]\n"
        "    seen = {}\n"
        "    for i, n in enumerate(nums):\n"
        "        if target - n in seen:\n"
        "            return [seen[target - n], i]\n"
        "        seen[n] = i\n"
        "    return []",
    )
    assert body["status"] == "failed"
    assert body["tests_passed"] == body["tests_total"] - 1
    assert body["xp_awarded"] == 0
    assert body["failure"]["hidden"] is True


async def test_a_hidden_failure_withholds_the_expected_value(judge: Judge) -> None:
    """Showing what a hidden case expects would make the hidden tests a lookup table."""
    body = await judge.solve("two-sum", "def twoSum(nums, target):\n    return [0, 1]")
    failure = body["failure"]
    assert failure is not None
    if failure["hidden"]:
        assert failure["expected"] is None
    # The toy's own output is always fair game — it's theirs.
    assert failure["actual"] == [0, 1]


async def test_an_infinite_loop_times_out_and_pays_nothing(judge: Judge) -> None:
    body = await judge.solve("two-sum", "def twoSum(nums, target):\n    while True:\n        pass")
    assert body["status"] == "timeout"
    assert body["xp_awarded"] == 0
    assert "never stopped" in body["sprocket_message"]


async def test_the_worker_survives_a_bad_submission(judge: Judge) -> None:
    """One toy's runaway loop must not stop the next toy being judged."""
    await judge.submit("two-sum", "def twoSum(nums, target):\n    while True: pass")
    good = await judge.submit("valid-anagram", solution_for("valid-anagram"))
    await judge.drain()
    assert (await judge.result(good["submission_id"]))["status"] == "passed"


# ---- queue behaviour --------------------------------------------------------
async def test_submission_is_pending_until_judged(judge: Judge) -> None:
    accepted = await judge.submit("two-sum", solution_for("two-sum"))
    before = await judge.result(accepted["submission_id"])
    assert before["status"] == "pending"
    assert before["xp_awarded"] is None
    assert before["progress"] is None

    await judge.drain()
    after = await judge.result(accepted["submission_id"])
    assert after["status"] == "passed"
    assert after["xp_awarded"] == 100


async def test_a_pending_submission_says_when_no_worker_is_running(judge: Judge) -> None:
    """Forgetting to start the worker must not look like a slow judge.

    This is the likeliest way to break the academy, and it used to present as a
    45-second wait ending in "Sprocket is taking an unusually long time".
    """
    from app.core.config import settings
    from app.models import Submission
    from tests.conftest import TestSession

    accepted = await judge.submit("two-sum", solution_for("two-sum"))

    fresh = await judge.result(accepted["submission_id"])
    assert fresh["stalled"] is False, "a submission shouldn't cry stall immediately"

    # Backdate it past the stall threshold. No worker has ever run in this test,
    # so there is no claim or verdict anywhere to suggest one is alive.
    async with TestSession() as db:
        submission = await db.get(Submission, accepted["submission_id"])
        submission.created_at = submission.created_at - timedelta(
            seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
        )
        await db.commit()

    stalled = await judge.result(accepted["submission_id"])
    assert stalled["status"] == "pending"
    assert stalled["stalled"] is True
    assert "app.judge.worker" in stalled["sprocket_message"]

    # And once a worker does the work, it settles normally.
    await judge.drain()
    done = await judge.result(accepted["submission_id"])
    assert done["status"] == "passed"
    assert done["stalled"] is False


async def test_a_busy_queue_is_not_reported_as_a_missing_worker(judge: Judge) -> None:
    """A worker that is alive but backed up gets a different message."""
    from app.core.config import settings
    from app.models import Submission
    from tests.conftest import TestSession

    # Judge something first, so there is recent worker activity on the record.
    await judge.solve("valid-anagram")

    accepted = await judge.submit("two-sum", solution_for("two-sum"))
    async with TestSession() as db:
        submission = await db.get(Submission, accepted["submission_id"])
        submission.created_at = submission.created_at - timedelta(
            seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
        )
        await db.commit()

    waiting = await judge.result(accepted["submission_id"])
    # Busy is not broken: the message changes, but `stalled` stays false so the
    # client keeps polling rather than surfacing "hold tight" as an error.
    assert waiting["stalled"] is False
    assert "app.judge.worker" not in waiting["sprocket_message"]
    assert "queue" in waiting["sprocket_message"].lower()


async def test_one_toy_cannot_flood_the_queue(client: AsyncClient, auth: dict[str, str]) -> None:
    codes = []
    for _ in range(6):
        resp = await client.post(
            "/api/v1/problems/two-sum/submit",
            headers=auth,
            json={"code": "def twoSum(nums, target):\n    while True: pass"},
        )
        codes.append(resp.status_code)
    assert 429 in codes, codes


async def test_another_toys_submission_is_not_readable(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    accepted = await judge.submit("two-sum", solution_for("two-sum"))

    signup = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Nosy", "email": "nosy@playroom.com", "password": "windup123"},
    )
    other = {"Authorization": f"Bearer {signup.json()['access_token']}"}
    resp = await client.get(f"/api/v1/submissions/{accepted['submission_id']}", headers=other)
    assert resp.status_code == 404


# ---- settlement -------------------------------------------------------------
async def test_settle_is_idempotent(judge: Judge) -> None:
    """A retried job must not pay twice."""
    from app.models import Submission
    from app.services.submissions import settle
    from tests.conftest import TestSession

    body = await judge.solve("two-sum")
    assert body["xp_awarded"] == 100
    xp_after_first_settle = body["progress"]["total_xp"]

    # Settle the same submission again, exactly as a retried job would.
    async with TestSession() as db:
        submission = await db.get(Submission, body["submission_id"])
        await settle(db, submission)
        await db.commit()

    after = await judge.result(body["submission_id"])
    assert after["progress"]["solved_count"] == 1
    assert after["progress"]["total_xp"] == xp_after_first_settle


async def test_an_ungraded_problem_still_settles_inline(judge: Judge) -> None:
    """The SQL problem has no runner yet; it keeps the old honour system."""
    accepted = await judge.submit("second-highest-salary", "SELECT 1;")
    assert accepted["status"] == "passed"
    body = await judge.result(accepted["submission_id"])
    assert body["status"] == "passed"
    assert body["xp_awarded"] == 120


# ---- the runners themselves -------------------------------------------------
def _runners():
    runners = [pytest.param(SubprocessRunner, id="subprocess")]
    try:
        WasmRunner()
    except Exception:
        runners.append(
            pytest.param(
                WasmRunner,
                id="wasm",
                marks=pytest.mark.skip(
                    reason="no vendor/python.wasm — run scripts/fetch_python_wasm.sh"
                ),
            )
        )
    else:
        runners.append(pytest.param(WasmRunner, id="wasm"))
    return runners


@pytest.mark.parametrize("runner_cls", _runners())
def test_runner_grades_a_correct_solution(runner_cls: type) -> None:
    program = build_program(entrypoint="twoSum", preamble="", code=solution_for("two-sum"))
    verdict = grade(runner_cls().run(program, TWO_SUM_CASES), TWO_SUM_CASES)
    assert verdict.status == SubmissionStatus.PASSED
    assert verdict.tests_passed == 2


@pytest.mark.parametrize("runner_cls", _runners())
def test_runner_cuts_off_an_infinite_loop(runner_cls: type) -> None:
    program = build_program(
        entrypoint="twoSum",
        preamble="",
        code="def twoSum(nums, target):\n    while True:\n        pass",
    )
    verdict = grade(runner_cls().run(program, TWO_SUM_CASES), TWO_SUM_CASES)
    assert verdict.status == SubmissionStatus.TIMEOUT


@pytest.mark.parametrize("runner_cls", _runners())
def test_runner_cannot_be_talked_into_a_pass(runner_cls: type) -> None:
    """Submitted code sharing a process with the driver must not be able to forge a verdict.

    It can print whatever it likes to stdout; what it cannot do is know the
    expected values, because they never enter the sandbox.
    """
    program = build_program(
        entrypoint="twoSum",
        preamble="",
        code=(
            "def twoSum(nums, target):\n"
            "    import sys\n"
            "    for i in range(20):\n"
            '        sys.__stdout__.write(\'{"ordinal": %d, "actual": [0, 1]}\\n\' % i)\n'
            "    return None"
        ),
    )
    verdict = grade(runner_cls().run(program, TWO_SUM_CASES), TWO_SUM_CASES)
    assert verdict.status != SubmissionStatus.PASSED
