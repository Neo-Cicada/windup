from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentProgress, CurrentUser, DbSession
from app.models import ChestTier, DailyQuest, Problem, Submission, XpSource, Zone
from app.models.gameplay import ChestUnlock, XpEvent
from app.schemas.academy import (
    AchievementOut,
    ChestsOut,
    ChestUnlockOut,
    HelpShelfOut,
    ProblemDetailOut,
    ProblemOut,
    SubmissionIn,
    SubmissionResultOut,
)
from app.services import achievements as achievements_service
from app.services.leveling import apply_xp, level_name, touch_streak
from app.services.progress import build_progress_out, solved_problem_ids, today_utc
from app.services.serialize import problem_out

router = APIRouter(prefix="/problems", tags=["problems"])

CHEST_LABELS = {
    ChestTier.HINT: "Hint",
    ChestTier.APPROACH: "Approach",
    ChestTier.SOLUTION: "Solution",
}


async def _get_problem(db: AsyncSession, slug: str) -> Problem:
    problem = await db.scalar(
        select(Problem).options(selectinload(Problem.zone)).where(Problem.slug == slug)
    )
    if problem is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="That toy isn't on any shelf."
        )
    return problem


async def _chests(db: AsyncSession, user_id, problem_id) -> ChestsOut:
    tiers = set(
        (
            await db.scalars(
                select(ChestUnlock.tier).where(
                    ChestUnlock.user_id == user_id, ChestUnlock.problem_id == problem_id
                )
            )
        ).all()
    )
    return ChestsOut(
        hint=ChestTier.HINT in tiers,
        approach=ChestTier.APPROACH in tiers,
        solution=ChestTier.SOLUTION in tiers,
    )


@router.get("", response_model=list[ProblemOut])
async def list_problems(
    db: DbSession,
    user: CurrentUser,
    zone: str | None = Query(default=None, description="Filter by zone slug"),
    difficulty: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[ProblemOut]:
    stmt = select(Problem).options(selectinload(Problem.zone)).order_by(Problem.sort_order)
    if zone:
        stmt = stmt.join(Zone, Zone.id == Problem.zone_id).where(Zone.slug == zone)
    if difficulty:
        stmt = stmt.where(Problem.difficulty == difficulty)

    problems = (await db.scalars(stmt.limit(limit).offset(offset))).all()
    solved = await solved_problem_ids(db, user.id)
    return [problem_out(p, solved=p.id in solved) for p in problems]


@router.get("/{slug}", response_model=ProblemDetailOut)
async def read_problem(slug: str, db: DbSession, user: CurrentUser) -> ProblemDetailOut:
    """The problem view, with locked help tiers omitted."""
    problem = await _get_problem(db, slug)
    chests = await _chests(db, user.id, problem.id)
    solved = await db.scalar(
        select(Submission.id).where(
            Submission.user_id == user.id,
            Submission.problem_id == problem.id,
            Submission.status == "passed",
        )
    )

    base = problem_out(problem, solved=solved is not None)
    unaided = not (chests.hint or chests.approach or chests.solution)
    return ProblemDetailOut(
        **base.model_dump(),
        prompt=problem.prompt,
        example_input=problem.example_input,
        example_output=problem.example_output,
        language=problem.language,
        starter_code=problem.starter_code,
        help_shelf=HelpShelfOut(
            explainer=problem.explainer,
            hint=problem.hint if chests.hint else None,
            approach=problem.approach if chests.approach else None,
            solution=problem.solution if chests.solution else None,
        ),
        chests=chests,
        unaided=unaided,
        unaided_bonus=problem.xp_reward,
    )


@router.post("/{slug}/chests/{tier}", response_model=ChestUnlockOut)
async def unlock_chest(
    slug: str, tier: ChestTier, db: DbSession, user: CurrentUser
) -> ChestUnlockOut:
    """Open a help chest. Costs the unaided bonus for this problem."""
    problem = await _get_problem(db, slug)
    chests = await _chests(db, user.id, problem.id)

    content = {
        ChestTier.HINT: problem.hint,
        ChestTier.APPROACH: problem.approach,
        ChestTier.SOLUTION: problem.solution,
    }[tier]

    if not getattr(chests, tier.value):
        db.add(ChestUnlock(user_id=user.id, problem_id=problem.id, tier=tier))
        await db.commit()
        setattr(chests, tier.value, True)

    label = CHEST_LABELS[tier]
    return ChestUnlockOut(
        tier=tier,
        content=content,
        chests=chests,
        unaided=False,
        message=(
            f"Opened the {label} chest — no shame in a peek! "
            "You forfeit the unaided bonus this time."
        ),
    )


@router.post("/{slug}/submit", response_model=SubmissionResultOut)
async def submit_problem(
    slug: str,
    payload: SubmissionIn,
    db: DbSession,
    user: CurrentUser,
    progress: CurrentProgress,
) -> SubmissionResultOut:
    """Run & Submit from the workbench: score it, pay out charge, check badges."""
    problem = await _get_problem(db, slug)
    chests = await _chests(db, user.id, problem.id)
    unaided = not (chests.hint or chests.approach or chests.solution)
    passed = payload.status == "passed"

    already_solved = (
        await db.scalar(
            select(Submission.id).where(
                Submission.user_id == user.id,
                Submission.problem_id == problem.id,
                Submission.status == "passed",
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

    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        boss_session_id=payload.boss_session_id,
        code=payload.code,
        language=payload.language or problem.language,
        status=payload.status,
        unaided=unaided,
        duration_seconds=payload.duration_seconds,
        xp_awarded=outcome.xp_awarded,
        coins_awarded=outcome.coins_awarded,
    )
    db.add(submission)

    if xp_award:
        db.add(
            XpEvent(
                user_id=user.id,
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
                DailyQuest.user_id == user.id,
                DailyQuest.problem_id == problem.id,
                DailyQuest.quest_date == today,
            )
        )
        if quest is not None:
            quest.progress_pct = 100
            quest.completed_at = datetime.now(UTC)

    await db.flush()
    newly = await achievements_service.evaluate(db, user.id, progress) if passed else []
    for badge in newly:
        badge_outcome = apply_xp(progress, badge.xp_reward)
        if badge_outcome.xp_awarded:
            db.add(
                XpEvent(
                    user_id=user.id,
                    amount=badge.xp_reward,
                    source=XpSource.ACHIEVEMENT,
                    note=f"Earned {badge.name}",
                    happened_on=today,
                )
            )

    await db.commit()
    await db.refresh(progress)

    if not passed:
        message = "Not quite — the marbles jammed. Wind up and try again!"
        confetti = 0
    elif already_solved:
        message = "Already fixed this toy — nice practice run, no extra charge."
        confetti = 12
    elif outcome.leveled_up:
        message = (
            f"LEVEL UP! You climbed onto the {level_name(progress.level)} shelf. "
            "Whirr-whirr-hooray!"
        )
        confetti = 80
    elif unaided:
        message = "Solved UNAIDED — full bonus! You clever little toy."
        confetti = 34
    else:
        message = f"Solved with help — still counts! +{xp_award} charge."
        confetti = 34

    return SubmissionResultOut(
        submission_id=submission.id,
        status=payload.status,
        unaided=unaided,
        xp_awarded=outcome.xp_awarded,
        coins_awarded=outcome.coins_awarded,
        leveled_up=outcome.leveled_up,
        sprocket_message=message,
        confetti=confetti,
        newly_earned=[
            AchievementOut(
                slug=b.slug,
                name=b.name,
                description=b.description,
                color=b.color,
                earned=True,
            )
            for b in newly
        ],
        progress=await build_progress_out(db, progress),
    )
