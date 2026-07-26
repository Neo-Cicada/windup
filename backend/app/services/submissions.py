"""Settling a judged submission: charge, streak, quest, badges, Sprocket's line.

This is the payout that used to sit inline in `POST /problems/{slug}/submit`,
back when the client declared its own verdict and the answer was known the
instant the request arrived. Now the verdict arrives later, from the judge
worker, so the payout moved here and the worker calls it.

The logic is unchanged from that inline version on purpose — including paying
`problem.xp_reward * 2` for an unaided solve rather than reading
`XP_SOLVE_UNAIDED`, which this path has never used. Changing what a solve is
worth is a separate decision from changing who decides whether you solved it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Achievement,
    DailyQuest,
    Problem,
    Progress,
    Submission,
    SubmissionStatus,
    XpEvent,
    XpSource,
)
from app.services import achievements as achievements_service
from app.services.leveling import apply_xp, level_name, touch_streak
from app.services.progress import today_utc


@dataclass
class Settlement:
    """What the payout produced, for the response the client eventually polls."""

    xp_awarded: int = 0
    coins_awarded: int = 0
    leveled_up: bool = False
    sprocket_message: str = ""
    confetti: int = 0
    newly_earned: list[Achievement] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.newly_earned is None:
            self.newly_earned = []


async def settle(db: AsyncSession, submission: Submission) -> Settlement:
    """Pay out a judged submission. Idempotent — safe to call twice.

    Called by the judge worker once a verdict lands, and inline by the endpoint
    for ungraded problems. Does not commit; the caller owns the transaction.
    """
    if submission.settled_at is not None:
        # Already paid. A retried job must not pay twice.
        return _replay(submission)

    problem = submission.problem or await db.get(Problem, submission.problem_id)

    # Lock the toy's progress row for the rest of this transaction.
    #
    # Everything below is a read-modify-write on shared state: the XP counters,
    # `solved_count`, the streak, and the `already_solved` probe that decides
    # whether this solve pays at all. Two workers settling for the same toy at
    # once — reachable, since JUDGE_MAX_PENDING_PER_USER allows three runs in
    # flight and the deployment story is "add more workers" — would both read
    # pre-payout values and the second commit would clobber the first, losing a
    # solve from the counters while both submissions told the client they paid.
    #
    # The lock serialises settlement per toy. Because Postgres reads committed
    # data, the loser of the race blocks here and then sees the winner's solve,
    # which is what makes the `already_solved` probe below trustworthy. It also
    # keeps `achievements.evaluate` from inserting the same badge twice.
    progress = await db.scalar(
        select(Progress).where(Progress.user_id == submission.user_id).with_for_update()
    )
    if progress is None:  # pragma: no cover - defensive, mirrors deps.get_current_progress
        progress = Progress(user_id=submission.user_id)
        db.add(progress)
        await db.flush()

    passed = submission.status == SubmissionStatus.PASSED
    unaided = submission.unaided

    # Has this problem already been paid for? Note `settled_at`: the question is
    # not "does another passing run exist" but "has one already been paid", and
    # those differ. Without it, two passing runs for the same problem that have
    # not settled yet each see the other, each conclude the toy was already paid,
    # and *neither* pays — a correct solve earning nothing.
    already_solved = (
        await db.scalar(
            select(Submission.id).where(
                Submission.user_id == submission.user_id,
                Submission.problem_id == submission.problem_id,
                Submission.status == SubmissionStatus.PASSED,
                Submission.id != submission.id,
                Submission.settled_at.is_not(None),
            )
        )
        is not None
    )

    xp_award = 0
    if passed and not already_solved:
        xp_award = problem.xp_reward * 2 if unaided else problem.xp_reward

    outcome = apply_xp(progress, xp_award)

    if passed and not already_solved:
        progress.solved_count += 1
        if unaided:
            progress.unaided_count += 1

    today = today_utc()
    if passed:
        touch_streak(progress, today)

    submission.xp_awarded = outcome.xp_awarded
    submission.coins_awarded = outcome.coins_awarded
    submission.leveled_up = outcome.leveled_up
    submission.settled_at = datetime.now(UTC)

    if xp_award:
        db.add(
            XpEvent(
                user_id=submission.user_id,
                amount=xp_award,
                source=XpSource.SOLVE,
                note=f"Solved {problem.title}",
                happened_on=today,
            )
        )

    # Close out today's quest card for this problem.
    if passed:
        quest = await db.scalar(
            select(DailyQuest).where(
                DailyQuest.user_id == submission.user_id,
                DailyQuest.problem_id == submission.problem_id,
                DailyQuest.quest_date == today,
            )
        )
        if quest is not None:
            quest.progress_pct = 100
            quest.completed_at = datetime.now(UTC)

    await db.flush()
    newly = (
        await achievements_service.evaluate(db, submission.user_id, progress) if passed else []
    )
    for badge in newly:
        badge_outcome = apply_xp(progress, badge.xp_reward)
        if badge_outcome.xp_awarded:
            db.add(
                XpEvent(
                    user_id=submission.user_id,
                    amount=badge.xp_reward,
                    source=XpSource.ACHIEVEMENT,
                    note=f"Earned {badge.name}",
                    happened_on=today,
                )
            )

    return Settlement(
        xp_awarded=outcome.xp_awarded,
        coins_awarded=outcome.coins_awarded,
        leveled_up=outcome.leveled_up,
        sprocket_message=sprocket_line(
            submission,
            already_solved=already_solved,
            leveled_up=outcome.leveled_up,
            level=progress.level,
            xp_award=xp_award,
        ),
        confetti=confetti_for(
            submission, already_solved=already_solved, leveled_up=outcome.leveled_up
        ),
        newly_earned=newly,
    )


def _replay(submission: Submission) -> Settlement:
    """The settlement for an already-settled submission, without paying again."""
    return Settlement(
        xp_awarded=submission.xp_awarded,
        coins_awarded=submission.coins_awarded,
        leveled_up=False,
        sprocket_message=sprocket_line(submission, already_solved=True, leveled_up=False),
        confetti=0,
    )


def sprocket_line(
    submission: Submission,
    *,
    already_solved: bool,
    leveled_up: bool,
    level: int = 1,
    xp_award: int = 0,
) -> str:
    """Sprocket's verdict, in the voice of the workshop."""
    status = submission.status
    passed_n, total_n = submission.tests_passed, submission.tests_total

    if status == SubmissionStatus.TIMEOUT:
        return (
            "That one ran and ran and never stopped — the spring wound down before it "
            "finished. Look for a loop that never ends."
        )
    if status == SubmissionStatus.ERROR:
        return "The workbench jammed before the tests could run. Check the code compiles!"
    if status != SubmissionStatus.PASSED:
        if passed_n:
            return (
                f"Close! {passed_n} of {total_n} springs held, but the rest jammed. "
                "Have another wind."
            )
        return "Not quite — the marbles jammed. Wind up and try again!"
    if already_solved:
        return "Already fixed this toy — nice practice run, no extra charge."
    if leveled_up:
        return (
            f"LEVEL UP! You climbed onto the {level_name(level)} shelf. Whirr-whirr-hooray!"
        )
    if submission.unaided:
        return "Solved UNAIDED — full bonus! You clever little toy."
    return f"Solved with help — still counts! +{xp_award} charge."


def confetti_for(submission: Submission, *, already_solved: bool, leveled_up: bool) -> int:
    if submission.status != SubmissionStatus.PASSED:
        return 0
    if already_solved:
        return 12
    if leveled_up:
        return 80
    return 34
