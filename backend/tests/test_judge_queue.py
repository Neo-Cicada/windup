"""The submissions table as a queue.

`claim_batch` is the whole broker: FOR UPDATE SKIP LOCKED, a stale-claim sweep so
a killed worker doesn't strand a run, and an attempt ceiling so a submission that
keeps blowing the judge up stops being retried. These tests drive it directly —
`test_judging.py` only ever sees the happy drain.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.judge.grade import Verdict
from app.judge.harness import RunResult
from app.judge.runner import SubprocessRunner
from app.judge.worker import claim_batch, judge_submission, process_one, run_forever
from app.models import Problem, Submission, SubmissionStatus, User, Zone
from tests.conftest import Judge, TestSession, solution_for


def _seeded_problems() -> list[dict[str, Any]]:
    from app.db.seed_data import PROBLEMS

    return PROBLEMS


async def _user_id(db: AsyncSession) -> uuid.UUID:
    user = await db.scalar(select(User).where(User.email == "patches@playroom.com"))
    assert user is not None, "the auth fixture signs this toy up"
    return user.id


async def _queue(
    db: AsyncSession,
    user_id: uuid.UUID,
    slug: str = "two-sum",
    *,
    code: str = "def twoSum(nums, target):\n    return []",
    status: str = SubmissionStatus.PENDING,
    **fields: Any,
) -> Submission:
    problem_id = await db.scalar(select(Problem.id).where(Problem.slug == slug))
    submission = Submission(
        user_id=user_id,
        problem_id=problem_id,
        code=code,
        language="python",
        status=status,
        unaided=True,
        **fields,
    )
    db.add(submission)
    await db.commit()
    return submission


class BoomRunner:
    """A sandbox that fails to run at all, the way a broken host would."""

    def __init__(self) -> None:
        self.calls = 0

    def run(self, program: str, cases: list[dict[str, Any]]) -> RunResult:
        self.calls += 1
        raise OSError("wasmtime is not having a good day")


# ---- claiming ---------------------------------------------------------------
async def test_claim_batch_takes_pending_work_and_marks_it_running(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    user_id = await _user_id(db)
    for _ in range(3):
        await _queue(db, user_id)

    async with TestSession() as worker_db:
        claimed = await claim_batch(worker_db, 10)
    assert len(claimed) == 3
    assert {s.status for s in claimed} == {SubmissionStatus.RUNNING}
    assert {s.attempts for s in claimed} == {1}
    assert all(s.claimed_at is not None for s in claimed)

    async with TestSession() as worker_db:
        assert await claim_batch(worker_db, 10) == [], "a running claim is not up for grabs"


async def test_claim_batch_honours_its_limit_oldest_first(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    user_id = await _user_id(db)
    first = await _queue(db, user_id)
    await _queue(db, user_id)
    # Make the ordering unambiguous rather than relying on clock resolution.
    first.created_at = first.created_at - timedelta(minutes=5)
    await db.commit()

    async with TestSession() as worker_db:
        claimed = await claim_batch(worker_db, 1)
    assert [s.id for s in claimed] == [first.id]


async def test_a_fresh_claim_is_left_alone_and_a_stale_one_is_reclaimed(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    """A worker killed mid-run would otherwise strand its submission forever."""
    user_id = await _user_id(db)
    now = datetime.now(UTC)
    fresh = await _queue(
        db, user_id, status=SubmissionStatus.RUNNING, claimed_at=now, attempts=1
    )
    stale = await _queue(
        db,
        user_id,
        status=SubmissionStatus.RUNNING,
        claimed_at=now - timedelta(seconds=settings.JUDGE_STALE_CLAIM_SECONDS + 30),
        attempts=1,
    )

    async with TestSession() as worker_db:
        claimed = await claim_batch(worker_db, 10)
    assert [s.id for s in claimed] == [stale.id]
    assert claimed[0].attempts == 2, "a reclaim counts as another attempt"

    await db.refresh(fresh)
    assert fresh.attempts == 1


async def test_a_submission_at_the_attempt_ceiling_is_never_claimed_again(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    """JUDGE_MAX_ATTEMPTS is what stops one poisonous run being retried forever."""
    user_id = await _user_id(db)
    burnt = await _queue(db, user_id, attempts=settings.JUDGE_MAX_ATTEMPTS)
    live = await _queue(db, user_id, attempts=settings.JUDGE_MAX_ATTEMPTS - 1)

    async with TestSession() as worker_db:
        claimed = await claim_batch(worker_db, 10)
    assert [s.id for s in claimed] == [live.id]

    await db.refresh(burnt)
    assert burnt.status == SubmissionStatus.PENDING
    assert burnt.attempts == settings.JUDGE_MAX_ATTEMPTS


async def test_a_judged_submission_is_not_claimed_again(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    user_id = await _user_id(db)
    for status in (SubmissionStatus.PASSED, SubmissionStatus.FAILED, SubmissionStatus.ERROR,
                   SubmissionStatus.TIMEOUT):
        await _queue(db, user_id, status=status, judged_at=datetime.now(UTC))

    async with TestSession() as worker_db:
        assert await claim_batch(worker_db, 10) == []


async def test_two_workers_never_take_the_same_row(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    """SKIP LOCKED is the reason scaling the judge needs no broker."""
    user_id = await _user_id(db)
    queued = [(await _queue(db, user_id)).id for _ in range(6)]

    async with TestSession() as one, TestSession() as two:
        first, second = await asyncio.gather(claim_batch(one, 6), claim_batch(two, 6))

    taken = [s.id for s in first] + [s.id for s in second]
    assert len(taken) == len(set(taken)), "the same submission was claimed twice"
    assert set(taken) == set(queued)


async def test_a_locked_row_is_skipped_rather_than_waited_on(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    """Deterministic proof of SKIP LOCKED: hold one row's lock open, claim the rest."""
    user_id = await _user_id(db)
    locked = await _queue(db, user_id)
    other = await _queue(db, user_id)

    async with TestSession() as holder:
        held = await holder.scalar(
            select(Submission).where(Submission.id == locked.id).with_for_update()
        )
        assert held is not None  # transaction now holds the row lock

        async with TestSession() as worker_db:
            claimed = await asyncio.wait_for(claim_batch(worker_db, 10), timeout=10)
        assert [s.id for s in claimed] == [other.id]
        await holder.rollback()

    # Once the lock is gone the skipped row is claimable as normal.
    async with TestSession() as worker_db:
        assert [s.id for s in await claim_batch(worker_db, 10)] == [locked.id]


# ---- retries ----------------------------------------------------------------
async def test_a_judge_that_blows_up_puts_the_submission_back(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    user_id = await _user_id(db)
    submission = await _queue(db, user_id)

    async with TestSession() as worker_db:
        await claim_batch(worker_db, 10)
    runner = BoomRunner()
    async with TestSession() as worker_db:
        await process_one(worker_db, runner, submission.id)

    assert runner.calls == 1
    await db.refresh(submission)
    assert submission.status == SubmissionStatus.PENDING
    assert submission.claimed_at is None
    assert submission.judged_at is None
    assert submission.settled_at is None
    assert submission.attempts == 1, "the attempt still counts"


async def test_the_last_attempt_settles_as_an_error_rather_than_looping(
    db: AsyncSession, auth: dict[str, str], judge: Judge
) -> None:
    """Otherwise the toy polls a submission that will never be answered."""
    user_id = await _user_id(db)
    submission = await _queue(db, user_id, attempts=settings.JUDGE_MAX_ATTEMPTS - 1)

    async with TestSession() as worker_db:
        await claim_batch(worker_db, 10)
    async with TestSession() as worker_db:
        await process_one(worker_db, BoomRunner(), submission.id)

    await db.refresh(submission)
    assert submission.attempts == settings.JUDGE_MAX_ATTEMPTS
    assert submission.status == SubmissionStatus.ERROR
    assert submission.judged_at is not None
    assert submission.settled_at is not None
    assert submission.xp_awarded == 0

    body = await judge.result(str(submission.id))
    assert body["status"] == "error"
    assert body["stalled"] is False
    assert body["failure"]["error"] == "The test rig jammed. Sprocket has been told."


# ---- a graded problem with no rig -------------------------------------------
async def test_a_graded_problem_with_no_test_cases_cannot_be_solved(
    db: AsyncSession, client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    """Zero cases means "every case passed" to a naive loop. It must not pay out."""
    zone_id = await db.scalar(select(Zone.id).limit(1))
    db.add(
        Problem(
            zone_id=zone_id,
            slug="unrigged-toy",
            title="Unrigged Toy",
            prompt="Sprocket hasn't written the cases yet.",
            entrypoint="solve",
            graded=True,
            xp_reward=999,
        )
    )
    await db.commit()

    body = await judge.solve("unrigged-toy", "def solve():\n    return 1")
    assert body["status"] == "error"
    assert body["tests_total"] == 0
    assert body["tests_passed"] == 0
    assert body["xp_awarded"] == 0
    assert body["progress"]["solved_count"] == 0
    assert "test rig" in body["failure"]["error"]

    dashboard = await client.get("/api/v1/dashboard", headers=auth)
    assert dashboard.status_code == 200
    assert dashboard.json()["progress"]["total_xp"] == 0


def test_judge_submission_refuses_an_empty_rig_without_running_anything() -> None:
    """The refusal happens before the sandbox — nothing to run, nothing to trust."""
    problem = Problem(slug="bare", title="Bare", prompt="", entrypoint="solve", graded=True)
    problem.tests = []
    runner = BoomRunner()
    verdict = judge_submission(runner, Submission(code="def solve(): return 1"), problem)
    assert isinstance(verdict, Verdict)
    assert verdict.status == SubmissionStatus.ERROR
    assert verdict.tests_total == 0
    assert runner.calls == 0


def test_judge_submission_feeds_the_cases_in_ordinal_order() -> None:
    """The driver reports by ordinal, so a shuffled rig must still line up."""
    from app.models import ProblemTest

    problem = Problem(
        slug="counter", title="Counter", prompt="", entrypoint="solve", graded=True,
        harness_preamble="",
    )
    problem.tests = [
        ProblemTest(ordinal=1, args_json=[2], expected_json=4, visibility="hidden"),
        ProblemTest(ordinal=0, args_json=[1], expected_json=2, visibility="example"),
    ]
    verdict = judge_submission(
        SubprocessRunner(), Submission(code="def solve(n):\n    return n * 2"), problem
    )
    assert verdict.status == SubmissionStatus.PASSED
    assert verdict.tests_passed == 2


# ---- the worker's own loop --------------------------------------------------
async def _await_verdict(submission_id: uuid.UUID, seconds: float = 20.0) -> Submission:
    """Wait for the loop under test to rule, without polling the API."""
    deadline = asyncio.get_running_loop().time() + seconds
    while asyncio.get_running_loop().time() < deadline:
        async with TestSession() as s:
            found = await s.get(Submission, submission_id)
            if found is not None and found.judged_at is not None:
                return found
        await asyncio.sleep(0.05)
    raise AssertionError("the worker loop never judged the submission")


def _worker_against_the_test_db(monkeypatch: Any) -> None:
    """run_forever opens its own sessions, so point them at the throwaway DB."""
    monkeypatch.setattr("app.judge.worker.SessionLocal", TestSession)
    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "JUDGE_RUNNER", "subprocess")


async def test_run_forever_drains_the_queue_and_stops_when_told(
    db: AsyncSession, auth: dict[str, str], monkeypatch: Any
) -> None:
    """The loop the `worker` command actually runs, start to clean stop."""
    _worker_against_the_test_db(monkeypatch)
    user_id = await _user_id(db)
    submission = await _queue(db, user_id, code=solution_for("two-sum"))

    stop = asyncio.Event()
    loop = asyncio.create_task(run_forever(stop))
    try:
        judged = await _await_verdict(submission.id)
        assert judged.status == SubmissionStatus.PASSED
        assert judged.settled_at is not None
    finally:
        stop.set()
        await asyncio.wait_for(loop, timeout=10)
    assert loop.done() and loop.exception() is None


async def test_run_forever_keeps_going_after_a_database_hiccup(
    db: AsyncSession, auth: dict[str, str], monkeypatch: Any
) -> None:
    """A blown claim query must back off and retry, not kill the worker."""
    _worker_against_the_test_db(monkeypatch)
    monkeypatch.setattr(settings, "JUDGE_POLL_SECONDS", 0.05)
    real_claim = claim_batch
    calls = {"n": 0}

    async def flaky_claim(db_: AsyncSession, limit: int) -> list[Submission]:
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("connection reset by the playroom")
        return await real_claim(db_, limit)

    monkeypatch.setattr("app.judge.worker.claim_batch", flaky_claim)

    user_id = await _user_id(db)
    submission = await _queue(db, user_id, code=solution_for("two-sum"))

    stop = asyncio.Event()
    loop = asyncio.create_task(run_forever(stop))
    try:
        judged = await _await_verdict(submission.id)
        assert judged.status == SubmissionStatus.PASSED
    finally:
        stop.set()
        await asyncio.wait_for(loop, timeout=10)
    assert calls["n"] > 1, "the loop gave up after the first error"


# ---- polling while the queue waits ------------------------------------------
async def test_describe_wait_copes_with_a_naive_created_at(
    db: AsyncSession, auth: dict[str, str]
) -> None:
    """A timestamp read back without a tzinfo must not crash the poll."""
    from app.api.v1.endpoints.submissions import _describe_wait
    from app.schemas.academy import SubmissionResultOut

    user_id = await _user_id(db)
    submission = await _queue(db, user_id)
    submission.created_at = datetime.now(UTC).replace(tzinfo=None) - timedelta(
        seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
    )

    result = SubmissionResultOut(
        submission_id=submission.id, status=SubmissionStatus.PENDING, unaided=True
    )
    await _describe_wait(db, submission, result)
    assert result.stalled is True
    assert "app.judge.worker" in result.sprocket_message


async def test_a_backed_up_queue_counts_the_runs_ahead(
    db: AsyncSession, auth: dict[str, str], judge: Judge
) -> None:
    """The message earns its keep by saying how deep the queue is."""
    await judge.solve("valid-anagram")  # recent worker activity: one is alive

    user_id = await _user_id(db)
    ahead = await _queue(db, user_id)
    mine = await _queue(db, user_id)
    ahead.created_at = mine.created_at - timedelta(minutes=1)
    mine.created_at = datetime.now(UTC) - timedelta(
        seconds=settings.JUDGE_STALL_AFTER_SECONDS + 5
    )
    await db.commit()

    body = await judge.result(str(mine.id))
    # `stalled` tells the client to stop polling, so a judge that is demonstrably
    # alive must not set it — see test_judge_fixes.py.
    assert body["stalled"] is False
    assert "1 run ahead" in body["sprocket_message"]


async def test_an_unknown_submission_id_is_404(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get(f"/api/v1/submissions/{uuid.uuid4()}", headers=auth)
    assert resp.status_code == 404


async def test_polling_needs_a_session(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get(f"/api/v1/submissions/{uuid.uuid4()}")
    assert resp.status_code == 401


# ---- the queue cap ----------------------------------------------------------
async def test_the_pending_cap_frees_up_once_the_judge_catches_up(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    """The 429 is a queue-depth cap, not a per-day quota."""
    for _ in range(settings.JUDGE_MAX_PENDING_PER_USER):
        await judge.submit("two-sum", "def twoSum(nums, target):\n    return []")

    blocked = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": "def twoSum(nums, target):\n    return []"},
    )
    assert blocked.status_code == 429

    await judge.drain()
    accepted = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": solution_for("two-sum")},
    )
    assert accepted.status_code == 202
    assert accepted.json()["queue_position"] == 0


# ---- the seeded catalogue ---------------------------------------------------
GRADED_SLUGS = [p["slug"] for p in _seeded_problems() if p.get("graded", True)]


@pytest.mark.parametrize("slug", GRADED_SLUGS)
async def test_every_seeded_reference_solution_passes_its_own_rig(
    judge: Judge, slug: str
) -> None:
    """The rig itself under test: 61 cases, three harness preambles, nine entrypoints.

    A wrong expected value or a preamble whose `_build` doesn't match its
    starter code makes the problem unsolvable, and nothing else would notice.
    """
    body = await judge.solve(slug)
    assert body["status"] == "passed", body["failure"]
    assert body["tests_total"] > 0
    assert body["tests_passed"] == body["tests_total"]


@pytest.mark.parametrize("slug", GRADED_SLUGS)
async def test_the_starter_code_never_passes_by_accident(judge: Judge, slug: str) -> None:
    """The stub a toy is handed must not already be a solve."""
    starter = next(p for p in _seeded_problems() if p["slug"] == slug).get("starter_code", "")
    body = await judge.solve(slug, starter)
    assert body["status"] != "passed"
    assert body["xp_awarded"] == 0
