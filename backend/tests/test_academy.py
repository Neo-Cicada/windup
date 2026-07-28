from httpx import AsyncClient

from app.db.seed_data import PROBLEMS, ZONES
from app.models import Progress
from app.services.leveling import apply_xp, level_name, touch_streak
from tests.conftest import Judge

# Read off the catalogue rather than written down here. These assertions are
# about the *endpoint* reporting what was seeded; pinning literals made adding a
# problem to a corner look like a broken zone count.
BUILDING_BLOCKS = next(z for z in ZONES if z["slug"] == "building-blocks")
BUILDING_BLOCKS_TOTAL = sum(1 for p in PROBLEMS if p["zone"] == "building-blocks")


def test_apply_xp_rolls_the_meter_like_the_frontend() -> None:
    progress = Progress(xp=340, xp_max=500, level=3, total_xp=340, coins=0)
    outcome = apply_xp(progress, 200)

    assert outcome.leveled_up is True
    assert progress.level == 4
    assert progress.xp == 40  # 340 + 200 - 500
    assert progress.xp_max == 560  # round(500 * 1.12 / 10) * 10
    assert progress.coins == 50  # round(200 / 4)
    assert progress.total_xp == 540


def test_apply_xp_ignores_zero_and_negative() -> None:
    progress = Progress(xp=10, xp_max=500, level=1, total_xp=10, coins=0)
    assert apply_xp(progress, 0).xp_awarded == 0
    assert apply_xp(progress, -50).xp_awarded == 0
    assert progress.xp == 10


def test_level_names_are_clamped() -> None:
    assert level_name(1) == "Freshly Unboxed"
    assert level_name(5) == "Top-Shelf Talent"
    assert level_name(99) == "Legendary Toy"


def test_streak_extends_then_resets() -> None:
    from datetime import date

    progress = Progress(streak=0, longest_streak=0)
    assert touch_streak(progress, date(2026, 7, 1)) is True
    assert progress.streak == 1

    touch_streak(progress, date(2026, 7, 2))
    assert progress.streak == 2

    # same day twice does nothing
    assert touch_streak(progress, date(2026, 7, 2)) is False
    assert progress.streak == 2

    # a missed day resets, but the record stands
    touch_streak(progress, date(2026, 7, 5))
    assert progress.streak == 1
    assert progress.longest_streak == 2


async def test_dashboard_returns_one_payload(client: AsyncClient, auth: dict[str, str]) -> None:
    body = (await client.get("/api/v1/dashboard", headers=auth)).json()
    assert body["toy_name"] == "Patches"
    assert body["progress"]["level"] == 1
    assert body["badges_label"].endswith("/12")
    assert len(body["quests"]) == 3  # settings.DAILY_QUESTS
    assert body["rank"] == 1


async def test_daily_quests_are_stable_within_a_day(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    first = (await client.get("/api/v1/quests/today", headers=auth)).json()
    second = (await client.get("/api/v1/quests/today", headers=auth)).json()
    assert [q["id"] for q in first] == [q["id"] for q in second]
    # spread across different toy corners
    assert len({q["zone"] for q in first}) == len(first)


async def test_solving_completes_the_matching_quest(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    quests = (await client.get("/api/v1/quests/today", headers=auth)).json()
    slug = quests[0]["slug"]
    assert (await judge.solve(slug))["status"] == "passed"

    after = (await client.get("/api/v1/quests/today", headers=auth)).json()
    done = next(q for q in after if q["slug"] == slug)
    assert done["completed"] is True
    assert done["pct"] == 100


async def test_quest_progress_can_be_nudged(client: AsyncClient, auth: dict[str, str]) -> None:
    quest = (await client.get("/api/v1/quests/today", headers=auth)).json()[0]
    resp = await client.patch(f"/api/v1/quests/{quest['id']}", headers=auth, json={"pct": 60})
    assert resp.status_code == 200
    assert resp.json()["pct"] == 60

    assert (
        await client.patch(f"/api/v1/quests/{quest['id']}", headers=auth, json={"pct": 900})
    ).status_code == 422


async def test_wind_up_adds_charge(client: AsyncClient, auth: dict[str, str]) -> None:
    before = (await client.get("/api/v1/me/progress", headers=auth)).json()
    body = (await client.post("/api/v1/me/wind-up", headers=auth)).json()
    assert body["progress"]["total_xp"] == before["total_xp"] + 40
    assert body["progress"]["streak"] == 1
    assert body["wind_up_available"] is False


async def test_wind_up_pays_out_only_once_a_day(client: AsyncClient, auth: dict[str, str]) -> None:
    """Without a cap this endpoint is an unlimited XP faucet."""
    assert (await client.get("/api/v1/dashboard", headers=auth)).json()["wind_up_available"] is True

    first = (await client.post("/api/v1/me/wind-up", headers=auth)).json()
    baseline = first["progress"]["total_xp"]

    for _ in range(5):
        again = (await client.post("/api/v1/me/wind-up", headers=auth)).json()
        assert again["progress"]["total_xp"] == baseline
        assert again["wind_up_available"] is False


async def test_zones_report_clear_counts(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    await judge.solve("two-sum")
    zones = (await client.get("/api/v1/zones", headers=auth)).json()
    blocks = next(z for z in zones if z["slug"] == "building-blocks")
    assert blocks["done"] == 1
    assert blocks["total"] == BUILDING_BLOCKS_TOTAL
    assert blocks["pattern"] == BUILDING_BLOCKS["pattern"]


async def test_analytics_tracks_the_week(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    await judge.solve("reverse-linked-list")
    body = (await client.get("/api/v1/analytics", headers=auth)).json()

    # 120 for the unaided solve, plus whatever badges it unlocked. The badge set
    # is not fixed: `night-owl` fires on the hour the submission was created, so
    # pinning a literal total makes this test fail for anyone running it between
    # midnight and 5am. Read the badges back instead of guessing at them.
    sash = (await client.get("/api/v1/achievements", headers=auth)).json()
    earned = [b for b in sash["items"] if b["earned"]]
    assert "first-fix" in {b["slug"] for b in earned}
    expected_today = 120 + 50 * len(earned)

    assert len(body["xp_history"]) == 7
    assert body["xp_history"][-1]["value"] == expected_today
    assert body["xp_this_week"] == expected_today
    assert len(body["streak"]["cells"]) == 36
    assert body["unaided_rate"] == 100
    assert len(body["coverage"]) == len(ZONES)


async def test_leaderboard_marks_you(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Domino", "email": "domino@playroom.com", "password": "windup123"},
    )
    await judge.solve("two-sum")

    body = (await client.get("/api/v1/leaderboard", headers=auth)).json()
    you = next(entry for entry in body["leaders"] if entry["you"])
    assert you["name"].endswith("(You)")
    assert you["rank"] == 1
    assert body["your_rank"] == 1


async def test_account_can_be_saved(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.patch(
        "/api/v1/me",
        headers=auth,
        json={
            "toy_name": "Patchwork",
            "notifications": {"streak": False, "weekly": True, "bosses": True},
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["toy_name"] == "Patchwork"
    assert body["notifications"] == {"streak": False, "weekly": True, "bosses": True}


async def test_profile_patch_cannot_change_credentials(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    """A stolen access token must not be enough to take the account over."""
    resp = await client.patch(
        "/api/v1/me",
        headers=auth,
        json={"email": "attacker@playroom.com", "password": "takenover123"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "patches@playroom.com"

    # neither the new password nor the new address works
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "patches@playroom.com", "password": "takenover123"},
        )
    ).status_code == 401
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "attacker@playroom.com", "password": "windup123"},
        )
    ).status_code == 401


async def test_email_change_requires_the_password(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    bad = await client.post(
        "/api/v1/me/email",
        headers=auth,
        json={"current_password": "wrong-one", "new_email": "patches2@playroom.com"},
    )
    assert bad.status_code == 400

    good = await client.post(
        "/api/v1/me/email",
        headers=auth,
        json={"current_password": "windup123", "new_email": "patches2@playroom.com"},
    )
    assert good.status_code == 200
    assert good.json()["email"] == "patches2@playroom.com"


async def test_account_email_collision_is_409(client: AsyncClient, auth: dict[str, str]) -> None:
    await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Domino", "email": "domino@playroom.com", "password": "windup123"},
    )
    resp = await client.post(
        "/api/v1/me/email",
        headers=auth,
        json={"current_password": "windup123", "new_email": "domino@playroom.com"},
    )
    assert resp.status_code == 409


async def test_password_change_requires_the_old_one(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    bad = await client.post(
        "/api/v1/me/password",
        headers=auth,
        json={"current_password": "wrong-one", "new_password": "newwindup123"},
    )
    assert bad.status_code == 400

    good = await client.post(
        "/api/v1/me/password",
        headers=auth,
        json={"current_password": "windup123", "new_password": "newwindup123"},
    )
    assert good.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "patches@playroom.com", "password": "newwindup123"},
        )
    ).status_code == 200


BOSS_ROUND_SLUGS = ["two-sum", "reverse-linked-list", "number-of-islands"]


async def _clear_boss_rounds(judge: Judge, session_id: str, slugs: list[str]) -> None:
    """Actually solve each round. A boss round can no longer be cleared by asking."""
    for slug in slugs:
        body = await judge.solve(slug, boss_session_id=session_id)
        assert body["status"] == "passed", f"{slug}: {body}"


async def test_boss_battle_lifecycle(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    started = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    assert started["status"] == "running"
    assert started["time_label"] == "15:00"
    assert started["button_label"] == "Pause fight"

    session_id = started["id"]
    paused = (
        await client.post(
            f"/api/v1/boss/sessions/{session_id}", headers=auth, json={"action": "pause"}
        )
    ).json()
    assert paused["status"] == "paused"

    await _clear_boss_rounds(judge, session_id, BOSS_ROUND_SLUGS)

    done = (
        await client.post(
            f"/api/v1/boss/sessions/{session_id}", headers=auth, json={"action": "complete"}
        )
    ).json()
    assert done["status"] == "completed"
    assert done["rounds_cleared"] == 3
    assert done["xp_awarded"] == 450  # 300 base + full speed bonus
    assert done["button_label"] == "Rematch"

    # a finished fight is no longer the current one
    assert (await client.get("/api/v1/boss/current", headers=auth)).json() is None

    sash = (await client.get("/api/v1/achievements", headers=auth)).json()
    assert "boss-slayer" in {b["slug"] for b in sash["items"] if b["earned"]}


async def test_boss_cannot_be_won_without_solving(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    """start + complete used to be a two-request, infinitely repeatable 450 XP faucet."""
    started = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    before = (await client.get("/api/v1/me/progress", headers=auth)).json()["total_xp"]

    resp = await client.post(
        f"/api/v1/boss/sessions/{started['id']}", headers=auth, json={"action": "complete"}
    )
    assert resp.status_code == 409
    assert "0 of 3" in resp.json()["detail"]

    after = (await client.get("/api/v1/me/progress", headers=auth)).json()["total_xp"]
    assert after == before


async def test_boss_partial_clear_does_not_pay(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    started = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    await _clear_boss_rounds(judge, started["id"], BOSS_ROUND_SLUGS[:2])

    resp = await client.post(
        f"/api/v1/boss/sessions/{started['id']}", headers=auth, json={"action": "complete"}
    )
    assert resp.status_code == 409
    assert "2 of 3" in resp.json()["detail"]


async def test_boss_rematch_cannot_reuse_old_solves(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    """Re-solving already-solved problems pays no XP, so it can't clear a fresh fight."""
    first = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    await _clear_boss_rounds(judge, first["id"], BOSS_ROUND_SLUGS)
    await client.post(
        f"/api/v1/boss/sessions/{first['id']}", headers=auth, json={"action": "complete"}
    )

    rematch = (await client.post("/api/v1/boss/sessions", headers=auth)).json()
    await _clear_boss_rounds(judge, rematch["id"], BOSS_ROUND_SLUGS)

    resp = await client.post(
        f"/api/v1/boss/sessions/{rematch['id']}", headers=auth, json={"action": "complete"}
    )
    assert resp.status_code == 409
    assert "0 of 3" in resp.json()["detail"]


async def test_boss_rejects_someone_elses_session(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    mine = (await client.post("/api/v1/boss/sessions", headers=auth)).json()

    other = await client.post(
        "/api/v1/auth/signup",
        json={"toy_name": "Squeak", "email": "squeak@playroom.com", "password": "windup123"},
    )
    other_auth = {"Authorization": f"Bearer {other.json()['access_token']}"}

    resp = await client.post(
        f"/api/v1/boss/sessions/{mine['id']}", headers=other_auth, json={"action": "complete"}
    )
    assert resp.status_code == 404
