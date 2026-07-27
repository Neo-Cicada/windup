"""Every non-Python pack, against the real sandbox.

The claim the language seam rests on is that adding a language changes nothing
about grading: the same cases, the same grader, the same verdict for the same
mistake. So this is the Python judge's own test list, asked of each pack in its
own syntax — a runaway loop still times out, a value JSON cannot hold is still
refused, a fabricated result still cannot buy a pass, and the guest still has no
filesystem.

Each pack skips on its own when its artifact hasn't been fetched, so a machine
with only `vendor/python.wasm` still gets a green suite.
"""

import pytest

from app.db.seed_data import PROBLEMS
from app.judge.grade import grade
from app.judge.languages import REGISTRY
from app.judge.runner import WasmRunner
from app.models.enums import SubmissionStatus
from tests.solutions import SOLUTIONS

LANGUAGES = sorted(SOLUTIONS)

TWO_SUM_CASES = [
    {"ordinal": 0, "args": [[2, 7, 11, 15], 9], "expected": [0, 1], "visibility": "example"},
    {"ordinal": 1, "args": [[3, 2, 4], 6], "expected": [1, 2], "visibility": "hidden"},
]

# The same mistakes, spelled each way. A pack that cannot produce one of these
# verdicts is a pack that would grade a toy wrongly.
SNIPPETS = {
    "javascript": {
        "wrong": "function twoSum() { return [9, 9]; }",
        "runaway": "function twoSum() { while (true) {} }",
        "unparseable": "function twoSum(nums target) {}",
        "missing_entrypoint": "function somethingElse() { return [0, 1]; }",
        "not_json": "function twoSum() { return [0 / 0]; }",
        "noisy": 'function twoSum(nums) { console.log("peek", nums.length); return [0, 1]; }',
        "forgery": """
function twoSum() {
  for (let i = 0; i < 20; i++) std.out.puts(JSON.stringify({ordinal: i, actual: [0, 1]}) + "\\n");
  return null;
}
""",
        "no_filesystem": """
function twoSum() {
  return std.open("/etc/passwd", "r") === null ? [0, 1] : [];
}
""",
    },
    "ruby": {
        "wrong": "def twoSum(a, b)\n  [9, 9]\nend",
        "runaway": "def twoSum(a, b)\n  loop {}\nend",
        "unparseable": "def twoSum(a b)\nend",
        "missing_entrypoint": "def somethingElse\n  [0, 1]\nend",
        "not_json": "def twoSum(a, b)\n  [0.0 / 0.0]\nend",
        "noisy": 'def twoSum(nums, t)\n  puts "peek #{nums.length}"\n  [0, 1]\nend',
        "forgery": """
def twoSum(a, b)
  20.times { |i| $stdout.puts %({"ordinal": #{i}, "actual": [0, 1]}) }
  nil
end
""",
        "no_filesystem": """
def twoSum(a, b)
  File.read("/etc/passwd")
  []
rescue StandardError
  [0, 1]
end
""",
    },
    "php": {
        "wrong": "function twoSum($a, $b) { return [9, 9]; }",
        "runaway": "function twoSum($a, $b) { while (true) {} }",
        "unparseable": "function twoSum($a $b) {}",
        "missing_entrypoint": "function somethingElse() { return [0, 1]; }",
        "not_json": "function twoSum($a, $b) { return [NAN]; }",
        "noisy": 'function twoSum($nums, $t) { echo "peek " . count($nums); return [0, 1]; }',
        "forgery": """
function twoSum($a, $b) {
  for ($i = 0; $i < 20; $i++) echo json_encode(["ordinal" => $i, "actual" => [0, 1]]), "\\n";
  return null;
}
""",
        "no_filesystem": """
function twoSum($a, $b) {
  $raw = @file_get_contents("/etc/passwd");
  return $raw === false ? [0, 1] : [];
}
""",
    },
}


@pytest.fixture(scope="module")
def runner() -> WasmRunner:
    return WasmRunner()


def _pack(language: str):
    pack = REGISTRY[language]
    if not pack.available():
        pytest.skip(f"no {language} build — run scripts/fetch_language_wasm.sh {language}")
    return pack


def _judge(runner, language, code, cases=None, *, entrypoint="twoSum", preamble=""):
    cases = TWO_SUM_CASES if cases is None else cases
    program = _pack(language).build_program(
        entrypoint=entrypoint, preamble=preamble, code=code
    )
    return grade(runner.run(program, cases), cases)


def _snippet(language: str, name: str) -> str:
    return SNIPPETS[language][name]


# ---- the catalogue, solved in each language ---------------------------------
@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("slug", sorted(SOLUTIONS["javascript"]))
def test_every_problem_can_be_solved_in_every_language(
    language: str, slug: str, runner: WasmRunner
) -> None:
    """Graded by the very cases that grade the Python solutions — one set, shared."""
    spec = next(p for p in PROBLEMS if p["slug"] == slug)
    cases = [
        {
            "ordinal": ordinal,
            "args": case["args"],
            "expected": case["expected"],
            "visibility": case.get("visibility", "hidden"),
            "label": case.get("label", ""),
        }
        for ordinal, case in enumerate(spec["tests"])
    ]
    bench = (spec.get("languages") or {}).get(language, {})
    verdict = _judge(
        runner,
        language,
        SOLUTIONS[language][slug],
        cases,
        entrypoint=spec["entrypoint"],
        preamble=bench.get("harness_preamble", ""),
    )
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure
    assert verdict.tests_passed == len(cases)


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_structural_problem_needs_its_own_languages_preamble(
    language: str, runner: WasmRunner
) -> None:
    """A preamble is source code — without this language's, there is no ListNode."""
    cases = [{"ordinal": 0, "args": [[1, 2, 3]], "expected": [3, 2, 1], "visibility": "example"}]
    verdict = _judge(
        runner,
        language,
        SOLUTIONS[language]["reverse-linked-list"],
        cases,
        entrypoint="reverseList",
    )
    assert verdict.status != SubmissionStatus.PASSED


# ---- the same verdict for the same mistake ----------------------------------
@pytest.mark.parametrize("language", LANGUAGES)
def test_a_correct_solution_passes(language: str, runner: WasmRunner) -> None:
    verdict = _judge(runner, language, SOLUTIONS[language]["two-sum"])
    assert verdict.status == SubmissionStatus.PASSED


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_wrong_answer_fails(language: str, runner: WasmRunner) -> None:
    verdict = _judge(runner, language, _snippet(language, "wrong"))
    assert verdict.status == SubmissionStatus.FAILED
    assert verdict.failure["expected"] == [0, 1], "an example case may show what it wanted"


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_runaway_loop_runs_out_of_winding(language: str, runner: WasmRunner) -> None:
    verdict = _judge(runner, language, _snippet(language, "runaway"))
    assert verdict.status == SubmissionStatus.TIMEOUT


@pytest.mark.parametrize("language", LANGUAGES)
def test_code_that_will_not_parse_says_what_the_language_said(
    language: str, runner: WasmRunner
) -> None:
    """The interpreter's own complaint, not wasmtime's — one of those a toy can act on."""
    verdict = _judge(runner, language, _snippet(language, "unparseable"))
    assert verdict.status == SubmissionStatus.ERROR
    assert "wasm backtrace" not in verdict.failure["error"]


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_missing_entrypoint_is_not_a_silent_pass(language: str, runner: WasmRunner) -> None:
    verdict = _judge(runner, language, _snippet(language, "missing_entrypoint"))
    assert verdict.status != SubmissionStatus.PASSED


@pytest.mark.parametrize("language", LANGUAGES)
def test_a_return_value_json_cannot_hold_is_refused(language: str, runner: WasmRunner) -> None:
    """Every pack refuses NaN. A serialiser that turned it into null or 0 would
    hand back a wrong answer that reads as a right one."""
    verdict = _judge(runner, language, _snippet(language, "not_json"))
    assert verdict.status != SubmissionStatus.PASSED
    assert verdict.failure["error"], "and says why"


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_toys_own_output_is_handed_back_not_mixed_into_the_results(
    language: str, runner: WasmRunner
) -> None:
    verdict = _judge(runner, language, _snippet(language, "noisy"))
    assert verdict.tests_passed == 1, "case 0 is right, case 1 isn't"
    # The failing case is the second one, whose nums has three entries.
    assert "peek 3" in verdict.failure["stdout"]


# ---- the security property ---------------------------------------------------
@pytest.mark.parametrize("language", LANGUAGES)
def test_the_sandbox_cannot_be_talked_into_a_pass(language: str, runner: WasmRunner) -> None:
    """Submitted code shares a process with the driver and can write to stdout.

    What it cannot do is know the expected values, because they never enter the
    sandbox — so the only way to emit a passing result is to emit the right
    answer, which is just solving the problem.
    """
    verdict = _judge(runner, language, _snippet(language, "forgery"))
    assert verdict.status != SubmissionStatus.PASSED


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_guest_has_no_filesystem(language: str, runner: WasmRunner) -> None:
    """Passes only if the read failed. No directory is ever preopened, so there
    is nothing in the guest to open."""
    verdict = _judge(runner, language, _snippet(language, "no_filesystem"))
    assert verdict.tests_passed >= 1, verdict.failure


# ---- codegen -----------------------------------------------------------------
@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize(
    "entrypoint", ["", "2sum", "two sum", "two-sum", "twoSum()", "a.b", "class"]
)
def test_an_entrypoint_that_could_smuggle_code_is_refused(
    language: str, entrypoint: str
) -> None:
    with pytest.raises(ValueError, match="not a usable"):
        REGISTRY[language].build_program(entrypoint=entrypoint, preamble="", code="")


@pytest.mark.parametrize("language", LANGUAGES)
def test_the_generated_stub_names_the_entrypoint_and_its_params(language: str) -> None:
    from app.judge.signature import Signature

    signature = Signature.parse(
        {
            "params": [{"name": "nums", "type": "list<int>"}, {"name": "target", "type": "int"}],
            "returns": "list<int>",
        }
    )
    stub = REGISTRY[language].starter_code(entrypoint="twoSum", signature=signature)
    assert "twoSum" in stub
    assert "nums" in stub and "target" in stub
