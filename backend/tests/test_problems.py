from httpx import AsyncClient


async def test_problem_hides_locked_tiers(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get("/api/v1/problems/reverse-linked-list", headers=auth)
    assert resp.status_code == 200
    body = resp.json()

    assert body["help_shelf"]["explainer"]  # tier 1 is free
    assert body["help_shelf"]["hint"] is None
    assert body["help_shelf"]["approach"] is None
    assert body["help_shelf"]["solution"] is None
    assert body["chests"] == {"hint": False, "approach": False, "solution": False}
    assert body["unaided"] is True


async def test_unlocking_a_chest_forfeits_unaided(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    unlock = await client.post(
        "/api/v1/problems/reverse-linked-list/chests/hint", headers=auth
    )
    assert unlock.status_code == 200
    assert unlock.json()["content"]
    assert unlock.json()["unaided"] is False

    detail = (await client.get("/api/v1/problems/reverse-linked-list", headers=auth)).json()
    assert detail["help_shelf"]["hint"]
    assert detail["help_shelf"]["approach"] is None
    assert detail["unaided"] is False


async def test_unlocking_twice_is_idempotent(client: AsyncClient, auth: dict[str, str]) -> None:
    for _ in range(2):
        resp = await client.post("/api/v1/problems/two-sum/chests/solution", headers=auth)
        assert resp.status_code == 200
    assert resp.json()["chests"]["solution"] is True


async def test_unknown_problem_is_404(client: AsyncClient, auth: dict[str, str]) -> None:
    assert (await client.get("/api/v1/problems/no-such-toy", headers=auth)).status_code == 404


async def test_unaided_solve_pays_double(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.post(
        "/api/v1/problems/reverse-linked-list/submit",
        headers=auth,
        json={"code": "...", "status": "passed"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["unaided"] is True
    assert body["xp_awarded"] == 120  # 60 reward x2
    assert body["coins_awarded"] == 30
    assert body["progress"]["solved_count"] == 1
    assert body["progress"]["unaided_rate"] == 100
    assert "UNAIDED" in body["sprocket_message"]


async def test_aided_solve_pays_base(client: AsyncClient, auth: dict[str, str]) -> None:
    await client.post("/api/v1/problems/reverse-linked-list/chests/approach", headers=auth)
    body = (
        await client.post(
            "/api/v1/problems/reverse-linked-list/submit",
            headers=auth,
            json={"code": "...", "status": "passed"},
        )
    ).json()
    assert body["unaided"] is False
    assert body["xp_awarded"] == 60
    assert body["progress"]["unaided_rate"] == 0


async def test_resolving_the_same_problem_pays_nothing(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    first = await client.post(
        "/api/v1/problems/two-sum/submit", headers=auth, json={"status": "passed"}
    )
    second = await client.post(
        "/api/v1/problems/two-sum/submit", headers=auth, json={"status": "passed"}
    )
    assert first.json()["xp_awarded"] == 100
    assert second.json()["xp_awarded"] == 0
    assert second.json()["progress"]["solved_count"] == 1


async def test_failed_submission_pays_nothing(client: AsyncClient, auth: dict[str, str]) -> None:
    body = (
        await client.post(
            "/api/v1/problems/two-sum/submit", headers=auth, json={"status": "failed"}
        )
    ).json()
    assert body["xp_awarded"] == 0
    assert body["progress"]["solved_count"] == 0
    assert body["confetti"] == 0


async def test_first_solve_earns_the_first_fix_badge(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    body = (
        await client.post(
            "/api/v1/problems/two-sum/submit", headers=auth, json={"status": "passed"}
        )
    ).json()
    assert "first-fix" in {b["slug"] for b in body["newly_earned"]}

    sash = (await client.get("/api/v1/achievements", headers=auth)).json()
    earned = {b["slug"] for b in sash["items"] if b["earned"]}
    assert "first-fix" in earned
    assert sash["label"].endswith(f"/{sash['total_count']}")


async def test_problems_can_be_filtered_by_zone(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get("/api/v1/problems?zone=marble-run", headers=auth)
    assert resp.status_code == 200
    assert {p["zone_slug"] for p in resp.json()} == {"marble-run"}
