"""Settlement under concurrency, and the ordering of the already-paid probe.

Both of these were real bugs. `settle()` did a read-modify-write on the shared
`progress` row with no lock, so two workers settling for one toy lost a solve;
and the already-paid probe counted any other passing run rather than one that had
actually been paid, so two unsettled passing runs each deferred to the other and
neither paid.

The worker's documented scaling story is "start more processes", which makes both
reachable rather than theoretical.
"""

import asyncio

from sqlalchemy import func, select

from app.models import Progress, Submission, SubmissionStatus, XpEvent
from app.services.submissions import settle
from tests.conftest import Judge, TestSession, solution_for


async def _judged_unsettled(user_id, problem_id) -> Submission:
    """A submission in the state a worker hands to settle()."""
    async with TestSession() as db:
        submission = Submission(
            user_id=user_id,
            problem_id=problem_id,
            code="whatever",
            language="python",
            status=SubmissionStatus.PASSED,
            unaided=True,
            tests_passed=7,
            tests_total=7,
            judged_at=func.now(),
        )
        db.add(submission)
        await db.commit()
        return submission.id


async def _settle_alone(submission_id, barrier: asyncio.Barrier) -> int:
    """Settle in a session of its own, after both racers have read."""
    async with TestSession() as db:
        submission = await db.scalar(
            select(Submission).where(Submission.id == submission_id)
        )
        await barrier.wait()
        settlement = await settle(db, submission)
        await db.commit()
        return settlement.xp_awarded


async def _totals(user_id) -> tuple[int, int, int]:
    async with TestSession() as db:
        progress = await db.scalar(select(Progress).where(Progress.user_id == user_id))
        ledger = int(
            await db.scalar(
                select(func.coalesce(func.sum(XpEvent.amount), 0)).where(
                    XpEvent.user_id == user_id
                )
            )
        )
        return progress.solved_count, progress.total_xp, ledger


async def _ids(client, auth) -> tuple:
    me = (await client.get("/api/v1/me", headers=auth)).json()
    problems = (await client.get("/api/v1/problems", headers=auth)).json()
    return me["id"], {p["slug"]: p["id"] for p in problems}


async def test_concurrent_settlement_of_two_problems_keeps_the_counters_honest(
    client, auth
) -> None:
    """Two genuine first solves settled at once must both count.

    The failure this pins: both reported paying 100 while progress recorded a
    single solve and 100 total, because the second commit clobbered the first.
    """
    user_id, by_slug = await _ids(client, auth)
    a = await _judged_unsettled(user_id, by_slug["two-sum"])
    b = await _judged_unsettled(user_id, by_slug["valid-anagram"])

    barrier = asyncio.Barrier(2)
    paid = await asyncio.gather(_settle_alone(a, barrier), _settle_alone(b, barrier))

    assert sorted(paid) == [100, 100], paid
    solved, total_xp, ledger = await _totals(user_id)
    assert solved == 2, f"a solve went missing: solved_count={solved}"
    # The ledger is the append-only source of truth; the counter must agree.
    assert total_xp == ledger, f"progress.total_xp={total_xp} but ledger={ledger}"


async def test_concurrent_settlement_of_one_problem_pays_exactly_once(client, auth) -> None:
    user_id, by_slug = await _ids(client, auth)
    a = await _judged_unsettled(user_id, by_slug["two-sum"])
    b = await _judged_unsettled(user_id, by_slug["two-sum"])

    barrier = asyncio.Barrier(2)
    paid = await asyncio.gather(_settle_alone(a, barrier), _settle_alone(b, barrier))

    assert sorted(paid) == [0, 100], f"one and only one run should pay: {paid}"
    solved, total_xp, ledger = await _totals(user_id)
    assert solved == 1
    assert total_xp == ledger


async def test_two_unsettled_passing_runs_do_not_both_defer(client, auth) -> None:
    """Neither-pays was the failure here, and it is not a concurrency bug.

    Settled strictly one after the other, with two passing rows already on the
    record, the probe used to find "another passing submission" from *both*
    sides and pay nothing at all.
    """
    user_id, by_slug = await _ids(client, auth)
    a = await _judged_unsettled(user_id, by_slug["climbing-stairs"])
    b = await _judged_unsettled(user_id, by_slug["climbing-stairs"])

    paid = []
    for submission_id in (a, b):
        async with TestSession() as db:
            submission = await db.scalar(
                select(Submission).where(Submission.id == submission_id)
            )
            paid.append((await settle(db, submission)).xp_awarded)
            await db.commit()

    assert paid == [100, 0], f"the first should pay and the second should not: {paid}"
    solved, total_xp, ledger = await _totals(user_id)
    assert solved == 1
    assert total_xp == ledger


async def test_settling_through_the_real_worker_stays_consistent(judge: Judge) -> None:
    """End to end, via process_one, with several runs in flight at once."""
    for slug in ("two-sum", "valid-anagram", "valid-parentheses"):
        await judge.submit(slug, solution_for(slug))
    await judge.drain()

    async with TestSession() as db:
        progress = await db.scalar(select(Progress))
        ledger = int(
            await db.scalar(select(func.coalesce(func.sum(XpEvent.amount), 0)))
        )
    assert progress.solved_count == 3
    assert progress.total_xp == ledger
