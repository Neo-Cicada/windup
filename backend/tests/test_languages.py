"""The language seam: signatures, packs, and which bench a problem offers.

The judge's guarantee is that adding a language changes none of the grading.
These tests pin the parts that make that true — one set of cases, one grader,
and a per-language bench that cannot quietly hand a pack another language's
source.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.judge.bench import bench_for, benches_for, offered_languages
from app.judge.languages import (
    DEFAULT_LANGUAGE,
    REGISTRY,
    UnknownLanguage,
    enabled_packs,
    get_pack,
    is_enabled,
)
from app.judge.signature import Signature, Type, expand, parse_signature, parse_type
from app.models import Problem, ProblemLanguage


# ---- the type language ------------------------------------------------------
@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("int", Type("int")),
        ("  bool  ", Type("bool")),
        ("list<int>", Type("list", Type("int"))),
        ("list<list<string>>", Type("list", Type("list", Type("string")))),
        ("matrix<string>", Type("matrix", Type("string"))),
        ("null<int>", Type("null", Type("int"))),
        ("treenode", Type("treenode")),
    ],
)
def test_parse_type_reads_the_shapes_the_catalogue_uses(text: str, expected: Type) -> None:
    assert parse_type(text) == expected


@pytest.mark.parametrize(
    "text", ["", "banana", "list", "list<int", "int<int>", "list<>", "null"]
)
def test_parse_type_refuses_anything_it_cannot_render(text: str) -> None:
    with pytest.raises(ValueError):
        parse_type(text)


def test_matrix_is_sugar_for_a_list_of_lists() -> None:
    assert expand(parse_type("matrix<int>")) == parse_type("list<list<int>>")
    assert expand(parse_type("list<matrix<int>>")) == parse_type("list<list<list<int>>>")


def test_a_param_name_that_is_not_an_identifier_is_refused() -> None:
    """Names land in generated source, so a bad one is a config error, not a stub."""
    with pytest.raises(ValueError, match="not a usable identifier"):
        Signature.parse({"params": [{"name": "two sum", "type": "int"}], "returns": "int"})


def test_a_duplicate_param_name_is_refused() -> None:
    with pytest.raises(ValueError, match="appears twice"):
        Signature.parse(
            {
                "params": [{"name": "n", "type": "int"}, {"name": "n", "type": "int"}],
                "returns": "int",
            }
        )


def test_a_problem_without_a_signature_is_allowed() -> None:
    assert parse_signature(None) is None


# ---- the registry -----------------------------------------------------------
def test_python_is_registered_and_offered() -> None:
    assert is_enabled(DEFAULT_LANGUAGE)
    assert get_pack(DEFAULT_LANGUAGE).label == "Python"
    assert [p.slug for p in enabled_packs()][0] == DEFAULT_LANGUAGE


def test_asking_for_a_language_no_pack_implements_says_so() -> None:
    with pytest.raises(UnknownLanguage, match="never heard of"):
        get_pack("brainfuck")


def test_a_registered_pack_this_deployment_does_not_offer_is_refused(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Registered and enabled are different questions — an artifact may not be fetched."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_LANGUAGES", [])
    with pytest.raises(UnknownLanguage, match="hasn't set up"):
        get_pack(DEFAULT_LANGUAGE)


def test_every_registered_pack_generates_a_stub_for_every_seeded_signature() -> None:
    """Codegen is what makes per-submission language choice affordable."""
    from app.db.seed_data import PROBLEMS

    for spec in PROBLEMS:
        signature = parse_signature(spec.get("signature"))
        if signature is None:
            continue
        for pack in REGISTRY.values():
            stub = pack.starter_code(entrypoint=spec["entrypoint"], signature=signature)
            assert spec["entrypoint"] in stub
            for param in signature.params:
                assert param.name in stub


def test_every_seeded_signature_parses() -> None:
    """A malformed one would surface as a broken problem page, so it is caught here."""
    from app.db.seed_data import PROBLEMS

    for spec in PROBLEMS:
        assert parse_signature(spec.get("signature")) is not None or "signature" not in spec


# ---- benches ----------------------------------------------------------------
async def _problem(db: AsyncSession, slug: str) -> Problem:
    return await db.scalar(
        select(Problem)
        .options(selectinload(Problem.languages))
        .where(Problem.slug == slug)
    )


async def test_a_problem_offers_its_own_language_without_any_row(
    db: AsyncSession, seeded: None
) -> None:
    """The default needs no bench row — it is what the problem was authored in."""
    problem = await _problem(db, "two-sum")
    problem.languages.clear()
    await db.commit()

    assert offered_languages(problem) == ["python"]
    assert bench_for(problem).entrypoint == "twoSum"
    assert bench_for(problem).starter_code == problem.starter_code


async def test_a_problem_does_not_offer_a_language_it_has_no_bench_for(
    db: AsyncSession, seeded: None
) -> None:
    problem = await _problem(db, "two-sum")
    assert "javascript" in offered_languages(problem), "seeded with a JavaScript bench"

    problem.languages.clear()
    await db.commit()
    with pytest.raises(UnknownLanguage, match="hasn't set up"):
        bench_for(problem, "javascript")


async def test_a_bench_row_adds_a_language_and_keeps_the_default_first(
    db: AsyncSession, seeded: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_LANGUAGES", ["python", "pretend"])
    monkeypatch.setitem(REGISTRY, "pretend", REGISTRY["python"])

    problem = await _problem(db, "two-sum")
    db.add(
        ProblemLanguage(
            problem_id=problem.id, language="pretend", starter_code="# a pretend bench"
        )
    )
    await db.commit()
    await db.refresh(problem, ["languages"])

    assert offered_languages(problem) == ["python", "pretend"]
    benches = benches_for(problem)
    assert benches[0].starter_code.startswith("def twoSum")
    assert benches[1].starter_code == "# a pretend bench"


async def test_one_languages_preamble_never_leaks_into_another(
    db: AsyncSession, seeded: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The preamble is source code. Handing Python's ListNode to another pack
    would produce a program that cannot parse."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_LANGUAGES", ["python", "pretend"])
    monkeypatch.setitem(REGISTRY, "pretend", REGISTRY["python"])

    problem = await _problem(db, "reverse-linked-list")
    assert "class ListNode" in bench_for(problem, "python").preamble

    db.add(ProblemLanguage(problem_id=problem.id, language="pretend"))
    await db.commit()
    await db.refresh(problem, ["languages"])
    assert bench_for(problem, "pretend").preamble == ""


async def test_a_bench_row_can_be_retired_without_losing_what_it_held(
    db: AsyncSession, seeded: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_LANGUAGES", ["python", "pretend"])
    monkeypatch.setitem(REGISTRY, "pretend", REGISTRY["python"])

    problem = await _problem(db, "two-sum")
    db.add(ProblemLanguage(problem_id=problem.id, language="pretend", enabled=False))
    await db.commit()
    await db.refresh(problem, ["languages"])

    assert offered_languages(problem) == ["python"]
    with pytest.raises(UnknownLanguage):
        bench_for(problem, "pretend")


# ---- the API ----------------------------------------------------------------
async def test_the_problem_payload_lists_the_benches_it_offers(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    resp = await client.get("/api/v1/problems/two-sum", headers=auth)
    body = resp.json()
    # Default first — it is the one the workbench opens on.
    assert body["language"] == "python"
    assert body["languages"][0]["language"] == "python"
    assert body["languages"][0]["starter_code"] == body["starter_code"]

    benches = {row["language"]: row for row in body["languages"]}
    assert set(benches) == set(settings.JUDGE_LANGUAGES)
    # Each bench opens on its own stub, in its own syntax.
    assert benches["python"]["starter_code"].startswith("def twoSum")
    assert "function twoSum(nums, target)" in benches["javascript"]["starter_code"]
    assert "def twoSum(nums, target)" in benches["ruby"]["starter_code"]
    assert "function twoSum($nums, $target)" in benches["php"]["starter_code"]
    # Only the ones with a browser engine offer the Run button.
    assert benches["javascript"]["runs_in_browser"] is True
    assert benches["ruby"]["runs_in_browser"] is False


async def test_a_structural_problem_hands_each_bench_its_own_preamble(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    """The preamble is source code — the wrong language's would not even parse."""
    body = (await client.get("/api/v1/problems/reverse-linked-list", headers=auth)).json()
    benches = {row["language"]: row for row in body["languages"]}
    assert "class ListNode" in benches["python"]["harness_preamble"]
    assert "function ListNode" in benches["javascript"]["harness_preamble"]


async def test_submitting_in_a_language_the_problem_does_not_offer_is_refused(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": "print('hello')", "language": "haskell"},
    )
    assert resp.status_code == 400
    assert "Sprocket" in resp.json()["detail"]


async def test_a_submission_naming_no_language_is_judged_as_the_problems_own(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    resp = await client.post(
        "/api/v1/problems/two-sum/submit",
        headers=auth,
        json={"code": "def twoSum(nums, target):\n    return [0, 1]"},
    )
    assert resp.status_code == 202
    detail = await client.get(
        f"/api/v1/submissions/{resp.json()['submission_id']}", headers=auth
    )
    assert detail.json()["language"] == "python"


async def test_the_languages_endpoint_reports_what_this_deployment_offers(
    client: AsyncClient, auth: dict[str, str]
) -> None:
    from app.core.config import settings

    resp = await client.get("/api/v1/languages", headers=auth)
    assert resp.status_code == 200
    assert [row["slug"] for row in resp.json()] == list(settings.JUDGE_LANGUAGES)


async def test_the_same_problem_can_be_solved_in_either_language(judge) -> None:
    """One set of hidden cases, two languages, the same verdict and the same payout."""
    from app.db.seed_data import PROBLEMS
    from tests.solutions import JAVASCRIPT_SOLUTIONS

    reward = next(p for p in PROBLEMS if p["slug"] == "two-sum")["xp_reward"]
    result = await judge.solve("two-sum", JAVASCRIPT_SOLUTIONS["two-sum"], language="javascript")
    assert result["status"] == "passed", result
    assert result["language"] == "javascript"
    # The same unaided payout a Python solve of this problem earns.
    assert result["xp_awarded"] == reward * 2


async def test_a_wrong_javascript_answer_is_graded_by_the_same_hidden_cases(judge) -> None:
    result = await judge.solve(
        "two-sum", "function twoSum(nums, target) { return [0, 1]; }", language="javascript"
    )
    assert result["status"] == "failed"
    # Right for the first case, wrong for the rest — graded by the very cases
    # that made the Python version fail, because there is only one set of them.
    assert 0 < result["tests_passed"] < result["tests_total"]
