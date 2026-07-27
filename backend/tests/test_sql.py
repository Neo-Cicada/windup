"""The SQL pack.

Different enough from the others to be tested on its own: there is no entrypoint
to call and no signature to generate a stub from, and the "program" is a query
run against a fixture rather than a function run against arguments.

What has not changed is everything downstream — the same driver contract, the
same grader, and the same rule that the expected rows never enter the sandbox.
"""

import json

import pytest

from app.db.seed_data import PROBLEMS
from app.judge.grade import grade
from app.judge.languages import get_pack
from app.judge.languages.sql import ENTRYPOINT, PACK, build_guest
from app.judge.runner import SubprocessRunner
from app.models.enums import SubmissionStatus

SPEC = next(p for p in PROBLEMS if p["slug"] == "second-highest-salary")
SCHEMA = SPEC["harness_preamble"]

CASES = [
    {
        "ordinal": ordinal,
        "args": case["args"],
        "expected": case["expected"],
        "visibility": case.get("visibility", "hidden"),
        "label": case.get("label", ""),
    }
    for ordinal, case in enumerate(SPEC["tests"])
]


@pytest.fixture(scope="module")
def runner() -> SubprocessRunner:
    # SQL runs inside the Python interpreter, so the subprocess runner is enough
    # and the suite needs no wasm artifact for it.
    return SubprocessRunner()


def _judge(runner, query: str, cases=None):
    cases = CASES if cases is None else cases
    program = PACK.build_program(entrypoint="", preamble=SCHEMA, code=query)
    return grade(runner.run(program, cases), cases)


def test_the_seeded_solution_passes_its_own_cases(runner) -> None:
    verdict = _judge(runner, SPEC["solution"])
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure
    assert verdict.tests_passed == len(CASES)


def test_the_query_the_hint_warns_about_fails_the_case_it_warns_about(runner) -> None:
    """Dropping DISTINCT survives the examples and dies on a repeated top rating.

    Which is the entire argument for hidden cases: the visible ones do not
    distinguish these two queries, and the grade does.
    """
    naive = "SELECT (SELECT rating FROM recipes ORDER BY rating DESC LIMIT 1 OFFSET 1);"
    verdict = _judge(runner, naive)
    assert verdict.status == SubmissionStatus.FAILED
    assert 0 < verdict.tests_passed < len(CASES)
    assert verdict.failure["hidden"] is True
    assert "expected" not in verdict.failure, "a hidden case must not show its answer"


@pytest.mark.parametrize(
    ("label", "query", "wanted"),
    [
        ("mistyped keyword", "SELEKT * FROM recipes;", 'near "SELEKT"'),
        ("no such table", "SELECT * FROM cakes;", "no such table"),
        ("no such column", "SELECT flavour FROM recipes;", "no such column"),
    ],
)
def test_a_broken_query_reports_what_sqlite_said(label, query, wanted, runner) -> None:
    verdict = _judge(runner, query)
    assert verdict.status != SubmissionStatus.PASSED
    assert wanted in verdict.failure["error"], label


def test_a_query_that_answers_nothing_is_not_a_pass(runner) -> None:
    verdict = _judge(runner, "SELECT 1;")
    assert verdict.status == SubmissionStatus.FAILED


def test_each_case_gets_a_fresh_database(runner) -> None:
    """Rows from one case must not be visible to the next, or the later cases
    would be graded against a table nobody wrote."""
    counts = [
        {"ordinal": 0, "args": [{"table": "recipes", "rows": [[1]]}], "expected": [[1]]},
        {"ordinal": 1, "args": [{"table": "recipes", "rows": [[1], [2]]}], "expected": [[2]]},
        {"ordinal": 2, "args": [{"table": "recipes", "rows": []}], "expected": [[0]]},
    ]
    verdict = _judge(runner, "SELECT COUNT(*) FROM recipes;", counts)
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure


def test_a_quote_in_the_query_cannot_end_the_literal_it_is_embedded_in(runner) -> None:
    """The query is interpolated into a Python program, so this is the place a
    stray quote or backslash would break out of."""
    cases = [
        {"ordinal": 0, "args": [{"table": "recipes", "rows": []}], "expected": [["it's \\ ok"]]}
    ]
    verdict = _judge(runner, """SELECT 'it''s \\ ok';""", cases)
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure


def test_a_table_name_that_is_not_an_identifier_is_refused(runner) -> None:
    """The fixture's table name is the one thing here that cannot be a bound
    parameter, so it is checked rather than trusted."""
    cases = [
        {
            "ordinal": 0,
            "args": [{"table": "recipes; DROP TABLE recipes", "rows": [[1]]}],
            "expected": [[1]],
        }
    ]
    verdict = _judge(runner, "SELECT COUNT(*) FROM recipes;", cases)
    assert verdict.status != SubmissionStatus.PASSED
    assert "table name" in verdict.failure["error"]


def test_the_guest_program_is_python_and_names_no_other_runtime() -> None:
    """SQL adds a language and no artifact: sqlite3 is already in the standard
    library of the interpreter the judge has always run."""
    spec = PACK.build_program(entrypoint="", preamble=SCHEMA, code="SELECT 1;")
    assert spec.runner.language == "python"
    assert spec.runner.wasm_path.endswith("python.wasm")
    assert "sqlite3" in spec.source
    assert ENTRYPOINT in spec.source


def test_the_schema_and_query_are_embedded_as_python_literals() -> None:
    guest = build_guest(schema="CREATE TABLE t (a);", query="SELECT 'x';")
    assert json.dumps("SELECT 'x';") in guest
    assert json.dumps("CREATE TABLE t (a);") in guest


def test_the_pack_is_registered_and_offered() -> None:
    assert get_pack("sql").label == "SQL"
    assert get_pack("sql").runs_in_browser is True, "Pyodide bundles sqlite3"


async def test_the_sql_problem_is_graded_now(client, auth) -> None:
    body = (await client.get("/api/v1/problems/second-highest-salary", headers=auth)).json()
    assert body["graded"] is True
    assert body["language"] == "sql"
    assert [row["language"] for row in body["languages"]] == ["sql"]
    assert body["hidden_test_count"] == sum(
        1 for t in SPEC["tests"] if t.get("visibility") != "example"
    )


async def test_solving_it_pays_out(judge) -> None:
    result = await judge.solve("second-highest-salary", SPEC["solution"])
    assert result["status"] == "passed", result
    assert result["language"] == "sql"
    assert result["xp_awarded"] == SPEC["xp_reward"] * 2
