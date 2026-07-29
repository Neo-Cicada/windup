"""The head-to-head race.

Two rules carry this feature and both are easy to break without a red test:

- a duel round clears on *any* passed submission tagged into the duel for a problem in
  its set — deliberately unlike the boss, which demands a first-time solve;
- exactly one of two simultaneous polls gets to write the verdict down.

`test_duel_round_clears_even_when_the_solve_pays_nothing` and
`test_duel_exactly_one_winner_when_both_finish` are those two. Everything else is
lifecycle.
"""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import (
    Duel,
    DuelRound,
    DuelStatus,
    Problem,
    Submission,
    SubmissionStatus,
    XpEvent,
    XpSource,
)
from app.services.duels import decide
from tests.conftest import Judge

BOSS_ROUND_SLUGS = ["two-sum", "reverse-linked-list", "number-of-islands"]


async def _open(client: AsyncClient, auth: dict[str, str]) -> dict:
    resp = await client.post("/api/v1/duels", headers=auth)
    assert resp.status_code == 201, resp.text
    return resp.json()


async def _join(client: AsyncClient, auth: dict[str, str], code: str) -> dict:
    resp = await client.post(f"/api/v1/duels/by-code/{code}/join", headers=auth)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _read(client: AsyncClient, auth: dict[str, str], duel_id: str) -> dict:
    resp = await client.get(f"/api/v1/duels/{duel_id}", headers=auth)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def _start(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> tuple[dict, dict]:
    """Open a challenge and accept it. Returns (host's view, opponent's view)."""
    opened = await _open(client, auth)
    joined = await _join(client, auth2, opened["code"])
    return await _read(client, auth, opened["id"]), joined


async def _clear(j: Judge, duel: dict, ordinals: list[int]) -> None:
    """Actually solve the given rounds, tagged into the duel."""
    for ordinal in ordinals:
        slug = next(r["slug"] for r in duel["rounds"] if r["ordinal"] == ordinal)
        body = await j.solve(slug, duel_id=duel["id"])
        assert body["status"] == "passed", f"{slug}: {body}"


async def _duel_xp(db: AsyncSession, duel_id: str) -> list[int]:
    rows = await db.scalars(
        select(XpEvent.amount).where(XpEvent.source == XpSource.DUEL).order_by(XpEvent.amount)
    )
    return [int(a) for a in rows.all()]


async def _tagged(db: AsyncSession) -> int:
    """How many submissions carry *any* duel tag. Zero is what a dropped claim looks like."""
    return int(
        await db.scalar(
            select(func.count()).select_from(Submission).where(Submission.duel_id.is_not(None))
        )
        or 0
    )


# ---- the two load-bearing rules ---------------------------------------------


async def test_duel_round_clears_even_when_the_solve_pays_nothing(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """The rule the boss gets wrong, asserted directly.

    The boss counts a round only when the submission paid XP, which means a first-time
    solve. Carry that into a race and a toy who fixed the problem last week has a
    counter that can never move — they lose to a bug, silently. Here the submission
    pays nothing and must still clear its round.
    """
    host, _ = await _start(client, auth, auth2)
    first = host["rounds"][0]

    problem_id = await db.scalar(select(Problem.id).where(Problem.slug == first["slug"]))
    user_id = await db.scalar(select(Duel.host_id).where(Duel.id == host["id"]))
    db.add(
        Submission(
            user_id=user_id,
            problem_id=problem_id,
            duel_id=host["id"],
            code="# already solved this one last week",
            status=SubmissionStatus.PASSED,
            xp_awarded=0,
            judged_at=datetime.now(UTC),
        )
    )
    await db.commit()

    after = await _read(client, auth, host["id"])
    assert after["you"]["rounds_cleared"] == 1, after["you"]
    assert after["you"]["cleared_ordinals"] == [first["ordinal"]]


async def test_duel_round_clears_from_a_zero_paying_solve_end_to_end(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str],
    judge: Judge,
) -> None:
    """The same rule as above, but nothing is hand-inserted — every row is real.

    The test beside this one builds its passing submission with `db.add`, which proves
    `cleared_ordinals` ignores `xp_awarded` but steps over `resolve_duel_tag` entirely.
    Here the toy genuinely solves the problem first (untagged, paying full price), then
    solves it again inside the duel. That second submission pays nothing — re-solving
    never does — and it is the *only* one tagged into the duel, so the round can only
    clear if a zero-paying solve counts. Port the boss's `xp_awarded > 0` filter across
    and this goes red while the synthetic version stays green.
    """
    host, _ = await _start(client, auth, auth2)
    first = host["rounds"][0]

    paid = await judge.solve(first["slug"])
    assert paid["status"] == "passed"
    assert paid["xp_awarded"] > 0, "the untagged solve should have paid full price"
    assert (await _read(client, auth, host["id"]))["you"]["rounds_cleared"] == 0, (
        "an untagged solve is not a duel round"
    )

    again = await judge.solve(first["slug"], duel_id=host["id"])
    assert again["status"] == "passed"
    assert again["xp_awarded"] == 0, "re-solving must not pay, or this proves nothing"

    after = await _read(client, auth, host["id"])
    assert after["you"]["rounds_cleared"] == 1
    assert after["you"]["cleared_ordinals"] == [first["ordinal"]]


async def test_duel_same_problem_three_times_clears_one_round(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str], judge: Judge
) -> None:
    """The other half of the rule: dropping `xp_awarded > 0` must not become a faucet.

    `cleared_ordinals` counts DISTINCT `duel_rounds.ordinal`, not submissions. Without
    that the previous test's rule — any passed submission counts — would let a toy fix
    the easiest problem in the set three times and sweep the duel in one sitting.
    """
    host, _ = await _start(client, auth, auth2)
    first = host["rounds"][0]

    for _ in range(3):
        body = await judge.solve(first["slug"], duel_id=host["id"])
        assert body["status"] == "passed"

    after = await _read(client, auth, host["id"])
    assert after["you"]["rounds_cleared"] == 1, "three solves of one problem are one round"
    assert after["you"]["cleared_ordinals"] == [first["ordinal"]]
    assert after["status"] == "active", "the duel must not have been swept"
    assert after["winner"] is None


async def test_duel_exactly_one_winner_when_both_finish(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
    judge2: Judge,
) -> None:
    """Both toys sweep, then both poll at once. That must settle to one winner.

    The guard is the conditional UPDATE in `close_out`. Rewrite it as a plain attribute
    assignment and this test is the only thing that notices: both polls pay out, and the
    duel has two winners and four ledger entries.
    """
    host, opponent = await _start(client, auth, auth2)
    await _clear(judge2, opponent, [r["ordinal"] for r in opponent["rounds"]])
    await _clear(judge, host, [r["ordinal"] for r in host["rounds"]])

    a, b = await asyncio.gather(
        client.get(f"/api/v1/duels/{host['id']}", headers=auth),
        client.get(f"/api/v1/duels/{host['id']}", headers=auth2),
    )
    assert a.status_code == 200 and b.status_code == 200, (a.text, b.text)
    assert a.json()["status"] == "completed"
    assert b.json()["status"] == "completed"

    # Opposite sides of the same verdict — never two winners, never two losers.
    assert {a.json()["winner"], b.json()["winner"]} == {"you", "them"}

    paid = await _duel_xp(db, host["id"])
    assert len(paid) == 2, f"expected one payout per toy, got {paid}"


async def test_duel_does_not_disturb_the_boss(
    client: AsyncClient,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
) -> None:
    """The regression guard: duels were added alongside the boss, not through it.

    A toy may be in both at once, so every submission here carries *both* tags. The
    boss must still complete and still pay exactly 450 — the same number it paid before
    duels existed.
    """
    host, _ = await _start(client, auth, auth2)

    fight = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    assert fight["status"] == "running"

    for slug in BOSS_ROUND_SLUGS:
        body = await judge.solve(slug, boss_session_id=fight["id"], duel_id=host["id"])
        assert body["status"] == "passed", f"{slug}: {body}"

    resp = await client.post(
        f"/api/v1/boss/sessions/{fight['id']}", headers=auth, json={"action": "complete"}
    )
    assert resp.status_code == 200, resp.text
    won = resp.json()
    assert won["status"] == "completed"
    assert won["rounds_cleared"] == 3
    assert won["xp_awarded"] == 450, "the boss payout changed"


# ---- lifecycle --------------------------------------------------------------


async def test_duel_full_lifecycle(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge2: Judge,
) -> None:
    opened = await _open(client, auth)
    assert opened["status"] == "waiting"
    assert opened["them"] is None
    assert opened["rounds"] == [], "a waiting duel must not reveal its problems"
    assert opened["you_are_host"] is True
    assert opened["invite_path"] == f"/academy/duel/{opened['code']}"

    joined = await _join(client, auth2, opened["code"])
    assert joined["status"] == "active"
    assert joined["you_are_host"] is False
    assert joined["them"]["toy_name"] == "Patches"
    assert len(joined["rounds"]) == settings.DUEL_ROUNDS

    host = await _read(client, auth, opened["id"])
    assert host["them"]["toy_name"] == "Pipsqueak"
    # Same problems, same order, for both toys — otherwise it isn't a race.
    assert [r["slug"] for r in host["rounds"]] == [r["slug"] for r in joined["rounds"]]

    await _clear(judge2, joined, [r["ordinal"] for r in joined["rounds"]])

    theirs = await _read(client, auth2, opened["id"])
    assert theirs["status"] == "completed"
    assert theirs["winner"] == "you"
    assert theirs["you"]["rounds_cleared"] == settings.DUEL_ROUNDS
    assert theirs["poll_after_ms"] == 0, "a finished duel must tell the client to stop"

    mine = await _read(client, auth, opened["id"])
    assert mine["winner"] == "them"
    assert mine["outcome_label"]

    # One ledger entry each; the loser cleared nothing, so only the winner was paid.
    paid = await _duel_xp(db, opened["id"])
    assert len(paid) == 1
    assert paid[0] >= settings.DUEL_XP_WIN

    # And the duel is over, so neither toy is still "in" one.
    assert (await client.get("/api/v1/duels/current", headers=auth)).json() is None


async def test_duel_rounds_are_hidden_until_start(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """The invite preview cannot leak the problem set — its schema has nowhere to put it."""
    opened = await _open(client, auth)

    resp = await client.get(f"/api/v1/duels/by-code/{opened['code']}", headers=auth2)
    assert resp.status_code == 200, resp.text
    preview = resp.json()
    assert preview["joinable"] is True
    assert preview["host_name"] == "Patches"
    assert "rounds" not in preview
    assert "slug" not in resp.text


async def test_duel_set_excludes_problems_either_toy_solved(
    client: AsyncClient,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
    judge2: Judge,
) -> None:
    """A head start is invisible to both players, so the pool is filtered against both."""
    assert (await judge.solve("two-sum"))["status"] == "passed"
    assert (await judge2.solve("valid-anagram"))["status"] == "passed"

    _, joined = await _start(client, auth, auth2)
    slugs = {r["slug"] for r in joined["rounds"]}
    assert "two-sum" not in slugs
    assert "valid-anagram" not in slugs


async def test_duel_ignores_an_outsiders_tag(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """A toy who is not in the duel cannot stuff it with submissions."""
    host, _ = await _start(client, auth, auth2)
    slug = host["rounds"][0]["slug"]

    outsider = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Squeak", "email": "squeak@playroom.com", "password": "windup123"},
    )
    headers = {"Authorization": f"Bearer {outsider.json()['access_token']}"}

    resp = await client.post(
        f"/api/v1/problems/{slug}/submit",
        headers=headers,
        json={"code": "def two_sum(a, b): return []", "duel_id": host["id"]},
    )
    assert resp.status_code == 202, resp.text

    tagged = await db.scalar(
        select(func.count())
        .select_from(Submission)
        .where(Submission.duel_id == host["id"])
    )
    assert int(tagged or 0) == 0, "an outsider's tag was written to the submission"


async def test_duel_ignores_a_problem_outside_the_set(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """Otherwise a toy clears three rounds by solving one easy problem three times."""
    host, _ = await _start(client, auth, auth2)
    in_set = {r["slug"] for r in host["rounds"]}
    outside = next(s for s in BOSS_ROUND_SLUGS + ["valid-anagram"] if s not in in_set)

    resp = await client.post(
        f"/api/v1/problems/{outside}/submit",
        headers=auth,
        json={"code": "def f(): pass", "duel_id": host["id"]},
    )
    assert resp.status_code == 202, resp.text

    tagged = await db.scalar(
        select(func.count())
        .select_from(Submission)
        .where(Submission.duel_id == host["id"])
    )
    assert int(tagged or 0) == 0


async def test_duel_ignores_a_bogus_tag(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """A duel id that names nothing is dropped, not refused.

    The whole point of `resolve_duel_tag` returning None rather than raising: a claim
    the server can't stand behind costs the toy their round, never their solve. A 4xx
    here would mean a stale tab could lose someone a correct answer.
    """
    host, _ = await _start(client, auth, auth2)
    slug = host["rounds"][0]["slug"]

    resp = await client.post(
        f"/api/v1/problems/{slug}/submit",
        headers=auth,
        json={"code": "def f(): pass", "duel_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 202, "a bad tag must not cost the toy their submission"
    assert await _tagged(db) == 0


async def test_duel_ignores_a_tag_once_the_clock_has_run_out(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """A tab that missed the buzzer still submits. It just can't clear a round any more."""
    host, _ = await _start(client, auth, auth2)
    slug = host["rounds"][0]["slug"]

    duel = await db.scalar(select(Duel).where(Duel.id == host["id"]))
    duel.started_at = datetime.now(UTC) - timedelta(seconds=duel.total_seconds + 5)
    await db.commit()

    resp = await client.post(
        f"/api/v1/problems/{slug}/submit",
        headers=auth,
        json={"code": "def f(): pass", "duel_id": host["id"]},
    )
    assert resp.status_code == 202, "the buzzer must not refuse a correct solve"
    assert await _tagged(db) == 0


async def test_duel_writes_no_rounds_until_someone_joins(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str]
) -> None:
    """The reveal is the rows not existing — asserted against the table, not the payload.

    `test_duel_rounds_are_hidden_until_start` checks that the invite *schema* has nowhere
    to put the problems. This checks the stronger claim underneath it: there is nothing
    to leak in the first place, so no serialiser, log line or future endpoint can spill
    it. A waiting duel is therefore also un-taggable — its id resolves to no round.
    """
    opened = await _open(client, auth)

    rows = int(
        await db.scalar(
            select(func.count()).select_from(DuelRound).where(DuelRound.duel_id == opened["id"])
        )
        or 0
    )
    assert rows == 0, "a waiting duel wrote duel_rounds before anyone accepted"

    resp = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": "def f(): pass", "duel_id": opened["id"]},
    )
    assert resp.status_code == 202
    assert await _tagged(db) == 0, "a duel nobody has joined must not accept tags"


async def test_boss_tag_from_another_toys_fight_is_dropped(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """The sibling hole `_resolve_boss_tag` closes, and the reason duels forced it open.

    `boss_session_id` used to be written through from the request body unchecked, so any
    toy could stuff a stranger's fight with submissions. Duels needed the same guard, and
    both tags are now claims the endpoint re-resolves. Dropped silently, like the duel's.
    """
    mine = (await client.post("/api/v1/boss/sessions", headers=auth)).json()

    resp = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth2,
        json={"code": "def f(): pass", "boss_session_id": mine["id"]},
    )
    assert resp.status_code == 202

    stuffed = int(
        await db.scalar(
            select(func.count())
            .select_from(Submission)
            .where(Submission.boss_session_id == mine["id"])
        )
        or 0
    )
    assert stuffed == 0, "another toy's submission was tagged into this fight"


async def test_duel_join_edge_cases(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    opened = await _open(client, auth)

    mine = await client.post(f"/api/v1/duels/by-code/{opened['code']}/join", headers=auth)
    assert mine.status_code == 409
    assert "yourself" in mine.json()["detail"]

    bad = await client.post("/api/v1/duels/by-code/ZZZZZZ/join", headers=auth2)
    assert bad.status_code == 404

    joined = await _join(client, auth2, opened["code"])

    # F5 on the invite link is normal, and must not be an error.
    again = await _join(client, auth2, opened["code"])
    assert again["id"] == joined["id"]
    assert again["status"] == "active"

    third = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Squeak", "email": "squeak@playroom.com", "password": "windup123"},
    )
    headers = {"Authorization": f"Bearer {third.json()['access_token']}"}
    full = await client.post(f"/api/v1/duels/by-code/{opened['code']}/join", headers=headers)
    assert full.status_code == 409
    assert "two toys" in full.json()["detail"]


async def test_duel_one_at_a_time(client: AsyncClient, auth: dict[str, str]) -> None:
    await _open(client, auth)
    second = await client.post("/api/v1/duels", headers=auth)
    assert second.status_code == 409
    assert "already in a duel" in second.json()["detail"]


async def test_duel_invite_expires(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str], monkeypatch
) -> None:
    opened = await _open(client, auth)
    monkeypatch.setattr(settings, "DUEL_INVITE_TTL_SECONDS", 0)

    preview = await client.get(f"/api/v1/duels/by-code/{opened['code']}", headers=auth2)
    assert preview.json()["joinable"] is False

    late = await client.post(f"/api/v1/duels/by-code/{opened['code']}/join", headers=auth2)
    assert late.status_code == 409
    assert "wound down" in late.json()["detail"]

    assert (await client.get("/api/v1/duels/current", headers=auth)).json() is None


async def test_duel_host_can_cancel_an_unaccepted_challenge(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    opened = await _open(client, auth)
    resp = await client.post(
        f"/api/v1/duels/{opened['id']}/actions", headers=auth, json={"action": "cancel"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "abandoned"

    # Cancelling frees the toy to open another.
    assert (await client.post("/api/v1/duels", headers=auth)).status_code == 201


async def test_duel_timeout_awards_the_leader(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
    judge2: Judge,
) -> None:
    """Nobody swept, but a close race should still feel decided — and pay no speed bonus."""
    host, opponent = await _start(client, auth, auth2)
    await _clear(judge, host, [r["ordinal"] for r in host["rounds"][:2]])
    await _clear(judge2, opponent, [r["ordinal"] for r in opponent["rounds"][:1]])

    # The clock is derived from started_at and nothing else, so winding that back is
    # the honest way to run it out.
    duel = await db.scalar(select(Duel).where(Duel.id == host["id"]))
    duel.started_at = datetime.now(UTC) - timedelta(seconds=duel.total_seconds + 1)
    await db.commit()

    settled = await _read(client, auth, host["id"])
    assert settled["status"] == "expired"
    assert settled["winner"] == "you"

    paid = await _duel_xp(db, host["id"])
    assert len(paid) == 2, f"the loser's cleared rounds should still pay: {paid}"
    winner_paid = max(paid)
    expected = settings.DUEL_XP_WIN + settings.DUEL_XP_PARTICIPATION * 2
    assert winner_paid == expected, "a win on the clock must not earn the speed bonus"


async def test_duel_timeout_level_on_rounds_is_a_draw(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
    judge2: Judge,
) -> None:
    """Neither swept and neither led. `decide` has to say so rather than pick a side."""
    host, opponent = await _start(client, auth, auth2)
    await _clear(judge, host, [host["rounds"][0]["ordinal"]])
    await _clear(judge2, opponent, [opponent["rounds"][1]["ordinal"]])

    duel = await db.scalar(select(Duel).where(Duel.id == host["id"]))
    duel.started_at = datetime.now(UTC) - timedelta(seconds=duel.total_seconds + 1)
    await db.commit()

    settled = await _read(client, auth, host["id"])
    assert settled["status"] == "expired"
    assert settled["winner"] == "draw"
    assert settled["outcome_label"], "a draw still needs a line from Sprocket"

    # Both sides see a draw — never one "you" and one "them".
    theirs = await _read(client, auth2, host["id"])
    assert theirs["winner"] == "draw"

    # A draw pays participation only, on both sides, and no win bonus.
    paid = await _duel_xp(db, host["id"])
    assert paid == [settings.DUEL_XP_PARTICIPATION, settings.DUEL_XP_PARTICIPATION]


async def test_duel_payout_does_not_run_through_settle(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge: Judge,
) -> None:
    """The duel bonus is paid by whoever reads the duel, never by the judge worker.

    Deliberate: paying from inside `settle()` would mean taking both toys' `progress`
    locks in submission order, which is a deadlock as soon as there are two workers. So
    a swept duel that nobody has looked at yet must have paid its solves and *nothing*
    else — the bonus appears only once a poll runs `close_out`.
    """
    host, _ = await _start(client, auth, auth2)
    await _clear(judge, host, [r["ordinal"] for r in host["rounds"]])

    assert await _duel_xp(db, host["id"]) == [], "settle() paid the duel bonus"
    sources = {str(s) for s in (await db.scalars(select(XpEvent.source))).all()}
    assert XpSource.SOLVE in sources, "the solves themselves should still have paid"
    assert XpSource.DUEL not in sources

    still_open = await db.scalar(select(Duel.status).where(Duel.id == host["id"]))
    assert still_open == DuelStatus.ACTIVE, "nothing but a read may close a duel"

    await _read(client, auth, host["id"])
    assert len(await _duel_xp(db, host["id"])) == 1, "the poll should have paid the winner"


async def test_duel_win_pins_on_the_duellist_badge(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """The new badge, and the reason `test_academy` now expects a sash of 13."""
    host, _ = await _start(client, auth, auth2)

    before = (await client.get("/api/v1/achievements", headers=auth)).json()
    assert "duellist" in {b["slug"] for b in before["items"]}, "the badge must be seeded"
    assert "duellist" not in {b["slug"] for b in before["items"] if b["earned"]}

    resp = await client.post(
        f"/api/v1/duels/{host['id']}/actions", headers=auth2, json={"action": "forfeit"}
    )
    assert resp.status_code == 200, resp.text
    await _read(client, auth, host["id"])

    sash = (await client.get("/api/v1/achievements", headers=auth)).json()
    assert "duellist" in {b["slug"] for b in sash["items"] if b["earned"]}

    # The toy who walked away won nothing, so they earn nothing to pin on.
    theirs = (await client.get("/api/v1/achievements", headers=auth2)).json()
    assert "duellist" not in {b["slug"] for b in theirs["items"] if b["earned"]}


async def test_duel_cancel_belongs_to_the_host_and_only_before_it_starts(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    """Cancel is the escape hatch for an invite nobody took, not for a race going badly."""
    opened = await _open(client, auth)

    # A toy who is in no duel of that name gets the same 404 as a bad id.
    stranger = await client.post(
        f"/api/v1/duels/{opened['id']}/actions", headers=auth2, json={"action": "cancel"}
    )
    assert stranger.status_code == 404

    joined = await _join(client, auth2, opened["code"])
    for headers in (auth, auth2):
        late = await client.post(
            f"/api/v1/duels/{joined['id']}/actions", headers=headers, json={"action": "cancel"}
        )
        assert late.status_code == 409, late.text
        assert "already running" in late.json()["detail"]

    # Forfeit is the only way out of a running duel — and it still works.
    out = await client.post(
        f"/api/v1/duels/{joined['id']}/actions", headers=auth, json={"action": "forfeit"}
    )
    assert out.status_code == 200, out.text
    assert out.json()["status"] == "completed"


async def test_duel_forfeit_hands_the_win_over(
    client: AsyncClient, db: AsyncSession, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    host, _ = await _start(client, auth, auth2)

    resp = await client.post(
        f"/api/v1/duels/{host['id']}/actions", headers=auth2, json={"action": "forfeit"}
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "completed"
    assert resp.json()["winner"] == "them"

    mine = await _read(client, auth, host["id"])
    assert mine["winner"] == "you"
    assert mine["you"]["xp_awarded"] == settings.DUEL_XP_FORFEIT_WIN

    # The toy who ran away collects nothing, so there is exactly one entry.
    paid = await _duel_xp(db, host["id"])
    assert paid == [settings.DUEL_XP_FORFEIT_WIN]


async def test_duel_daily_bonus_is_capped(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    monkeypatch,
) -> None:
    """Two accounts duelling on a loop is the exploit; the cap bounds what it's worth."""
    monkeypatch.setattr(settings, "DUEL_DAILY_BONUS_CAP", settings.DUEL_XP_FORFEIT_WIN + 10)

    for _ in range(2):
        host, _ = await _start(client, auth, auth2)
        resp = await client.post(
            f"/api/v1/duels/{host['id']}/actions", headers=auth2, json={"action": "forfeit"}
        )
        assert resp.status_code == 200, resp.text

    paid = await _duel_xp(db, host["id"])
    assert paid == [10, settings.DUEL_XP_FORFEIT_WIN], f"the cap was not applied: {paid}"
    # The ledger records the clamped figure, not the notional one — the heatmap reads it.
    assert sum(paid) == settings.DUEL_XP_FORFEIT_WIN + 10


async def test_duel_rejects_a_stranger(
    client: AsyncClient, auth: dict[str, str], auth2: dict[str, str]
) -> None:
    host, _ = await _start(client, auth, auth2)

    third = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Squeak", "email": "squeak@playroom.com", "password": "windup123"},
    )
    headers = {"Authorization": f"Bearer {third.json()['access_token']}"}

    resp = await client.get(f"/api/v1/duels/{host['id']}", headers=headers)
    assert resp.status_code == 404, "a stranger must not be able to watch a duel"


# ---- deciding ---------------------------------------------------------------


def _paper_duel(**overrides) -> Duel:
    """An unsaved Duel, for exercising `decide` without a database.

    `decide` reads five plain attributes and returns a dataclass; that it needs nothing
    else is exactly the property under test, so this deliberately never touches a
    session. A round-trip through the API could not tell purity from luck.
    """
    duel = Duel(
        code="ABC123",
        host_id=uuid.uuid4(),
        opponent_id=uuid.uuid4(),
        status=DuelStatus.ACTIVE,
        rounds_total=3,
        total_seconds=900,
    )
    for key, value in overrides.items():
        setattr(duel, key, value)
    return duel


def test_duel_decide_is_pure_so_both_polls_agree() -> None:
    """Both players run this, in their own sessions, possibly in the same millisecond.

    The conditional UPDATE in `close_out` picks which of them writes the verdict down —
    it does *not* pick the verdict. That only works because `decide` is a function of
    committed data, so calling it twice, or from either side, gives the same answer.
    Every branch below is called twice for that reason.
    """
    duel = _paper_duel()
    early = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)
    late = early + timedelta(seconds=30)

    def twice(*args):
        first, second = decide(duel, *args), decide(duel, *args)
        assert first == second, f"decide disagreed with itself: {first} vs {second}"
        return first

    # Still racing — nobody swept and the clock is running.
    assert twice(None, None, 1, 2, False) is None

    # One sweep ends it, whatever the other toy had done.
    won = twice(early, None, 3, 2, False)
    assert (won.status, won.winner_id, won.swept) == (DuelStatus.COMPLETED, duel.host_id, True)

    # Both swept: the earlier `judged_at` takes it, not the earlier poll.
    for host_at, opp_at, expected in ((early, late, duel.host_id), (late, early, duel.opponent_id)):
        out = twice(host_at, opp_at, 3, 3, False)
        assert out.winner_id == expected
        assert out.swept is True

    # Identical timestamps are a dead heat, not a coin toss.
    heat = twice(early, early, 3, 3, False)
    assert heat.winner_id is None and heat.status == DuelStatus.COMPLETED

    # Out of time: the leader on rounds takes it, but wins no speed bonus.
    clock = twice(None, None, 2, 1, True)
    assert (clock.status, clock.winner_id, clock.swept) == (
        DuelStatus.EXPIRED, duel.host_id, False,
    )
    assert twice(None, None, 1, 1, True).winner_id is None


def test_duel_decide_hands_a_forfeit_to_the_other_toy() -> None:
    """Whichever side walks away, the win goes to the one still standing."""
    assert decide(_paper_duel(), None, None, 0, 0, False) is None, (
        "an unforfeited, unfinished duel is still a race"
    )

    host_out = _paper_duel()
    host_out.forfeited_by_id = host_out.host_id
    out = decide(host_out, None, None, 0, 0, False)
    assert out.winner_id == host_out.opponent_id
    assert out.status == DuelStatus.COMPLETED
    assert out.swept is False, "a walkover must never earn the speed bonus"

    opp_out = _paper_duel()
    opp_out.forfeited_by_id = opp_out.opponent_id
    assert decide(opp_out, None, None, 0, 0, False).winner_id == opp_out.host_id


def test_duel_a_forfeit_cannot_rewrite_a_finished_sweep() -> None:
    """A race that is already won cannot be turned back into a walkover.

    Concretely: the opponent clears all three rounds. The duel is still `active`, because
    nothing closes it until somebody reads it — `settle()` deliberately doesn't, and the
    poll is on a 2s timer (and stops entirely while the tab is hidden). In that window
    the host taps Forfeit. Were `forfeited_by_id` checked first, the finished sweep would
    be discarded and the winner paid DUEL_XP_FORFEIT_WIN (60) instead of the sweep's
    ~470 — letting the loser choose the winner's payout by conceding at the right moment.

    The same ordering has a worse face: if the toy who *swept* forfeits, the win goes to
    the toy who cleared nothing — see the sibling test below.
    """
    duel = _paper_duel()
    swept_at = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)
    duel.forfeited_by_id = duel.host_id  # the host concedes...

    out = decide(duel, None, swept_at, 0, 3, False)  # ...after the opponent swept

    assert out.winner_id == duel.opponent_id, "the sweeper still wins, either way"
    assert out.swept is True, (
        "a sweep that had already happened was rewritten as a walkover, cutting the "
        "winner's payout from the sweep bonus down to DUEL_XP_FORFEIT_WIN"
    )


def test_duel_a_sweepers_own_forfeit_does_not_hand_over_the_win() -> None:
    """The starkest face of the ordering: a completed sweep must not lose to a mis-tap.

    The opponent has cleared every round; the host has cleared none. The opponent then
    forfeits — a fat-fingered tap, or a client that sends `forfeit` on unload. With the
    forfeit branch running first, the duel would go to the toy who solved nothing at all.
    """
    duel = _paper_duel()
    swept_at = datetime(2026, 7, 29, 12, 0, 0, tzinfo=UTC)
    duel.forfeited_by_id = duel.opponent_id

    out = decide(duel, None, swept_at, 0, 3, False)

    assert out.winner_id == duel.opponent_id, (
        "a toy who had already cleared every round lost the duel to a toy who cleared none"
    )


async def test_duel_forfeit_after_a_sweep_is_not_worth_the_tap(
    client: AsyncClient,
    db: AsyncSession,
    auth: dict[str, str],
    auth2: dict[str, str],
    judge2: Judge,
) -> None:
    """The same rule end to end, priced.

    The opponent sweeps; nothing has polled the duel, so it is still `active`; the host
    concedes. The winner is paid for the sweep they actually completed, not the walkover.
    """
    host, opponent = await _start(client, auth, auth2)
    await _clear(judge2, opponent, [r["ordinal"] for r in opponent["rounds"]])

    assert (
        await db.scalar(select(Duel.status).where(Duel.id == host["id"]))
    ) == DuelStatus.ACTIVE, "the duel closed before the forfeit — the race window is gone"

    conceded = await client.post(
        f"/api/v1/duels/{host['id']}/actions", headers=auth, json={"action": "forfeit"}
    )
    assert conceded.status_code == 200, conceded.text
    assert conceded.json()["winner"] == "them", "the sweeper wins either way"

    theirs = await _read(client, auth2, host["id"])
    floor = settings.DUEL_XP_WIN + settings.DUEL_XP_PARTICIPATION * settings.DUEL_ROUNDS
    assert theirs["you"]["xp_awarded"] >= floor, (
        "conceding after the opponent swept repriced their win as a walkover — "
        f"paid {theirs['you']['xp_awarded']}, a completed sweep is worth >= {floor}"
    )
