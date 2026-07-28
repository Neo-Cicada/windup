import json

from httpx import AsyncClient

from tests.conftest import Judge


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


async def test_hidden_test_cases_never_reach_the_client(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    """The hidden cases are what make the verdict worth anything.

    They must not be inferable from the payload — otherwise a toy could read the
    answers off the wire instead of writing the function.
    """
    from app.db.seed_data import PROBLEMS

    for spec in (p for p in PROBLEMS if p.get("graded", True)):
        body = (await client.get(f"/api/v1/problems/{spec['slug']}", headers=auth)).json()

        examples = [t for t in spec["tests"] if t.get("visibility") == "example"]
        hidden = [t for t in spec["tests"] if t.get("visibility") != "example"]

        # `example_tests` is the only place a case is serialised, so the property
        # is structural: everything shipped must be one of the visible examples.
        # (Substring-searching the payload gives false positives both ways — a
        # hidden case can share an answer with a visible one, and an argument
        # list like `[[]]` appears incidentally inside the harness preamble.)
        # sort_keys because a case whose args hold an object comes back from
        # JSONB in whatever key order Postgres felt like.
        def key(case):
            return (
                json.dumps(case["args"], sort_keys=True),
                json.dumps(case["expected"], sort_keys=True),
            )

        shipped = {key(t) for t in body["example_tests"]}
        visible = {key(t) for t in examples}
        secret = {key(t) for t in hidden}

        assert shipped == visible, f"{spec['slug']}: shipped cases are not the visible examples"
        assert not (shipped & secret), f"{spec['slug']}: a hidden case was shipped"
        assert body["hidden_test_count"] == len(hidden)
        assert hidden, f"{spec['slug']}: nothing hidden means nothing to grade against"


async def test_unlocking_a_chest_forfeits_unaided(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    unlock = await client.post("/api/v1/problems/reverse-linked-list/chests/hint", headers=auth)
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


async def test_unaided_solve_pays_double(judge: Judge) -> None:
    body = await judge.solve("reverse-linked-list")
    assert body["status"] == "passed"
    assert body["tests_passed"] == body["tests_total"] > 0
    assert body["unaided"] is True
    assert body["xp_awarded"] == 120  # 60 reward x2
    assert body["coins_awarded"] == 30
    assert body["progress"]["solved_count"] == 1
    assert body["progress"]["unaided_rate"] == 100
    assert "UNAIDED" in body["sprocket_message"]


async def test_aided_solve_pays_base(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    await client.post("/api/v1/problems/reverse-linked-list/chests/approach", headers=auth)
    body = await judge.solve("reverse-linked-list")
    assert body["status"] == "passed"
    assert body["unaided"] is False
    assert body["xp_awarded"] == 60
    assert body["progress"]["unaided_rate"] == 0


async def test_resolving_the_same_problem_pays_nothing(judge: Judge) -> None:
    first = await judge.solve("two-sum")
    second = await judge.solve("two-sum")
    assert first["xp_awarded"] == 100
    assert second["status"] == "passed"
    assert second["xp_awarded"] == 0
    assert second["progress"]["solved_count"] == 1


async def test_first_solve_earns_the_first_fix_badge(
    client: AsyncClient, auth: dict[str, str], judge: Judge
) -> None:
    body = await judge.solve("two-sum")
    assert "first-fix" in {b["slug"] for b in body["newly_earned"]}

    sash = (await client.get("/api/v1/achievements", headers=auth)).json()
    earned = {b["slug"] for b in sash["items"] if b["earned"]}
    assert "first-fix" in earned
    assert sash["label"].endswith(f"/{sash['total_count']}")


async def test_problems_can_be_filtered_by_zone(client: AsyncClient, auth: dict[str, str]) -> None:
    resp = await client.get("/api/v1/problems?zone=marble-run", headers=auth)
    assert resp.status_code == 200
    assert {p["zone_slug"] for p in resp.json()} == {"marble-run"}
