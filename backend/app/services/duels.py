"""The head-to-head race: picking its problems, counting its rounds, deciding its winner.

Everything here is deliberately HTTP-free — `api/v1/endpoints/duels.py` is a thin shell
over these functions, and the interesting parts (`decide`, `pick_rounds`) are pure or
close to it so they can be reasoned about without a request.

Two rules in this module are load-bearing and easy to break by accident; both are
called out where they live:

- `cleared_ordinals` does **not** filter on `xp_awarded > 0` the way the boss does.
- `close_out` writes its verdict with a conditional UPDATE, not an attribute assignment.
"""

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.models import (
    Duel,
    DuelRound,
    DuelStatus,
    Problem,
    Progress,
    Submission,
    SubmissionStatus,
    XpEvent,
    XpSource,
)
from app.services.leveling import apply_xp, touch_streak
from app.services.progress import solved_problem_ids, today_utc

# No I/L/O/0/1 — a duel code gets read aloud and typed off a phone screen.
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6
CODE_ATTEMPTS = 5

_LOAD = (
    selectinload(Duel.rounds).selectinload(DuelRound.problem).selectinload(Problem.zone),
)


def new_code() -> str:
    """A fresh invite code. `secrets`, not `random` — a guessable code is a hijackable duel."""
    return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LENGTH))


def normalise_code(raw: str) -> str:
    """Codes are compared canonically uppercase, so the column needs no citext."""
    return raw.strip().upper()


# ---- the clock --------------------------------------------------------------
# Derived from `started_at` alone. There is no snapshot to fold and no resume marker,
# which is what makes it impossible for a client to stretch by refreshing or opening a
# second tab — the two halves of a duel would disagree about the time if it could.


def remaining_seconds(duel: Duel) -> int:
    if duel.started_at is None:
        return duel.total_seconds
    started = duel.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=UTC)
    spent = int((datetime.now(UTC) - started).total_seconds())
    return max(0, duel.total_seconds - spent)


def invite_expired(duel: Duel) -> bool:
    """A `waiting` duel nobody accepted in time. The code stays unique forever regardless."""
    created = duel.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return datetime.now(UTC) - created > timedelta(seconds=settings.DUEL_INVITE_TTL_SECONDS)


# ---- loading ----------------------------------------------------------------


async def load_duel(db: AsyncSession, duel_id: UUID) -> Duel | None:
    """Load a duel with its rounds, players and zones already in hand.

    `populate_existing` matters: this session does not expire on commit, and several
    callers reload right after writing a verdict with a Core UPDATE. Without it they
    would be handed the identity map's stale copy — a duel that still says "active" on
    the very request that decided it. `refresh()` is the wrong tool here because it
    also expires the eager loads, and the next attribute access would then be a lazy
    load inside async code, which raises rather than reloading.
    """
    return await db.scalar(
        select(Duel)
        .options(*_LOAD)
        .where(Duel.id == duel_id)
        .execution_options(populate_existing=True)
    )


async def load_by_code(db: AsyncSession, code: str) -> Duel | None:
    return await db.scalar(select(Duel).options(*_LOAD).where(Duel.code == normalise_code(code)))


async def live_duel_for(db: AsyncSession, user_id: UUID) -> Duel | None:
    """The duel this toy is currently in, as either side. At most one, by policy."""
    return await db.scalar(
        select(Duel)
        .options(*_LOAD)
        .where(
            or_(Duel.host_id == user_id, Duel.opponent_id == user_id),
            Duel.status.in_((DuelStatus.WAITING, DuelStatus.ACTIVE)),
        )
        .order_by(Duel.created_at.desc())
        .limit(1)
    )


async def recent_duels(db: AsyncSession, user_id: UUID, limit: int) -> list[Duel]:
    """This toy's duels, newest first, as either side."""
    rows = await db.scalars(
        select(Duel)
        .options(*_LOAD)
        .where(or_(Duel.host_id == user_id, Duel.opponent_id == user_id))
        .order_by(Duel.created_at.desc())
        .limit(max(1, min(limit, 50)))
    )
    return list(rows.all())


def is_participant(duel: Duel, user_id: UUID) -> bool:
    return user_id in (duel.host_id, duel.opponent_id)


# ---- round counting ---------------------------------------------------------


async def cleared_ordinals(db: AsyncSession, duel: Duel, user_id: UUID | None) -> list[int]:
    """Which rounds this toy has actually put down, in this duel.

    Note what is *not* here: the boss's `xp_awarded > 0`. That filter is solo's way of
    saying "a fresh solve, not an old one", and it is wrong for a race — a toy who
    solved two-sum last week would have a counter that could never move, losing the
    duel to a bug rather than to an opponent, with no error and no log line.

    What replaces it is the join to `duel_rounds`: a submission only counts if it is
    for a problem genuinely in this duel's set. Drop that join and a toy clears all
    three rounds by solving one easy problem three times. The `duel_id` tag already
    means "during this duel, by a participant, before the clock ran out" — see
    `resolve_duel_tag`, which refuses to write it otherwise.
    """
    if user_id is None:
        return []
    rows = await db.scalars(
        select(DuelRound.ordinal)
        .join(Submission, Submission.problem_id == DuelRound.problem_id)
        .where(
            DuelRound.duel_id == duel.id,
            Submission.duel_id == duel.id,
            Submission.user_id == user_id,
            Submission.status == SubmissionStatus.PASSED,
        )
        .distinct()
        .order_by(DuelRound.ordinal)
    )
    return [int(o) for o in rows.all()]


async def resolve_duel_tag(
    db: AsyncSession, user_id: UUID, problem_id: UUID, raw: UUID | None
) -> UUID | None:
    """Turn a claimed duel tag into one the round count can trust, or into nothing.

    Three things have to hold, and each closes a different hole: the toy is in this
    duel (or an outsider could stuff a live race with submissions), the clock is still
    running (or a tag from a stale tab could clear a round after time), and the problem
    is genuinely one of the duel's rounds (or a toy clears all three by solving one
    easy problem three times).

    Returns None rather than raising. A stale tag from a tab that missed the clock
    running out is ordinary, and refusing a *correct solve* over it would be the wrong
    trade — the solve still counts as a solve, it just doesn't count as a round.
    """
    if raw is None:
        return None
    duel = await db.scalar(
        select(Duel).where(
            Duel.id == raw,
            Duel.status == DuelStatus.ACTIVE,
            or_(Duel.host_id == user_id, Duel.opponent_id == user_id),
        )
    )
    if duel is None or remaining_seconds(duel) <= 0:
        return None
    in_set = await db.scalar(
        select(DuelRound.id).where(
            DuelRound.duel_id == duel.id, DuelRound.problem_id == problem_id
        )
    )
    return duel.id if in_set is not None else None


async def swept_at(db: AsyncSession, duel: Duel, user_id: UUID | None) -> datetime | None:
    """When this toy's *last* round landed, or None if they haven't cleared them all.

    This timestamp is what decides a duel where both sides finish: it is committed data
    about when the judging happened, not about when an HTTP request arrived, so every
    reader computes the same winner.
    """
    if user_id is None:
        return None
    row = await db.execute(
        select(func.count(func.distinct(DuelRound.ordinal)), func.max(Submission.judged_at))
        .join(Submission, Submission.problem_id == DuelRound.problem_id)
        .where(
            DuelRound.duel_id == duel.id,
            Submission.duel_id == duel.id,
            Submission.user_id == user_id,
            Submission.status == SubmissionStatus.PASSED,
        )
    )
    count, last = row.one()
    return last if int(count or 0) >= duel.rounds_total else None


# ---- picking the problem set ------------------------------------------------


async def pick_rounds(
    db: AsyncSession, host_id: UUID, opponent_id: UUID, wanted: int
) -> list[Problem]:
    """The duel's problem set: fair first, symmetric second, available third.

    An asymmetric head start is the most obvious unfairness in a race and it is
    invisible to both players, so the pool is filtered against *both* solve histories:

    1. Problems neither toy has fixed — the only genuinely fair pool.
    2. Problems both have fixed. Not fresh, but *equally* stale, which is the property
       that actually matters. This tier is why a tenth duel between the same pair is
       still a fair race.
    3. Whatever is left. Lopsided by construction, and only reachable once the pair has
       between them cleared essentially the whole catalogue.

    An ungraded problem is never eligible — it settles instantly on the honour system,
    which would make it a free round.
    """
    candidates = list(
        (
            await db.scalars(
                select(Problem)
                .options(selectinload(Problem.zone))
                .where(Problem.graded.is_(True))
                .order_by(Problem.sort_order)
            )
        ).all()
    )
    host_solved = await solved_problem_ids(db, host_id)
    opp_solved = await solved_problem_ids(db, opponent_id)

    neither = [p for p in candidates if p.id not in host_solved and p.id not in opp_solved]
    both = [p for p in candidates if p.id in host_solved and p.id in opp_solved]
    rest = [p for p in candidates if p not in neither and p not in both]

    picked: list[Problem] = []
    for tier in (neither, both, rest):
        if len(picked) >= wanted:
            break
        picked.extend(_spread_across_zones(tier, wanted - len(picked)))

    # Easy-to-hard inside the duel, whatever order the tiers offered them in.
    picked.sort(key=lambda p: p.sort_order)
    return picked[:wanted]


def _spread_across_zones(pool: list[Problem], wanted: int) -> list[Problem]:
    """Prefer one problem per toy corner, then fill — the same shape as today's quests.

    Shuffled, so two toys who duel repeatedly don't get the same three problems every
    time inside the same tier.
    """
    if wanted <= 0 or not pool:
        return []

    shuffled = list(pool)
    secrets.SystemRandom().shuffle(shuffled)

    picked: list[Problem] = []
    seen_zones: set = set()
    for problem in shuffled:
        if problem.zone_id not in seen_zones:
            picked.append(problem)
            seen_zones.add(problem.zone_id)
        if len(picked) == wanted:
            return picked
    for problem in shuffled:
        if len(picked) >= wanted:
            break
        if problem not in picked:
            picked.append(problem)
    return picked


# ---- creating and joining ---------------------------------------------------


async def create_duel(db: AsyncSession, host_id: UUID) -> Duel:
    """Open a challenge. The code is unique by constraint, not by hopeful SELECT."""
    for _ in range(CODE_ATTEMPTS):
        duel = Duel(
            code=new_code(),
            host_id=host_id,
            status=DuelStatus.WAITING,
            rounds_total=settings.DUEL_ROUNDS,
            total_seconds=settings.DUEL_DURATION_SECONDS,
        )
        db.add(duel)
        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            continue
        return duel
    raise RuntimeError("could not mint a unique duel code")


async def start_duel(db: AsyncSession, duel: Duel, opponent_id: UUID) -> list[Problem]:
    """Accept a challenge: choose the rounds and start the clock, in one transaction.

    This is the moment the problem set comes into existence — see `DuelRound`'s
    docstring for why it isn't chosen when the duel is created.
    """
    problems = await pick_rounds(db, duel.host_id, opponent_id, duel.rounds_total)
    for ordinal, problem in enumerate(problems, start=1):
        db.add(DuelRound(duel_id=duel.id, problem_id=problem.id, ordinal=ordinal))

    duel.opponent_id = opponent_id
    duel.rounds_total = len(problems)
    duel.status = DuelStatus.ACTIVE
    duel.started_at = datetime.now(UTC)
    return problems


# ---- deciding ---------------------------------------------------------------


@dataclass(slots=True)
class Outcome:
    status: DuelStatus
    winner_id: UUID | None
    # A clean sweep beat the clock, so it earns the speed bonus. Winning on rounds when
    # the clock ran out does not.
    swept: bool


def decide(
    duel: Duel,
    host_swept: datetime | None,
    opp_swept: datetime | None,
    host_cleared: int,
    opp_cleared: int,
    timed_out: bool,
) -> Outcome | None:
    """Who won, or None if the race is still on. Pure — the same inputs always agree.

    Called by every reader of an active duel. Because it reads committed `judged_at`
    timestamps rather than request arrival order, two players polling in the same
    millisecond compute the same answer; the conditional UPDATE in `close_out` only
    decides which of them gets to write it down.
    """
    # A sweep is checked before a forfeit, and the order is load-bearing. Nothing closes a
    # duel until somebody reads it, so a race can sit won-but-open for as long as neither
    # toy polls — and the other one conceding in that window must not rewrite the result.
    # Ordered the other way, a loser could downgrade the winner's sweep to the forfeit
    # payout by tapping at the right moment, and a sweeper's own mis-tap would hand the
    # win to a toy who cleared nothing.
    if host_swept is not None and opp_swept is not None:
        if host_swept == opp_swept:
            return Outcome(DuelStatus.COMPLETED, None, swept=True)  # a dead heat
        first = duel.host_id if host_swept < opp_swept else duel.opponent_id
        return Outcome(DuelStatus.COMPLETED, first, swept=True)
    if host_swept is not None:
        return Outcome(DuelStatus.COMPLETED, duel.host_id, swept=True)
    if opp_swept is not None:
        return Outcome(DuelStatus.COMPLETED, duel.opponent_id, swept=True)

    if duel.forfeited_by_id is not None:
        other = duel.host_id if duel.forfeited_by_id == duel.opponent_id else duel.opponent_id
        return Outcome(DuelStatus.COMPLETED, other, swept=False)

    if timed_out:
        # Nobody finished, but a close race should still feel decided.
        if host_cleared == opp_cleared:
            return Outcome(DuelStatus.EXPIRED, None, swept=False)
        leader = duel.host_id if host_cleared > opp_cleared else duel.opponent_id
        return Outcome(DuelStatus.EXPIRED, leader, swept=False)

    return None


async def close_out(db: AsyncSession, duel: Duel) -> Duel:
    """Settle a finished duel, exactly once, then pay both toys.

    Every read of an active duel runs this. Both players poll on their own timers and
    can land in the same millisecond, so the write below is guarded rather than assumed.
    """
    if duel.status != DuelStatus.ACTIVE:
        return duel

    # Held separately because a rollback below expires every loaded instance, and then
    # even reading `duel.id` would be a lazy load — which raises inside async code
    # rather than quietly fetching.
    duel_id = duel.id

    host_swept = await swept_at(db, duel, duel.host_id)
    opp_swept = await swept_at(db, duel, duel.opponent_id)
    host_cleared = len(await cleared_ordinals(db, duel, duel.host_id))
    opp_cleared = len(await cleared_ordinals(db, duel, duel.opponent_id))

    outcome = decide(
        duel, host_swept, opp_swept, host_cleared, opp_cleared, remaining_seconds(duel) <= 0
    )
    if outcome is None:
        return duel

    # The exactly-one-winner guard. Postgres serialises the row lock, so of two
    # concurrent close-outs one updates a row and the other gets nothing back.
    # If this WHERE is ever dropped — or this is rewritten as `duel.status = ...` —
    # both players' polls pay out and the duel has two winners.
    claimed = (
        await db.execute(
            update(Duel)
            .where(Duel.id == duel_id, Duel.status == DuelStatus.ACTIVE)
            .values(
                status=outcome.status,
                winner_id=outcome.winner_id,
                finished_at=datetime.now(UTC),
            )
            .returning(Duel.id)
        )
    ).scalar_one_or_none()

    if claimed is None:
        # The other toy's poll closed it a moment ago, and `decide` is pure, so they
        # reached the same verdict. Report theirs.
        await db.rollback()
        return await load_duel(db, duel_id) or duel

    await _award(db, duel, outcome, host_cleared, opp_cleared)
    await db.commit()
    # The verdict went in as a Core UPDATE and this session doesn't expire on commit,
    # so the loaded object still believes it is active until it is told otherwise.
    return await load_duel(db, duel_id) or duel


async def _award(
    db: AsyncSession, duel: Duel, outcome: Outcome, host_cleared: int, opp_cleared: int
) -> None:
    """Pay both sides the duel bonus, on top of whatever settle() already paid per solve."""
    if duel.host_xp_awarded or duel.opponent_xp_awarded:
        return
    if duel.opponent_id is None:
        return

    # Both progress rows in one statement, ordered — two concurrent close-outs that
    # share a toy would otherwise be free to take the locks in opposite orders.
    rows = (
        await db.scalars(
            select(Progress)
            .where(Progress.user_id.in_([duel.host_id, duel.opponent_id]))
            .order_by(Progress.user_id)
            .with_for_update()
        )
    ).all()
    by_user = {p.user_id: p for p in rows}

    for user_id, cleared in ((duel.host_id, host_cleared), (duel.opponent_id, opp_cleared)):
        progress = by_user.get(user_id)
        if progress is None:
            continue
        amount = _payout(duel, outcome, user_id, cleared)
        amount = await _clamp_to_daily_cap(db, user_id, amount)
        if amount <= 0:
            continue

        apply_xp(progress, amount)
        touch_streak(progress, today_utc())
        db.add(
            XpEvent(
                user_id=user_id,
                amount=amount,
                source=XpSource.DUEL,
                note=_note(duel, outcome, user_id),
                happened_on=today_utc(),
            )
        )
        if user_id == duel.host_id:
            duel.host_xp_awarded = amount
        else:
            duel.opponent_xp_awarded = amount


def _payout(duel: Duel, outcome: Outcome, user_id: UUID, cleared: int) -> int:
    participation = settings.DUEL_XP_PARTICIPATION * cleared

    if outcome.winner_id != user_id:
        # A toy who walked away collects nothing for the rounds they did fix.
        return 0 if duel.forfeited_by_id == user_id else participation

    # A walkover is not a win — but a forfeit only *makes* it a walkover when it decided
    # the duel. `decide` weighs a sweep first, so a recorded forfeit that arrived after
    # the winner had already cleared every round must not reprice their win; otherwise a
    # loser sets the winner's payout by choosing when to concede.
    if duel.forfeited_by_id is not None and not outcome.swept:
        return settings.DUEL_XP_FORFEIT_WIN

    if not outcome.swept:
        return settings.DUEL_XP_WIN + participation  # led on rounds when time ran out

    left = remaining_seconds(duel) / max(1, duel.total_seconds)
    return settings.DUEL_XP_WIN + round(left * settings.DUEL_XP_SPEED_BONUS_MAX) + participation


async def _clamp_to_daily_cap(db: AsyncSession, user_id: UUID, amount: int) -> int:
    """Bound the exploit rather than try to detect intent.

    Two accounts duelling each other on a loop is the one thing the problem-set filter
    can't close — tier 2 keeps serving problems that clear rounds while paying nothing
    per solve. The clamped figure is what gets written to the ledger as well as to the
    meter, because the heatmap and the weekly chart read the ledger and it must not lie.
    """
    if amount <= 0:
        return 0
    earned = int(
        await db.scalar(
            select(func.coalesce(func.sum(XpEvent.amount), 0)).where(
                XpEvent.user_id == user_id,
                XpEvent.source == XpSource.DUEL,
                XpEvent.happened_on == today_utc(),
            )
        )
        or 0
    )
    return max(0, min(amount, settings.DUEL_DAILY_BONUS_CAP - earned))


def _note(duel: Duel, outcome: Outcome, user_id: UUID) -> str:
    if outcome.winner_id is None:
        return "Duel drawn"
    if outcome.winner_id == user_id:
        walkover = duel.forfeited_by_id is not None and not outcome.swept
        return "Won a duel by forfeit" if walkover else "Won a duel"
    return "Fought a duel"
