"""Which languages a problem offers, and what each one's workbench holds.

A problem's bench is per-language — the stub it opens to, the preamble that
defines whatever structures it needs, occasionally a different entrypoint name.
The test cases are not, and never will be: `args_json` / `expected_json` are
plain JSON compared on the host, so one set of cases grades every language.

Pure. Takes a `Problem` with its `languages` loaded and touches no database, so
the worker and the API can both ask the same question and get the same answer.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.judge.languages import (
    DEFAULT_LANGUAGE,
    LanguagePack,
    UnknownLanguage,
    get_pack,
    is_enabled,
)
from app.judge.signature import Signature, parse_signature


@dataclass(frozen=True)
class Bench:
    """One problem, one language, everything needed to build or open it."""

    pack: LanguagePack
    entrypoint: str
    preamble: str
    starter_code: str
    signature: Signature | None

    @property
    def language(self) -> str:
        return self.pack.slug


def default_language(problem) -> str:
    """The language the workbench opens on."""
    return problem.language or DEFAULT_LANGUAGE


def offered_languages(problem) -> list[str]:
    """Every language this problem can be solved in, default first.

    The default is always offered — it is the one the problem's own
    `starter_code` and `harness_preamble` were written for. Everything else has
    to be authored as a `ProblemLanguage` row and enabled in this deployment.
    """
    default = default_language(problem)
    offered = [default] if is_enabled(default) else []
    for row in problem.languages:
        if row.enabled and row.language != default and is_enabled(row.language):
            offered.append(row.language)
    return offered


def bench_for(problem, language: str | None = None) -> Bench:
    """Resolve one bench, or say why there isn't one."""
    default = default_language(problem)
    language = language or default
    pack = get_pack(language)  # raises UnknownLanguage for unknown or not-offered-here

    row = next(
        (r for r in problem.languages if r.language == language and r.enabled),
        None,
    )
    if row is None and language != default:
        raise UnknownLanguage(f"Sprocket hasn't set up a {pack.label} bench for this toy yet.")

    signature = parse_signature(problem.signature_json)
    entrypoint = (row.entrypoint if row and row.entrypoint else None) or problem.entrypoint

    # Only the default language inherits the problem's own preamble — it is
    # source code in that language, and handing Python's ListNode to the Ruby
    # pack would produce a program that cannot parse.
    if row is not None and row.harness_preamble:
        preamble = row.harness_preamble
    elif language == default:
        preamble = problem.harness_preamble
    else:
        preamble = ""

    if row is not None and row.starter_code is not None:
        starter = row.starter_code
    elif language == default and problem.starter_code:
        starter = problem.starter_code
    else:
        starter = pack.starter_code(entrypoint=entrypoint, signature=signature)

    return Bench(
        pack=pack,
        entrypoint=entrypoint,
        preamble=preamble,
        starter_code=starter,
        signature=signature,
    )


def benches_for(problem) -> list[Bench]:
    """Every offered bench, default first."""
    return [bench_for(problem, language) for language in offered_languages(problem)]


__all__ = ["Bench", "UnknownLanguage", "bench_for", "benches_for", "default_language",
           "offered_languages"]
