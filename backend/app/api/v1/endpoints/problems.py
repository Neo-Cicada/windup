import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.judge.bench import bench_for, benches_for, default_language
from app.judge.languages import UnknownLanguage
from app.models import (
    BossSession,
    BossStatus,
    ChestTier,
    Problem,
    Submission,
    SubmissionStatus,
    TestVisibility,
    Zone,
)
from app.models.gameplay import ChestUnlock
from app.schemas.academy import (
    ChestsOut,
    ChestUnlockOut,
    HelpShelfOut,
    ProblemDetailOut,
    ProblemLanguageOut,
    ProblemOut,
    SubmissionAcceptedOut,
    SubmissionIn,
    TestCaseOut,
)
from app.services.duels import resolve_duel_tag
from app.services.progress import solved_problem_ids
from app.services.serialize import problem_out
from app.services.submissions import settle

router = APIRouter(prefix="/problems", tags=["problems"])


async def _resolve_boss_tag(db: AsyncSession, user_id, raw) -> uuid.UUID | None:
    """A submission may only be tagged into a fight the toy is actually in.

    "In" means running *or* paused — the same pair `boss.py` calls ACTIVE. Pausing has
    never stopped a round from counting, and it shouldn't: a toy who pauses to read the
    problem and then fixes it has still fixed it during the fight.

    Like its duel counterpart this drops a bad tag rather than refusing the submission.
    A stale tag from a tab that missed the clock is ordinary, and losing a correct solve
    over it would be the wrong trade.
    """
    if raw is None:
        return None
    return await db.scalar(
        select(BossSession.id).where(
            BossSession.id == raw,
            BossSession.user_id == user_id,
            BossSession.status.in_((BossStatus.RUNNING, BossStatus.PAUSED)),
        )
    )

CHEST_LABELS = {
    ChestTier.HINT: "Hint",
    ChestTier.APPROACH: "Approach",
    ChestTier.SOLUTION: "Solution",
}


async def _get_problem(db: AsyncSession, slug: str) -> Problem:
    problem = await db.scalar(
        select(Problem)
        .options(
            selectinload(Problem.zone),
            selectinload(Problem.tests),
            selectinload(Problem.languages),
        )
        .where(Problem.slug == slug)
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
    # Default first, which is the one the workbench opens on.
    benches = benches_for(problem)
    return ProblemDetailOut(
        **base.model_dump(),
        prompt=problem.prompt,
        example_input=problem.example_input,
        example_output=problem.example_output,
        language=default_language(problem),
        starter_code=benches[0].starter_code if benches else problem.starter_code,
        languages=[
            ProblemLanguageOut(
                language=bench.language,
                label=bench.pack.label,
                runs_in_browser=bench.pack.runs_in_browser,
                entrypoint=bench.entrypoint,
                starter_code=bench.starter_code,
                harness_preamble=bench.preamble,
            )
            for bench in benches
        ],
        help_shelf=HelpShelfOut(
            explainer=problem.explainer,
            hint=problem.hint if chests.hint else None,
            approach=problem.approach if chests.approach else None,
            solution=problem.solution if chests.solution else None,
        ),
        chests=chests,
        unaided=unaided,
        unaided_bonus=problem.xp_reward,
        graded=problem.graded,
        entrypoint=benches[0].entrypoint if benches else problem.entrypoint,
        harness_preamble=benches[0].preamble if benches else problem.harness_preamble,
        example_tests=[
            TestCaseOut(
                ordinal=t.ordinal,
                label=t.label or f"Example {i + 1}",
                args=t.args_json,
                expected=t.expected_json,
            )
            for i, t in enumerate(
                sorted(
                    (t for t in problem.tests if t.visibility == TestVisibility.EXAMPLE),
                    key=lambda t: t.ordinal,
                )
            )
        ],
        # A count, not the cases. The toy should know how much is being checked.
        hidden_test_count=sum(
            1 for t in problem.tests if t.visibility == TestVisibility.HIDDEN
        ),
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


@router.post(
    "/{slug}/submit",
    response_model=SubmissionAcceptedOut,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_problem(
    slug: str,
    payload: SubmissionIn,
    db: DbSession,
    user: CurrentUser,
) -> SubmissionAcceptedOut:
    """Hand the code to the judge. The verdict arrives at GET /submissions/{id}.

    This endpoint deliberately executes nothing. It records the submission as
    pending and returns; a judge worker picks it up. That is what keeps one
    toy's infinite loop from stalling everyone else's requests, and it is why
    there is no longer any way for the client to say whether it passed.
    """
    problem = await _get_problem(db, slug)
    chests = await _chests(db, user.id, problem.id)
    unaided = not (chests.hint or chests.approach or chests.solution)

    # Which bench the code was written at decides which interpreter judges it, so
    # a language the problem doesn't offer is refused here rather than becoming a
    # baffling verdict later. An ungraded problem has no bench to check against —
    # nothing is going to run it.
    language = payload.language or problem.language
    if problem.graded:
        try:
            language = bench_for(problem, payload.language).language
        except UnknownLanguage as unknown:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=str(unknown)
            ) from unknown

    in_flight = int(
        await db.scalar(
            select(func.count())
            .select_from(Submission)
            .where(
                Submission.user_id == user.id,
                Submission.status.in_([SubmissionStatus.PENDING, SubmissionStatus.RUNNING]),
            )
        )
        or 0
    )
    if in_flight >= settings.JUDGE_MAX_PENDING_PER_USER:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Sprocket is still testing your last few springs — wait for those first.",
        )

    submission = Submission(
        user_id=user.id,
        problem_id=problem.id,
        # Both tags arrive as claims. Resolving them here is what stops one toy
        # stuffing another's fight or duel with submissions.
        boss_session_id=await _resolve_boss_tag(db, user.id, payload.boss_session_id),
        duel_id=await resolve_duel_tag(db, user.id, problem.id, payload.duel_id),
        code=payload.code,
        language=language,
        status=SubmissionStatus.PENDING,
        unaided=unaided,
        duration_seconds=payload.duration_seconds,
    )
    db.add(submission)

    if not problem.graded:
        # No runner for this language yet, so there is nothing to judge. It
        # settles immediately, on the old honour system.
        submission.status = SubmissionStatus.PASSED
        submission.judged_at = datetime.now(UTC)
        await db.flush()
        await settle(db, submission)

    await db.commit()

    return SubmissionAcceptedOut(
        submission_id=submission.id,
        status=submission.status,
        queue_position=in_flight,
    )
