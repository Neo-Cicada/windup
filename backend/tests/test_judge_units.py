"""The judge's pure parts, exercised directly.

`test_judging.py` drives the judge end to end. These tests go at the pieces one
at a time — the branches a normal submission never takes: a garbled stdout, a
case the guest never reached, an unordered comparison, and the sandbox refusing
to be the unsandboxed one in production.
"""

import pytest

from app.judge.grade import _matches, _why_missing, grade
from app.judge.harness import (
    CaseOutcome,
    RunResult,
    build_program,
    build_stdin,
    parse_results,
)
from app.judge.runner import SubprocessRunner, WasmRunner, get_runner
from app.models import Submission
from app.models.enums import SubmissionStatus
from app.services.submissions import confetti_for, sprocket_line

CASES = [
    {"ordinal": 0, "args": [[1, 2], 3], "expected": [0, 1], "visibility": "example"},
    {"ordinal": 1, "args": [[3, 3], 6], "expected": [0, 1], "visibility": "hidden"},
]


def _reported(ordinal: int, actual: object = None, error: str | None = None) -> CaseOutcome:
    return CaseOutcome(ordinal=ordinal, actual=actual, error=error, reported=True)


# ---- harness: assembling the program ----------------------------------------
def test_build_program_refuses_a_non_identifier_entrypoint() -> None:
    """The entrypoint is interpolated into the driver's source, so it is checked."""
    with pytest.raises(ValueError, match="not a usable Python identifier"):
        build_program(entrypoint="twoSum(); import os", preamble="", code="")


@pytest.mark.parametrize("entrypoint", ["", "2sum", "two sum", "two-sum", "twoSum()", "a.b"])
def test_build_program_rejects_anything_that_could_smuggle_code(entrypoint: str) -> None:
    with pytest.raises(ValueError):
        build_program(entrypoint=entrypoint, preamble="", code="pass")


def test_build_program_layers_preamble_code_and_driver_in_order() -> None:
    program = build_program(
        entrypoint="solve", preamble="# PREAMBLE HERE", code="# TOY CODE HERE"
    )
    assert program.index("def _build") < program.index("# PREAMBLE HERE")
    assert program.index("# PREAMBLE HERE") < program.index("# TOY CODE HERE")
    assert program.index("# TOY CODE HERE") < program.index("__windup_main")
    assert "solve(*_build(" in program
    assert "__WINDUP_ENTRYPOINT__" not in program


def test_build_stdin_carries_arguments_and_never_expected_values() -> None:
    """The security property, at the one place it could leak."""
    payload = build_stdin(CASES)
    assert '"args"' in payload
    assert "expected" not in payload
    assert "visibility" not in payload


# ---- harness: reading the guest's stdout back --------------------------------
def test_parse_results_keeps_what_arrived_before_a_truncated_line() -> None:
    """A half-written final line is what a fuel trap mid-write looks like."""
    outcomes = parse_results('{"ordinal": 0, "actual": [0, 1]}\n{"ordinal": 1, "actu')
    assert list(outcomes) == [0]
    assert outcomes[0].actual == [0, 1]


def test_parse_results_ignores_noise_the_toy_printed_to_fd_one() -> None:
    outcomes = parse_results(
        "hello from the toy\n"
        "{not json at all}\n"
        '{"ordinal": 0, "actual": 7, "stdout": "debug", "error": null}\n'
        "[1, 2, 3]\n"
        '{"no ordinal": true}\n'
        '{"ordinal": "one", "actual": 1}\n'
    )
    assert list(outcomes) == [0]
    assert outcomes[0].actual == 7
    assert outcomes[0].stdout == "debug"
    assert outcomes[0].reported is True


def test_parse_results_of_nothing_at_all_is_empty() -> None:
    assert parse_results("") == {}
    assert parse_results("\n \n") == {}


def test_parse_results_tolerates_indented_and_interleaved_lines() -> None:
    outcomes = parse_results(
        '  {"ordinal": 1, "actual": "b"}  \nchatter\n{"ordinal": 0, "actual": "a"}\n'
    )
    assert sorted(outcomes) == [0, 1]
    assert outcomes[1].actual == "b"


def test_parse_results_defaults_a_missing_stdout_to_empty_string() -> None:
    """FailureOut.stdout is not Optional, so None must not survive the parse."""
    outcomes = parse_results('{"ordinal": 0, "actual": 1, "stdout": null}')
    assert outcomes[0].stdout == ""


# ---- grade: comparison ------------------------------------------------------
def test_matches_exact_is_order_sensitive() -> None:
    assert _matches([1, 2], [1, 2], "exact") is True
    assert _matches([2, 1], [1, 2], "exact") is False


def test_matches_unordered_ignores_order() -> None:
    assert _matches([2, 1], [1, 2], "unordered") is True
    assert _matches([[2], [1]], [[1], [2]], "unordered") is True
    assert _matches([3, 1], [1, 2], "unordered") is False


def test_matches_unordered_falls_back_to_equality_when_unsortable() -> None:
    """`sorted(None)` raises; a scalar answer still has to be right."""
    assert _matches(None, [1, 2], "unordered") is False
    assert _matches(5, 5, "unordered") is True
    assert _matches(5, 6, "unordered") is False


def test_grade_honours_unordered_compare_mode() -> None:
    cases = [{"ordinal": 0, "args": [[1, 2]], "expected": [1, 2], "visibility": "example"}]
    run = RunResult(outcomes={0: _reported(0, [2, 1])})
    assert grade(run, cases).status == SubmissionStatus.FAILED
    assert grade(run, cases, compare_mode="unordered").status == SubmissionStatus.PASSED


def test_true_does_not_satisfy_an_expected_one() -> None:
    """Python says True == 1. A problem asking for a count must not agree."""
    assert _matches(True, 1, "exact") is False
    assert _matches(1, True, "exact") is False
    assert _matches(False, 0, "exact") is False
    assert _matches(True, True, "exact") is True
    assert _matches(0, 0, "exact") is True


def test_a_boolean_answer_to_a_counting_problem_fails_grading() -> None:
    cases = [{"ordinal": 0, "args": [[1]], "expected": 1, "visibility": "example"}]
    verdict = grade(RunResult(outcomes={0: _reported(0, True)}), cases)
    assert verdict.status == SubmissionStatus.FAILED
    assert verdict.tests_passed == 0


# ---- grade: cases the guest never reported ----------------------------------
def test_an_unreported_case_is_a_failure_not_a_skip() -> None:
    """Half a batch is not a pass — this is how a crash mid-run is accounted for."""
    run = RunResult(outcomes={0: _reported(0, [0, 1])})
    verdict = grade(run, CASES)
    assert verdict.status == SubmissionStatus.FAILED
    assert verdict.tests_passed == 1
    assert verdict.tests_total == 2
    assert verdict.failure["ordinal"] == 1
    assert verdict.failure["actual"] is None
    assert verdict.failure["error"] == "the toy never reported on this case"


def test_an_unreported_case_never_leaks_a_hidden_expected_value() -> None:
    verdict = grade(RunResult(), CASES)
    assert verdict.tests_passed == 0
    assert verdict.failure["ordinal"] == 0
    assert "expected" in verdict.failure, "an example case may show what it wanted"
    later = grade(RunResult(outcomes={0: _reported(0, [0, 1])}), CASES)
    assert "expected" not in later.failure, "a hidden case must not"


def test_only_the_first_failure_is_reported() -> None:
    verdict = grade(RunResult(), CASES)
    assert verdict.failure["ordinal"] == 0


def test_a_case_that_raised_reports_the_exception_not_a_mismatch() -> None:
    run = RunResult(outcomes={0: _reported(0, error="ValueError: nope")})
    verdict = grade(run, CASES)
    assert verdict.failure["error"] == "ValueError: nope"


def test_a_fatal_run_with_no_passing_case_is_an_error_not_a_failure() -> None:
    run = RunResult(fatal="exited with status 1", stderr="SyntaxError: invalid syntax")
    verdict = grade(run, CASES)
    assert verdict.status == SubmissionStatus.ERROR
    assert verdict.tests_passed == 0


def test_a_timeout_outranks_everything_else() -> None:
    run = RunResult(outcomes={0: _reported(0, [0, 1]), 1: _reported(1, [0, 1])}, timed_out=True)
    verdict = grade(run, CASES)
    assert verdict.tests_passed == 2
    assert verdict.status == SubmissionStatus.TIMEOUT, "a full-marks timeout still times out"


def test_a_graded_problem_with_no_cases_cannot_pass_by_vacuous_truth() -> None:
    """grade() of an empty case list must not report success."""
    verdict = grade(RunResult(), [])
    assert verdict.status != SubmissionStatus.PASSED
    assert verdict.tests_total == 0


def test_labels_fall_back_to_a_one_based_case_number() -> None:
    cases = [{"ordinal": 3, "args": [], "expected": 1, "visibility": "hidden"}]
    verdict = grade(RunResult(outcomes={3: _reported(3, 2)}), cases)
    assert verdict.failure["label"] == "case 4"
    assert verdict.failure["hidden"] is True


@pytest.mark.parametrize(
    ("run", "expected"),
    [
        (RunResult(timed_out=True), "ran out of winding before this case finished"),
        (RunResult(fatal="exited with status 1"), "exited with status 1"),
        (RunResult(stderr="Traceback\nSyntaxError: bad"), "SyntaxError: bad"),
        (RunResult(), "the toy never reported on this case"),
    ],
)
def test_why_missing_explains_each_way_a_case_can_go_unreported(
    run: RunResult, expected: str
) -> None:
    assert _why_missing(run) == expected


def test_why_missing_truncates_a_giant_stderr_line() -> None:
    assert len(_why_missing(RunResult(stderr="x" * 5000))) == 400


# ---- runners ----------------------------------------------------------------
@pytest.mark.parametrize("env", ["production", "staging"])
def test_subprocess_runner_refuses_to_exist_outside_development(
    env: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """It does not sandbox; being selected in production must be loud, not quiet."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENV", env)
    with pytest.raises(RuntimeError, match="does not sandbox"):
        SubprocessRunner()

    monkeypatch.setattr(settings, "JUDGE_RUNNER", "subprocess")
    with pytest.raises(RuntimeError, match="does not sandbox"):
        get_runner()


def test_subprocess_runner_constructs_in_development(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "ENV", "development")
    monkeypatch.setattr(settings, "JUDGE_RUNNER", "subprocess")
    assert isinstance(get_runner(), SubprocessRunner)


def test_an_unknown_runner_name_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_RUNNER", "docker")
    with pytest.raises(ValueError, match="Unknown JUDGE_RUNNER"):
        get_runner()


def test_the_wasm_runner_says_how_to_fetch_a_missing_build() -> None:
    with pytest.raises(FileNotFoundError, match="fetch_python_wasm"):
        WasmRunner("vendor/definitely-not-here.wasm")


def test_get_runner_asks_for_wasm_by_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """The default runner is the sandboxed one, and it is not silently skipped."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "JUDGE_RUNNER", "wasm")
    monkeypatch.setattr(settings, "JUDGE_WASM_PATH", "vendor/definitely-not-here.wasm")
    with pytest.raises(FileNotFoundError):
        get_runner()


@pytest.mark.parametrize(
    ("value", "expected"),
    [(None, ""), (b"partial\n", "partial\n"), ("text", "text"), (b"\xff", "�")],
)
def test_a_timed_out_run_still_yields_readable_output(value: object, expected: str) -> None:
    """TimeoutExpired hands back bytes or None depending on the platform."""
    from app.judge.runner import _as_text

    assert _as_text(value) == expected


def test_the_subprocess_runner_hands_back_the_toys_own_prints() -> None:
    """A toy's debugging prints are captured, not mixed into the result stream."""
    program = build_program(
        entrypoint="solve",
        preamble="",
        code="def solve(n):\n    print('halfway', n)\n    return n + 1",
    )
    run = SubprocessRunner().run(program, [{"ordinal": 0, "args": [1]}])
    assert run.outcomes[0].actual == 2
    assert "halfway 1" in run.outcomes[0].stdout
    assert run.fatal is None


def test_the_subprocess_runner_reports_a_program_that_cannot_compile() -> None:
    run = SubprocessRunner().run(
        build_program(entrypoint="solve", preamble="", code="def solve(n)\n    return"),
        [{"ordinal": 0, "args": [1]}],
    )
    assert run.outcomes == {}
    assert run.fatal is not None
    assert "SyntaxError" in run.stderr


def test_a_return_value_json_cannot_hold_is_an_error_not_a_pass() -> None:
    """`_dump` is the problem's job; an object that survives it is still refused."""
    program = build_program(
        entrypoint="solve", preamble="", code="def solve(n):\n    return object()"
    )
    run = SubprocessRunner().run(program, [{"ordinal": 0, "args": [1]}])
    assert run.outcomes[0].error is not None
    assert "plain data" in run.outcomes[0].error


def test_code_that_exits_the_interpreter_does_not_look_like_a_clean_finish() -> None:
    program = build_program(
        entrypoint="solve", preamble="", code="def solve(n):\n    raise SystemExit(0)"
    )
    run = SubprocessRunner().run(program, [{"ordinal": 0, "args": [1]}])
    cases = [{"ordinal": 0, "args": [1], "expected": 2, "visibility": "example"}]
    assert grade(run, cases).status != SubmissionStatus.PASSED


# ---- Sprocket's voice, for every verdict ------------------------------------
def _submission(status: SubmissionStatus, **kwargs: object) -> Submission:
    """An unpersisted submission — sprocket_line and confetti_for touch no DB."""
    fields = {"tests_passed": 0, "tests_total": 7, "unaided": True, **kwargs}
    return Submission(status=status, **fields)


@pytest.mark.parametrize("status", list(SubmissionStatus))
def test_sprocket_always_says_something(status: SubmissionStatus) -> None:
    line = sprocket_line(_submission(status), already_solved=False, leveled_up=False)
    assert line and line.strip() == line


@pytest.mark.parametrize(
    "status",
    [
        SubmissionStatus.PENDING,
        SubmissionStatus.RUNNING,
        SubmissionStatus.FAILED,
        SubmissionStatus.ERROR,
        SubmissionStatus.TIMEOUT,
    ],
)
def test_a_verdict_short_of_passed_never_reads_as_a_solve(status: SubmissionStatus) -> None:
    line = sprocket_line(
        _submission(status, tests_passed=7, tests_total=7),
        already_solved=False,
        leveled_up=True,
        level=9,
        xp_award=100,
    )
    assert "Solved" not in line
    assert "LEVEL UP" not in line
    assert confetti_for(_submission(status), already_solved=False, leveled_up=True) == 0


def test_a_timeout_points_at_the_loop() -> None:
    line = sprocket_line(
        _submission(SubmissionStatus.TIMEOUT), already_solved=False, leveled_up=False
    )
    assert "loop that never ends" in line


def test_an_error_points_at_the_code_not_the_answer() -> None:
    line = sprocket_line(
        _submission(SubmissionStatus.ERROR), already_solved=False, leveled_up=False
    )
    assert "compiles" in line


def test_partial_credit_is_counted_out_loud() -> None:
    line = sprocket_line(
        _submission(SubmissionStatus.FAILED, tests_passed=5, tests_total=7),
        already_solved=False,
        leveled_up=False,
    )
    assert "5 of 7" in line


def test_zero_passing_cases_gets_the_shorter_nudge() -> None:
    line = sprocket_line(
        _submission(SubmissionStatus.FAILED), already_solved=False, leveled_up=False
    )
    assert "of 7" not in line
    assert "try again" in line


def test_a_level_up_outranks_the_unaided_bonus_line() -> None:
    line = sprocket_line(
        _submission(SubmissionStatus.PASSED),
        already_solved=False,
        leveled_up=True,
        level=3,
        xp_award=100,
    )
    assert "LEVEL UP" in line
    assert confetti_for(_submission(SubmissionStatus.PASSED), already_solved=False,
                        leveled_up=True) == 80


def test_an_unaided_pass_says_so() -> None:
    passed = _submission(SubmissionStatus.PASSED, unaided=True)
    assert "UNAIDED" in sprocket_line(passed, already_solved=False, leveled_up=False)
    assert confetti_for(passed, already_solved=False, leveled_up=False) == 34


def test_an_aided_pass_quotes_the_charge_it_paid() -> None:
    aided = _submission(SubmissionStatus.PASSED, unaided=False)
    line = sprocket_line(aided, already_solved=False, leveled_up=False, xp_award=50)
    assert "+50 charge" in line


def test_a_practice_run_on_a_solved_toy_pays_no_confetti_worth_mentioning() -> None:
    passed = _submission(SubmissionStatus.PASSED)
    line = sprocket_line(passed, already_solved=True, leveled_up=False)
    assert "no extra charge" in line
    assert confetti_for(passed, already_solved=True, leveled_up=False) == 12
