"""The judge worker: `uv run python -m app.judge.worker`.

Claims pending submissions with FOR UPDATE SKIP LOCKED, runs them in a sandbox,
records the verdict and pays out. Scale by starting more worker processes —
SKIP LOCKED means two workers never take the same row, so no broker is needed
beyond the Postgres that is already there.

Nothing here runs inside the API process. That separation is the point: a
submission full of infinite loops burns a worker, not the event loop serving
everyone else's dashboard.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import logging
import signal
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.judge.grade import Verdict, grade
from app.judge.harness import build_program
from app.judge.runner import Runner, get_runner
from app.models import Problem, Submission, SubmissionStatus
from app.services.submissions import settle

log = logging.getLogger("windup.judge")


async def abandon_exhausted(db: AsyncSession) -> int:
    """Give up on runs that can neither progress nor be reclaimed.

    `claim_batch` only takes rows below the attempt ceiling, so a worker killed
    during a submission's *final* attempt leaves it `running` forever: never
    reclaimed, never judged. The toy is then told no worker is running and to
    start one, advice that can never help it, while its code sits there.
    """
    stale_before = datetime.now(UTC) - timedelta(seconds=settings.JUDGE_STALE_CLAIM_SECONDS)
    stranded = list(
        (
            await db.scalars(
                select(Submission).where(
                    Submission.status == SubmissionStatus.RUNNING,
                    Submission.claimed_at < stale_before,
                    Submission.attempts >= settings.JUDGE_MAX_ATTEMPTS,
                )
            )
        ).all()
    )
    for submission in stranded:
        submission.status = SubmissionStatus.ERROR
        submission.judged_at = datetime.now(UTC)
        submission.claimed_at = None
        submission.failure_json = {
            "error": "The test rig gave up on this one after too many tries. Submit it again."
        }
        await settle(db, submission)
        log.warning("abandoned %s after %d attempts", submission.id, submission.attempts)
    if stranded:
        await db.commit()
    return len(stranded)


async def claim_batch(db: AsyncSession, limit: int) -> list[Submission]:
    """Take up to `limit` submissions off the queue, exclusively.

    Picks up rows that are pending, plus rows whose claim has gone stale — a
    worker killed mid-run would otherwise strand its submission forever.
    """
    stale_before = datetime.now(UTC) - timedelta(seconds=settings.JUDGE_STALE_CLAIM_SECONDS)
    stmt = (
        select(Submission)
        .where(
            or_(
                Submission.status == SubmissionStatus.PENDING,
                (Submission.status == SubmissionStatus.RUNNING)
                & (Submission.claimed_at < stale_before),
            ),
            Submission.attempts < settings.JUDGE_MAX_ATTEMPTS,
        )
        .order_by(Submission.created_at)
        .limit(limit)
        .with_for_update(skip_locked=True)
    )
    rows = list((await db.scalars(stmt)).all())
    now = datetime.now(UTC)
    for row in rows:
        row.status = SubmissionStatus.RUNNING
        row.claimed_at = now
        row.attempts += 1
    await db.commit()
    return rows


def judge_submission(runner: Runner, submission: Submission, problem: Problem) -> Verdict:
    """Run one submission and grade it. Pure — no database access."""
    cases = [
        {
            "ordinal": t.ordinal,
            "args": t.args_json,
            "expected": t.expected_json,
            "visibility": t.visibility,
            "label": t.label,
        }
        for t in sorted(problem.tests, key=lambda t: t.ordinal)
    ]
    if not cases:
        # A graded problem with no cases would otherwise pass everything by
        # vacuous truth. Refuse instead.
        return Verdict(
            status=SubmissionStatus.ERROR,
            tests_passed=0,
            tests_total=0,
            runtime_ms=0,
            failure={"error": "This toy has no test rig yet — Sprocket is still building it."},
        )

    program = build_program(
        entrypoint=problem.entrypoint,
        preamble=problem.harness_preamble,
        code=submission.code,
    )
    return grade(runner.run(program, cases), cases, compare_mode=problem.compare_mode)


async def process_one(db: AsyncSession, runner: Runner, submission_id) -> None:
    submission = await db.scalar(
        select(Submission)
        .options(selectinload(Submission.problem).selectinload(Problem.tests))
        .where(Submission.id == submission_id)
    )
    if submission is None:  # pragma: no cover - deleted mid-flight
        return

    problem = submission.problem
    try:
        # The sandbox call is blocking; keep it off the event loop so one slow
        # submission doesn't stall this worker's other bookkeeping.
        verdict = await asyncio.to_thread(judge_submission, runner, submission, problem)
    except Exception:
        log.exception("judging %s blew up", submission.id)
        if submission.attempts >= settings.JUDGE_MAX_ATTEMPTS:
            verdict = Verdict(
                status=SubmissionStatus.ERROR,
                tests_passed=0,
                tests_total=len(problem.tests),
                runtime_ms=0,
                failure={"error": "The test rig jammed. Sprocket has been told."},
            )
        else:
            # Put it back for another worker to retry.
            submission.status = SubmissionStatus.PENDING
            submission.claimed_at = None
            await db.commit()
            return

    submission.status = verdict.status
    submission.tests_passed = verdict.tests_passed
    submission.tests_total = verdict.tests_total
    submission.runtime_ms = verdict.runtime_ms
    submission.failure_json = verdict.failure
    submission.judged_at = datetime.now(UTC)
    submission.claimed_at = None

    # Payout happens here, atomically with the verdict — see services/submissions.py.
    await settle(db, submission)
    await db.commit()
    log.info(
        "judged %s %s %d/%d in %dms",
        submission.id,
        verdict.status.value,
        verdict.tests_passed,
        verdict.tests_total,
        verdict.runtime_ms,
    )


async def run_forever(stop: asyncio.Event) -> None:
    runner = get_runner()
    log.info("judge worker up, runner=%s", settings.JUDGE_RUNNER)

    while not stop.is_set():
        try:
            async with SessionLocal() as db:
                await abandon_exhausted(db)
                claimed = await claim_batch(db, settings.JUDGE_BATCH_SIZE)
                ids = [s.id for s in claimed]
            if not ids:
                with contextlib.suppress(TimeoutError):
                    await asyncio.wait_for(stop.wait(), timeout=settings.JUDGE_POLL_SECONDS)
                continue
            for submission_id in ids:
                async with SessionLocal() as db:
                    await process_one(db, runner, submission_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("worker loop error; backing off")
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=2.0)

    log.info("judge worker stopping")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Windup Academy judge worker")
    parser.add_argument("--once", action="store_true", help="drain the queue and exit")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)-7s %(name)s: %(message)s"
    )

    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        with contextlib.suppress(NotImplementedError):
            loop.add_signal_handler(sig, stop.set)

    try:
        if args.once:
            runner = get_runner()
            while True:
                async with SessionLocal() as db:
                    ids = [s.id for s in await claim_batch(db, settings.JUDGE_BATCH_SIZE)]
                if not ids:
                    break
                for submission_id in ids:
                    async with SessionLocal() as db:
                        await process_one(db, runner, submission_id)
        else:
            await run_forever(stop)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
