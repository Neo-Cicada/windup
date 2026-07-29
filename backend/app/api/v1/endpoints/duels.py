"""The duel screen: open a challenge, share the code, race, settle.

A thin shell over `app/services/duels.py`. The one thing worth knowing before reading:
**every read of an active duel is also where it gets decided.** There is no background
task and no hook in `settle()` — both players are already polling, `decide()` is pure,
and a conditional UPDATE makes sure only one of those polls writes the verdict down.
"""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.api.deps import CurrentUser, DbSession
from app.core.config import settings
from app.models import Duel, DuelStatus, User
from app.schemas.academy import DuelActionIn, DuelInviteOut, DuelOut, DuelPlayerOut, DuelRoundOut
from app.services import duels as svc

router = APIRouter(prefix="/duels", tags=["duel"])

# Poll cadences, in ms. Racing is worth 2s; an unaccepted invite changes far less often;
# a finished duel never changes again, and 0 tells the client to stop entirely.
POLL_ACTIVE_MS = 2000
POLL_WAITING_MS = 5000
POLL_DONE_MS = 0

# Matches the shelf-of-fame swatches, for a toy who never picked a colour.
FALLBACK_COLOR = "#8B6FD6"


def _player(
    user: User | None, cleared: list[int], forfeited: bool, xp: int
) -> DuelPlayerOut | None:
    if user is None:
        return None
    return DuelPlayerOut(
        toy_name=user.toy_name,
        avatar_body=user.avatar_body or FALLBACK_COLOR,
        avatar_head=user.avatar_head or FALLBACK_COLOR,
        rounds_cleared=len(cleared),
        cleared_ordinals=cleared,
        forfeited=forfeited,
        xp_awarded=xp,
    )


def _outcome_label(duel: Duel, winner: str | None, you_forfeited: bool) -> str:
    """Sprocket's line for a finished duel, from the viewer's side of it."""
    if duel.status in (DuelStatus.WAITING, DuelStatus.ACTIVE):
        return ""
    if duel.status == DuelStatus.ABANDONED:
        return "That duel was called off."
    if duel.status == DuelStatus.EXPIRED and duel.started_at is None:
        return "Nobody accepted that challenge in time."

    if winner == "you":
        # A forfeiter who still won is the toy who had already swept and then mis-tapped,
        # so that is a race won, not a walkover handed over.
        if duel.forfeited_by_id is not None and duel.forfeited_by_id != duel.winner_id:
            return "The other toy wound down — the duel is yours."
        if duel.status == DuelStatus.EXPIRED:
            return "Time's up, and you were ahead. Duel won!"
        return "Every round fixed first — duel won!"
    if winner == "them":
        if you_forfeited:
            return "You ran away. The other toy takes it."
        return "The other toy got there first. Rematch?"
    return "A dead heat — nobody could split you."


async def _out(db, duel: Duel, viewer_id: UUID) -> DuelOut:
    """Serialise a duel from one toy's point of view."""
    you_are_host = duel.host_id == viewer_id
    mine, theirs = (
        (duel.host, duel.opponent) if you_are_host else (duel.opponent, duel.host)
    )
    my_id, their_id = (
        (duel.host_id, duel.opponent_id) if you_are_host else (duel.opponent_id, duel.host_id)
    )
    my_xp, their_xp = (
        (duel.host_xp_awarded, duel.opponent_xp_awarded)
        if you_are_host
        else (duel.opponent_xp_awarded, duel.host_xp_awarded)
    )

    my_cleared = await svc.cleared_ordinals(db, duel, my_id)
    their_cleared = await svc.cleared_ordinals(db, duel, their_id)
    you_forfeited = duel.forfeited_by_id is not None and duel.forfeited_by_id == my_id

    remaining = svc.remaining_seconds(duel) if duel.status == DuelStatus.ACTIVE else 0
    if duel.status == DuelStatus.WAITING:
        remaining = duel.total_seconds
    minutes, seconds = divmod(remaining, 60)

    winner: str | None = None
    if duel.winner_id is not None:
        winner = "you" if duel.winner_id == my_id else "them"
    elif duel.status in (DuelStatus.COMPLETED, DuelStatus.EXPIRED) and duel.opponent_id:
        winner = "draw"

    poll = POLL_ACTIVE_MS
    if duel.status == DuelStatus.WAITING:
        poll = POLL_WAITING_MS
    elif duel.status != DuelStatus.ACTIVE:
        poll = POLL_DONE_MS

    return DuelOut(
        id=duel.id,
        code=duel.code,
        status=DuelStatus(duel.status),
        rounds_total=duel.rounds_total,
        total_seconds=duel.total_seconds,
        remaining_seconds=remaining,
        time_label=f"{minutes}:{seconds:02d}",
        pct=round(remaining / duel.total_seconds * 100) if duel.total_seconds else 0,
        you=_player(mine, my_cleared, you_forfeited, my_xp)
        or DuelPlayerOut(toy_name="You", avatar_body=FALLBACK_COLOR, avatar_head=FALLBACK_COLOR),
        them=_player(theirs, their_cleared, duel.forfeited_by_id == their_id, their_xp),
        you_are_host=you_are_host,
        rounds=[
            DuelRoundOut(
                ordinal=r.ordinal,
                slug=r.problem.slug,
                title=r.problem.title,
                difficulty=r.problem.difficulty,
                zone=r.problem.zone.name if r.problem.zone else "",
                color=r.problem.zone.color if r.problem.zone else FALLBACK_COLOR,
                you_solved=r.ordinal in my_cleared,
                they_solved=r.ordinal in their_cleared,
            )
            for r in duel.rounds
        ],
        winner=winner,
        outcome_label=_outcome_label(duel, winner, you_forfeited),
        invite_path=f"/academy/duel/{duel.code}",
        poll_after_ms=poll,
    )


async def _settled(db, duel: Duel) -> Duel:
    """Fold in whatever the clock has decided since the last read.

    A waiting invite goes stale; an active duel gets its winner picked. Both are lazy,
    on read, for the same reason `/boss/current` expires a session that way: this
    deployment has no scheduler, and a duel nobody is looking at needs no verdict yet.
    """
    if duel.status == DuelStatus.WAITING and svc.invite_expired(duel):
        duel.status = DuelStatus.EXPIRED
        await db.commit()
        return await svc.load_duel(db, duel.id) or duel
    if duel.status == DuelStatus.ACTIVE:
        return await svc.close_out(db, duel)
    return duel


@router.post("", response_model=DuelOut, status_code=status.HTTP_201_CREATED)
async def open_challenge(db: DbSession, user: CurrentUser) -> DuelOut:
    """Open a challenge and get a code to share. One live duel per toy."""
    live = await svc.live_duel_for(db, user.id)
    if live is not None:
        live = await _settled(db, live)
    if live is not None and live.status in (DuelStatus.WAITING, DuelStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You're already in a duel — finish or call off that one first.",
        )

    duel = await svc.create_duel(db, user.id)
    await db.commit()
    fresh = await svc.load_duel(db, duel.id)
    return await _out(db, fresh or duel, user.id)


@router.get("/current", response_model=DuelOut | None)
async def current_duel(db: DbSession, user: CurrentUser) -> DuelOut | None:
    """The duel this toy is in, if any.

    Fetched on provider mount rather than when the duel screen opens — a toy can land
    straight on a problem link with a duel already running, and the submission has to
    carry the tag either way.
    """
    duel = await svc.live_duel_for(db, user.id)
    if duel is None:
        return None
    duel = await _settled(db, duel)
    return await _out(db, duel, user.id)


@router.get("", response_model=list[DuelOut])
async def list_duels(db: DbSession, user: CurrentUser, limit: int = 10) -> list[DuelOut]:
    """Recent duels, newest first — mirrors GET /boss/sessions."""
    rows = await svc.recent_duels(db, user.id, limit)
    return [await _out(db, d, user.id) for d in rows]


@router.get("/by-code/{code}", response_model=DuelInviteOut)
async def preview_invite(code: str, db: DbSession, user: CurrentUser) -> DuelInviteOut:
    """What the invite link shows before you accept. Never contains the problems."""
    duel = await svc.load_by_code(db, code)
    if duel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No duel by that code — check the letters.",
        )
    duel = await _settled(db, duel)

    joinable = True
    message = f"{duel.host.toy_name} wants to race you."
    if duel.host_id == user.id:
        joinable, message = False, "This is your own challenge — send the code to a friend."
    elif duel.opponent_id == user.id:
        joinable, message = True, "You're already in this duel."
    elif duel.status == DuelStatus.WAITING and svc.invite_expired(duel):
        joinable, message = False, "That invite wound down — ask for a fresh one."
    elif duel.status != DuelStatus.WAITING:
        joinable, message = False, "That duel is already over."

    return DuelInviteOut(
        code=duel.code,
        status=DuelStatus(duel.status),
        host_name=duel.host.toy_name,
        host_avatar=duel.host.avatar_body or FALLBACK_COLOR,
        rounds_total=duel.rounds_total,
        total_seconds=duel.total_seconds,
        joinable=joinable,
        message=message,
    )


@router.post("/by-code/{code}/join", response_model=DuelOut)
async def join_duel(code: str, db: DbSession, user: CurrentUser) -> DuelOut:
    """Accept a challenge — the moment the rounds are chosen and the clock starts.

    Idempotent for the toy who already joined: the invite screen makes this request on
    every load, so F5 must not be an error.
    """
    duel = await svc.load_by_code(db, code)
    if duel is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No duel by that code — check the letters.",
        )

    if duel.opponent_id == user.id:
        duel = await _settled(db, duel)
        return await _out(db, duel, user.id)

    if duel.host_id == user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You can't duel yourself — you'd lose either way.",
        )

    duel = await _settled(db, duel)
    if duel.status == DuelStatus.EXPIRED and duel.started_at is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That invite wound down — ask for a fresh one.",
        )
    if duel.status != DuelStatus.WAITING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "That duel already has two toys in it."
                if duel.opponent_id is not None
                else "That duel is already over."
            ),
        )

    mine = await svc.live_duel_for(db, user.id)
    if mine is not None:
        mine = await _settled(db, mine)
    if mine is not None and mine.status in (DuelStatus.WAITING, DuelStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You're already in a duel — finish or call off that one first.",
        )

    problems = await svc.start_duel(db, duel, user.id)
    if len(problems) < settings.DUEL_ROUNDS:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="There aren't enough toys in the workshop for a duel yet.",
        )
    await db.commit()
    fresh = await svc.load_duel(db, duel.id)
    return await _out(db, fresh or duel, user.id)


@router.post("/{duel_id}/actions", response_model=DuelOut)
async def act_on_duel(
    duel_id: UUID, payload: DuelActionIn, db: DbSession, user: CurrentUser
) -> DuelOut:
    """`forfeit` hands the win over; `cancel` calls off a challenge nobody accepted."""
    duel = await _mine(db, duel_id, user.id)

    if payload.action == "cancel":
        if duel.status != DuelStatus.WAITING:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Too late to call that one off — it's already running.",
            )
        if duel.host_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Only the toy who opened a challenge can call it off.",
            )
        duel.status = DuelStatus.ABANDONED
        await db.commit()
        return await _out(db, await svc.load_duel(db, duel.id) or duel, user.id)

    # forfeit
    if duel.status == DuelStatus.WAITING:
        duel.status = DuelStatus.ABANDONED
        await db.commit()
        return await _out(db, await svc.load_duel(db, duel.id) or duel, user.id)
    if duel.status != DuelStatus.ACTIVE:
        return await _out(db, duel, user.id)

    duel.forfeited_by_id = user.id
    await db.flush()
    duel = await svc.close_out(db, duel)
    return await _out(db, duel, user.id)


@router.get("/{duel_id}", response_model=DuelOut)
async def read_duel(duel_id: UUID, db: DbSession, user: CurrentUser) -> DuelOut:
    """The 2-second poll — and the place a finished duel actually gets decided."""
    duel = await _mine(db, duel_id, user.id)
    duel = await _settled(db, duel)
    return await _out(db, duel, user.id)


async def _mine(db, duel_id: UUID, user_id: UUID) -> Duel:
    """A duel the caller is actually in. A stranger gets the same 404 as a bad id."""
    duel = await svc.load_duel(db, duel_id)
    if duel is None or not svc.is_participant(duel, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No duel by that name on the record."
        )
    return duel
