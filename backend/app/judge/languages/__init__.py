"""The language registry.

Adding a language is adding a module here and a line to `REGISTRY`. Nothing in
`grade.py` changes, no test case is rewritten, and the sandbox is the same one —
`WasmRunner` instantiates whichever interpreter the pack names.

`settings.JUDGE_LANGUAGES` is what a deployment actually offers. A pack can be
registered and not enabled (its artifact isn't fetched yet), which is why
`enabled_packs()` and `get_pack()` are different questions.
"""

from __future__ import annotations

from app.core.config import settings
from app.judge.languages.base import (
    CASES_SLOT,
    PROGRAM_SLOT,
    LanguagePack,
    ProgramSpec,
    RunnerSpec,
)
from app.judge.languages.javascript import PACK as JAVASCRIPT_PACK
from app.judge.languages.php import PACK as PHP_PACK
from app.judge.languages.python import PACK as PYTHON_PACK
from app.judge.languages.ruby import PACK as RUBY_PACK


class UnknownLanguage(ValueError):
    """Asked for a language no pack implements, or one this deployment doesn't offer."""


REGISTRY: dict[str, LanguagePack] = {
    PYTHON_PACK.slug: PYTHON_PACK,
    JAVASCRIPT_PACK.slug: JAVASCRIPT_PACK,
    RUBY_PACK.slug: RUBY_PACK,
    PHP_PACK.slug: PHP_PACK,
}

# The language a problem falls back to, and the one the workbench opens on.
DEFAULT_LANGUAGE = PYTHON_PACK.slug


def get_pack(slug: str) -> LanguagePack:
    """The pack for `slug`, if this deployment offers it."""
    pack = REGISTRY.get(slug)
    if pack is None:
        raise UnknownLanguage(f"Sprocket has never heard of {slug!r}.")
    if slug not in settings.JUDGE_LANGUAGES:
        raise UnknownLanguage(f"Sprocket hasn't set up a {pack.label} bench yet.")
    return pack


def is_enabled(slug: str) -> bool:
    return slug in REGISTRY and slug in settings.JUDGE_LANGUAGES


def enabled_packs() -> list[LanguagePack]:
    """Every offered pack, in the order `JUDGE_LANGUAGES` lists them."""
    return [REGISTRY[slug] for slug in settings.JUDGE_LANGUAGES if slug in REGISTRY]


__all__ = [
    "CASES_SLOT",
    "DEFAULT_LANGUAGE",
    "PROGRAM_SLOT",
    "REGISTRY",
    "LanguagePack",
    "ProgramSpec",
    "RunnerSpec",
    "UnknownLanguage",
    "enabled_packs",
    "get_pack",
    "is_enabled",
]
