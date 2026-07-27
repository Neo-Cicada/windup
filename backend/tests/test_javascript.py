"""The JavaScript pack, against the real sandbox.

The claim these tests exist to check is that a second language changes nothing
about grading: the same cases, the same grader, the same verdicts for the same
mistakes. So most of what is here is the Python judge's own tests asked again in
another syntax — a runaway loop still times out, a fabricated result still can't
buy a pass, and the guest still has no filesystem.

Skipped wholesale when vendor/quickjs.wasm hasn't been fetched.
"""

import pytest

from app.db.seed_data import PROBLEMS
from app.judge.grade import grade
from app.judge.languages.javascript import PACK, jsdoc
from app.judge.runner import WasmRunner
from app.judge.signature import parse_type
from app.models.enums import SubmissionStatus

pytestmark = pytest.mark.skipif(
    not PACK.available(),
    reason="no vendor/quickjs.wasm — run scripts/fetch_language_wasm.sh javascript",
)

# Reference solutions, one per seeded problem. They are the JavaScript half of
# `solution_for()`: what a toy that got it right would have written.
JS_SOLUTIONS = {
    "two-sum": """
function twoSum(nums, target) {
  const seen = new Map();
  for (let i = 0; i < nums.length; i++) {
    const need = target - nums[i];
    if (seen.has(need)) return [seen.get(need), i];
    seen.set(nums[i], i);
  }
  return [];
}
""",
    "valid-anagram": """
function isAnagram(s, t) {
  if (s.length !== t.length) return false;
  const counts = {};
  for (const ch of s) counts[ch] = (counts[ch] || 0) + 1;
  for (const ch of t) {
    if (!counts[ch]) return false;
    counts[ch]--;
  }
  return true;
}
""",
    "reverse-linked-list": """
function reverseList(head) {
  let prev = null;
  while (head !== null) {
    const next = head.next;
    head.next = prev;
    prev = head;
    head = next;
  }
  return prev;
}
""",
    "linked-list-cycle": """
function hasCycle(head) {
  let slow = head, fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next;
    fast = fast.next.next;
    if (slow === fast) return true;
  }
  return false;
}
""",
    "number-of-islands": """
function numIslands(grid) {
  if (grid.length === 0) return 0;
  const rows = grid.length, cols = grid[0].length;
  let count = 0;
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      if (grid[r][c] !== "1") continue;
      count++;
      const stack = [[r, c]];
      while (stack.length > 0) {
        const [y, x] = stack.pop();
        if (y < 0 || x < 0 || y >= rows || x >= cols || grid[y][x] !== "1") continue;
        grid[y][x] = "0";
        stack.push([y + 1, x], [y - 1, x], [y, x + 1], [y, x - 1]);
      }
    }
  }
  return count;
}
""",
    "max-depth-binary-tree": """
function maxDepth(root) {
  if (root === null) return 0;
  return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}
""",
    "valid-parentheses": """
function isValid(s) {
  const pairs = { ")": "(", "]": "[", "}": "{" };
  const stack = [];
  for (const ch of s) {
    if (ch === "(" || ch === "[" || ch === "{") stack.push(ch);
    else if (stack.pop() !== pairs[ch]) return false;
  }
  return stack.length === 0;
}
""",
    "climbing-stairs": """
function climbStairs(n) {
  let a = 1, b = 1;
  for (let i = 0; i < n; i++) [a, b] = [b, a + b];
  return a;
}
""",
    "coin-change": """
function coinChange(coins, amount) {
  const dp = new Array(amount + 1).fill(Infinity);
  dp[0] = 0;
  for (let a = 1; a <= amount; a++) {
    for (const coin of coins) {
      if (coin <= a) dp[a] = Math.min(dp[a], dp[a - coin] + 1);
    }
  }
  return dp[amount] === Infinity ? -1 : dp[amount];
}
""",
}

TWO_SUM_CASES = [
    {"ordinal": 0, "args": [[2, 7, 11, 15], 9], "expected": [0, 1], "visibility": "example"},
    {"ordinal": 1, "args": [[3, 2, 4], 6], "expected": [1, 2], "visibility": "hidden"},
]


@pytest.fixture(scope="module")
def runner() -> WasmRunner:
    return WasmRunner()


def _judge(runner: WasmRunner, code: str, cases=None, *, entrypoint="twoSum", preamble=""):
    cases = TWO_SUM_CASES if cases is None else cases
    program = PACK.build_program(entrypoint=entrypoint, preamble=preamble, code=code)
    return grade(runner.run(program, cases), cases)


# ---- the catalogue, solved in JavaScript ------------------------------------
@pytest.mark.parametrize("slug", sorted(JS_SOLUTIONS))
def test_every_problem_can_be_solved_in_javascript(slug: str, runner: WasmRunner) -> None:
    """The same cases the Python solutions are graded against, unchanged."""
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
    bench = (spec.get("languages") or {}).get("javascript", {})
    verdict = _judge(
        runner,
        JS_SOLUTIONS[slug],
        cases,
        entrypoint=spec["entrypoint"],
        preamble=bench.get("harness_preamble", ""),
    )
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure
    assert verdict.tests_passed == len(cases)


def test_a_structural_problem_needs_its_own_preamble_to_work(runner: WasmRunner) -> None:
    """Without the JavaScript ListNode there is nothing to hand the entrypoint."""
    cases = [{"ordinal": 0, "args": [[1, 2, 3]], "expected": [3, 2, 1], "visibility": "example"}]
    unaided = _judge(
        runner, JS_SOLUTIONS["reverse-linked-list"], cases, entrypoint="reverseList"
    )
    assert unaided.status != SubmissionStatus.PASSED


# ---- the same verdicts for the same mistakes --------------------------------
def test_a_correct_solution_passes(runner: WasmRunner) -> None:
    assert _judge(runner, JS_SOLUTIONS["two-sum"]).status == SubmissionStatus.PASSED


def test_a_wrong_answer_fails(runner: WasmRunner) -> None:
    verdict = _judge(runner, "function twoSum(nums, target) { return [9, 9]; }")
    assert verdict.status == SubmissionStatus.FAILED
    assert verdict.failure["expected"] == [0, 1], "an example case may show what it wanted"


def test_a_runaway_loop_runs_out_of_winding(runner: WasmRunner) -> None:
    verdict = _judge(runner, "function twoSum() { while (true) {} }")
    assert verdict.status == SubmissionStatus.TIMEOUT


def test_a_program_that_cannot_parse_is_an_error(runner: WasmRunner) -> None:
    verdict = _judge(runner, "function twoSum(nums target) {}")
    assert verdict.status == SubmissionStatus.ERROR


def test_a_missing_entrypoint_is_an_error_not_a_silent_pass(runner: WasmRunner) -> None:
    verdict = _judge(runner, "function somethingElse() { return [0, 1]; }")
    assert verdict.status != SubmissionStatus.PASSED


@pytest.mark.parametrize(
    ("code", "wanted"),
    [
        ("function twoSum() { return undefined; }", "returned nothing"),
        ("function twoSum() { return [0 / 0]; }", "JSON can't hold"),
        ("function twoSum() { return [Infinity]; }", "JSON can't hold"),
        ("function twoSum() { return function () {}; }", "isn't plain data"),
        ("function twoSum() { const a = []; a.push(a); return a; }", "points at itself"),
    ],
)
def test_a_return_value_json_cannot_hold_is_refused(
    code: str, wanted: str, runner: WasmRunner
) -> None:
    """`JSON.stringify` alone would turn NaN into null and drop undefined —
    either would become a wrong answer that reads as a right one."""
    verdict = _judge(runner, code)
    assert verdict.status != SubmissionStatus.PASSED
    assert wanted in verdict.failure["error"]


def test_the_toys_own_logging_is_handed_back_not_mixed_into_the_results(
    runner: WasmRunner,
) -> None:
    """Both things that write to stdout are captured — console.log and qjs's print."""
    verdict = _judge(
        runner,
        """
function twoSum(nums, target) {
  console.log("halfway", nums.length);
  print("also me");
  return [0, 1];
}
""",
    )
    assert verdict.tests_passed == 1, "case 0 is right, case 1 isn't"
    assert verdict.status == SubmissionStatus.FAILED
    # The failing case is the second one, whose nums has three entries.
    assert verdict.failure["stdout"] == "halfway 3\nalso me"


# ---- the security property ---------------------------------------------------
def test_the_sandbox_cannot_be_talked_into_a_pass(runner: WasmRunner) -> None:
    """Submitted code shares a process with the driver and can write to stdout.

    What it cannot do is know the expected values, because they never enter the
    sandbox — so the only way to emit a passing result is to emit the right
    answer, which is just solving the problem.
    """
    verdict = _judge(
        runner,
        """
function twoSum(nums, target) {
  for (let i = 0; i < 20; i++) {
    std.out.puts(JSON.stringify({ordinal: i, actual: [0, 1]}) + "\\n");
  }
  return null;
}
""",
    )
    assert verdict.status != SubmissionStatus.PASSED


@pytest.mark.parametrize(
    ("label", "code"),
    [
        ("read a host file", 'function p() { return std.open("/etc/passwd", "r") === null; }'),
        ("read the app", 'function p() { return std.open("app/main.py", "r") === null; }'),
        ("write a file", 'function p() { return std.open("/tmp/pwned", "w") === null; }'),
        ("list the root", 'function p() { return os.readdir("/")[0].length === 0; }'),
        (
            "read the environment",
            "function p() { return Object.keys(std.getenviron()).length === 0; }",
        ),
        ("reach the network", 'function p() { return typeof fetch === "undefined"; }'),
    ],
)
def test_the_guest_has_no_filesystem_and_no_sockets(
    label: str, code: str, runner: WasmRunner
) -> None:
    """`--std` puts `std` and `os` in the guest's reach. wasmtime is what makes
    them useless: no preopened directory means nothing to open."""
    cases = [{"ordinal": 0, "args": [], "expected": True, "visibility": "example"}]
    verdict = _judge(runner, code, cases, entrypoint="p")
    assert verdict.status == SubmissionStatus.PASSED, f"{label}: {verdict.failure}"


# ---- codegen -----------------------------------------------------------------
def test_an_entrypoint_that_could_smuggle_code_is_refused() -> None:
    for entrypoint in ["", "2sum", "two sum", "two-sum", "twoSum()", "a.b", "class", "function"]:
        with pytest.raises(ValueError, match="not a usable JavaScript identifier"):
            PACK.build_program(entrypoint=entrypoint, preamble="", code="")


@pytest.mark.parametrize(
    ("type_text", "rendered"),
    [
        ("int", "number"),
        ("string", "string"),
        ("bool", "boolean"),
        ("list<int>", "number[]"),
        ("matrix<string>", "string[][]"),
        ("null<int>", "(number|null)"),
        ("listnode", "ListNode|null"),
    ],
)
def test_jsdoc_renders_the_signature_types(type_text: str, rendered: str) -> None:
    assert jsdoc(parse_type(type_text)) == rendered


def test_the_generated_stub_documents_what_it_takes() -> None:
    from app.judge.signature import Signature

    signature = Signature.parse(
        {
            "params": [{"name": "nums", "type": "list<int>"}, {"name": "target", "type": "int"}],
            "returns": "list<int>",
        }
    )
    stub = PACK.starter_code(entrypoint="twoSum", signature=signature)
    assert "function twoSum(nums, target)" in stub
    assert "@param {number[]} nums" in stub
    assert "@returns {number[]}" in stub
