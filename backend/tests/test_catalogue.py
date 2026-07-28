"""The catalogue checks itself.

`seed_data` is content, and content has no compiler. A mistyped expected value
in a hidden case doesn't break anything at seed time — it ships, and the first
person to find out is a toy whose correct answer is marked wrong on a case it is
not allowed to see. So the suite grades the catalogue against itself:

- every problem's own reference solution is run through the real judging path
  and must pass its own cases, which is what pins the expected values down;
- every bench a problem offers must actually assemble, including rendering the
  cases as literals for the compiled packs, so an unsupported signature is a red
  test rather than a 500 on the workbench.

These are fast because they don't touch the database — the seed specs are plain
dicts, and `SubprocessRunner` borrows the host interpreter.
"""

from __future__ import annotations

import pytest

from app.db.seed_data import PROBLEMS, ZONES
from app.judge.grade import grade
from app.judge.languages import REGISTRY
from app.judge.languages.compiled import CompiledPack
from app.judge.runner import SubprocessRunner
from app.judge.signature import parse_signature
from app.models import enums
from app.models.enums import SubmissionStatus

# Imported through the module rather than by name: pytest tries to *collect*
# anything called Test* that it finds at a test module's top level.
EXAMPLE = enums.TestVisibility.EXAMPLE
HIDDEN = enums.TestVisibility.HIDDEN

ZONE_SLUGS = {zone["slug"] for zone in ZONES}
BY_SLUG = {spec["slug"]: spec for spec in PROBLEMS}
SLUGS = sorted(BY_SLUG)

# Every zone carries at least this many problems. The roadmap corner is the unit
# a toy works through, and a corner with two toys in it isn't one.
MIN_PER_ZONE = 5


def _cases(spec: dict) -> list[dict]:
    """The seed spec's tests in the shape the judge passes around."""
    return [
        {
            "ordinal": ordinal,
            "visibility": case.get("visibility", HIDDEN),
            "label": case.get("label", ""),
            "args": case["args"],
            "expected": case["expected"],
        }
        for ordinal, case in enumerate(spec["tests"])
    ]


@pytest.mark.parametrize("slug", SLUGS)
def test_reference_solution_passes_its_own_cases(slug: str) -> None:
    """The seeded solution is what a toy who got it right would have written.

    If this fails, the *catalogue* is wrong — either the solution or one of the
    expected values — regardless of which of the two the diff touched.
    """
    spec = BY_SLUG[slug]
    pack = REGISTRY[spec["language"]]
    program = pack.build_program(
        entrypoint=spec["entrypoint"],
        preamble=spec["harness_preamble"],
        code=spec["solution"],
        signature=parse_signature(spec["signature"]),
    )
    cases = _cases(spec)
    verdict = grade(
        SubprocessRunner().run(program, cases),
        cases,
        compare_mode=spec["compare_mode"],
    )
    assert verdict.status == SubmissionStatus.PASSED, verdict.failure
    assert verdict.tests_passed == len(cases)


@pytest.mark.parametrize(
    ("slug", "language"),
    [(spec["slug"], language) for spec in PROBLEMS for language in spec["languages"]],
)
def test_every_offered_bench_assembles(slug: str, language: str) -> None:
    """A bench a problem offers has to be one the pack can actually build.

    For the compiled packs this also renders every case's arguments as typed
    literals, which is the step that rejects a signature they have no literal
    for — the failure that would otherwise surface as a submission that cannot
    be judged.
    """
    spec = BY_SLUG[slug]
    bench = spec["languages"][language]
    pack = REGISTRY[language]
    signature = parse_signature(spec["signature"])

    starter = bench.get("starter_code")
    if starter is None:
        starter = pack.starter_code(entrypoint=spec["entrypoint"], signature=signature)
    assert starter.strip(), f"{slug}/{language} opens on an empty bench"

    program = pack.build_program(
        entrypoint=bench.get("entrypoint") or spec["entrypoint"],
        preamble=bench.get("harness_preamble", ""),
        code=starter,
        signature=signature,
    )
    # Only the compiled packs put the cases in the source, and they are the only
    # ones this can fail for — but asking every pack costs nothing and keeps the
    # test from encoding which is which.
    assert program.source_for(_cases(spec))


def test_slugs_are_unique() -> None:
    slugs = [spec["slug"] for spec in PROBLEMS]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    assert not duplicates, f"two problems share a slug: {duplicates}"


@pytest.mark.parametrize("slug", SLUGS)
def test_problem_belongs_to_a_real_zone(slug: str) -> None:
    assert BY_SLUG[slug]["zone"] in ZONE_SLUGS


@pytest.mark.parametrize("zone", sorted(ZONE_SLUGS))
def test_every_zone_is_worth_visiting(zone: str) -> None:
    count = sum(1 for spec in PROBLEMS if spec["zone"] == zone)
    assert count >= MIN_PER_ZONE, f"{zone} has {count} problems, wanted {MIN_PER_ZONE}"


@pytest.mark.parametrize("slug", SLUGS)
def test_problem_shows_the_toy_something(slug: str) -> None:
    """At least one visible case, or Run has nothing to execute.

    And at least one hidden one, or the problem grades on exactly what it
    already handed over.
    """
    visibilities = [
        case.get("visibility", HIDDEN) for case in BY_SLUG[slug]["tests"]
    ]
    assert EXAMPLE in visibilities, "no example case to Run"
    assert HIDDEN in visibilities, "nothing hidden to grade on"


@pytest.mark.parametrize("slug", SLUGS)
def test_help_shelf_is_stocked(slug: str) -> None:
    """All four tiers, or a chest opens onto nothing."""
    spec = BY_SLUG[slug]
    for tier in ("explainer", "hint", "approach", "solution"):
        assert spec[tier].strip(), f"{slug} has an empty {tier}"


@pytest.mark.parametrize("slug", SLUGS)
def test_a_bench_is_never_the_default_language(slug: str) -> None:
    """`bench_for` resolves the default from the problem itself, so a row for it
    would be dead weight that also shadows the problem's own preamble."""
    spec = BY_SLUG[slug]
    assert spec["language"] not in spec["languages"]


def test_compiled_packs_only_appear_where_they_can_work() -> None:
    """A compiled pack needs a signature, and cannot take a bridged `_build`.

    `CompiledPack.build_program` refuses without a signature, and its `call_for`
    can only feed a single argument through `_build` — so a structural problem
    offering one would be a bench that raises on every submission.
    """
    for spec in PROBLEMS:
        compiled = [
            language
            for language in spec["languages"]
            if isinstance(REGISTRY[language], CompiledPack)
        ]
        if not compiled:
            continue
        assert spec["signature"], f"{spec['slug']} offers {compiled} without a signature"
        assert not spec["harness_preamble"], (
            f"{spec['slug']} offers {compiled} but carries a Python preamble they "
            "cannot use"
        )
