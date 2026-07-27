"""Reading a submission back — where the workbench learns its verdict.

`POST /problems/{slug}/submit` only queues the code, so this is the endpoint the
client polls. While the judge is still working the verdict fields are null; once
it has ruled they are all filled in at once, from the same settlement the worker
performed.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models import Achievement, Submission, SubmissionStatus, UserAchievement
from app.schemas.academy import (
    AchievementOut,
    FailureOut,
    SubmissionResultOut,
)
from app.services.progress import build_progress_out
from app.services.submissions import confetti_for, sprocket_line

router = APIRouter(prefix="/submissions", tags=["submissions"])

# Badges earned by the settlement that produced this submission. The worker has
# already written the UserAchievement rows, so we read them back rather than
# threading the Settlement object through the queue.
_RECENT_BADGE_WINDOW_SECONDS = 10


async def _newly_earned(db: AsyncSession, submission: Submission) -> list[AchievementOut]:
    if submission.settled_at is None or submission.status != SubmissionStatus.PASSED:
        return []
    rows = await db.execute(
        select(Achievement)
        .join(UserAchievement, UserAchievement.achievement_id == Achievement.id)
        .where(
            UserAchievement.user_id == submission.user_id,
            UserAchievement.earned_at >= submission.settled_at,
        )
        .order_by(Achievement.sort_order)
    )
    return [
        AchievementOut(
            slug=b.slug, name=b.name, description=b.description, color=b.color, earned=True
        )
        for b in rows.scalars().all()
    ]


async def _describe_wait(
    db: AsyncSession, submission: Submission, result: SubmissionResultOut
) -> None:
    """Say something useful when a submission is sitting in the queue.

    Distinguishes "no judge is running" from "the judge is busy". The first is
    the common case — nobody started `python -m app.judge.worker` — and it used
    to present as the judge merely being slow, which sent people looking in the
    wrong place for 45 seconds.
    """
    created = submission.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    waiting = (datetime.now(UTC) - created).total_seconds()
    if waiting < settings.JUDGE_STALL_AFTER_SECONDS:
        return

    # Any worker anywhere claiming or finishing work recently means one is alive.
    since = datetime.now(UTC) - timedelta(seconds=settings.JUDGE_LIVENESS_WINDOW_SECONDS)
    alive = await db.scalar(
        select(Submission.id)
        .where(or_(Submission.claimed_at >= since, Submission.judged_at >= since))
        .limit(1)
    )

    if alive is not None:
        # Backed up, not broken. Report the wait but leave `stalled` false — the
        # client gives up when it sees that flag, and giving up on a judge that
        # is demonstrably working would show "hold tight" as an error and hide
        # the charge the toy is about to be awarded.
        ahead = int(
            await db.scalar(
                select(func.count())
                .select_from(Submission)
                .where(
                    Submission.status == SubmissionStatus.PENDING,
                    Submission.created_at < submission.created_at,
                )
            )
            or 0
        )
        result.sprocket_message = (
            "Sprocket has a queue — "
            + (f"{ahead} run{'s' if ahead != 1 else ''} ahead of yours. " if ahead else "")
            + "Still testing, hold tight."
        )
        return

    # Nothing has claimed or finished anything in the liveness window, so waiting
    # longer cannot help. This is the one case worth interrupting the toy for.
    result.stalled = True
    result.sprocket_message = (
        "Nothing is manning the test rig — no judge worker is running, so your code "
        "is just sitting on the bench. Start one with: "
        "uv run python -m app.judge.worker"
    )


@router.get("/{submission_id}", response_model=SubmissionResultOut)
async def read_submission(
    submission_id: UUID,
    db: DbSession,
    user: CurrentUser,
) -> SubmissionResultOut:
    """Poll for a verdict. Null xp/progress means the judge is still working."""
    submission = await db.scalar(
        select(Submission)
        .options(selectinload(Submission.problem))
        .where(Submission.id == submission_id, Submission.user_id == user.id)
    )
    if submission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No such run on the workbench record.",
        )

    result = SubmissionResultOut(
        submission_id=submission.id,
        status=SubmissionStatus(submission.status),
        language=submission.language,
        unaided=submission.unaided,
        tests_passed=submission.tests_passed,
        tests_total=submission.tests_total,
        runtime_ms=submission.runtime_ms,
    )

    if submission.judged_at is None:
        result.sprocket_message = "Sprocket is testing the springs…"
        await _describe_wait(db, submission, result)
        return result

    already_solved = (
        await db.scalar(
            select(Submission.id).where(
                Submission.user_id == user.id,
                Submission.problem_id == submission.problem_id,
                Submission.status == SubmissionStatus.PASSED,
                Submission.id != submission.id,
                Submission.judged_at < submission.judged_at,
            )
        )
        is not None
    )

    result.xp_awarded = submission.xp_awarded
    result.coins_awarded = submission.coins_awarded
    result.leveled_up = submission.leveled_up
    result.sprocket_message = sprocket_line(
        submission,
        already_solved=already_solved,
        leveled_up=submission.leveled_up,
        level=user.progress.level if user.progress else 1,
        xp_award=submission.xp_awarded,
    )
    result.confetti = confetti_for(
        submission, already_solved=already_solved, leveled_up=submission.leveled_up
    )
    result.newly_earned = await _newly_earned(db, submission)
    if submission.failure_json:
        result.failure = FailureOut(**submission.failure_json)
    if user.progress is not None:
        result.progress = await build_progress_out(db, user.progress)
    return result


