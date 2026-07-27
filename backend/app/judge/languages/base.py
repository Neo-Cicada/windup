"""What every language has to provide, and what it hands the runner back.

A language pack owns exactly one thing: turning a toy's code into a program the
sandbox can execute. Everything downstream of that — the case payload on stdin,
the JSONL read back off stdout, the comparison against expected values — is
language-neutral and lives in `harness.py` and `grade.py`, unchanged.

That split is what keeps the security property from being re-argued per
language. Every pack's driver obeys the same contract:

    in : {"tests": [{"ordinal": n, "args": [...]}, ...]}          on stdin
    out: {"ordinal": n, "actual": ..., "stdout": "", "error": null}\\n   per case

Expected values are not in that payload and never will be, so a pass can only be
forged by emitting correct answers, which is just solving the problem.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from app.judge.signature import Signature

if TYPE_CHECKING:
    from app.judge.compile import CompileSpec

# Replaced with the assembled program when the runner builds its argv. Most
# interpreters here take the program on the command line (`-c`, `-e`), which is
# what lets the guest keep having no filesystem at all.
PROGRAM_SLOT = "__WINDUP_PROGRAM__"

# Replaced with the case payload, for a pack that sets `program_on_stdin` and so
# has no stdin left to read it from. Same payload either way — arguments only,
# never expected values — so which door it comes through changes nothing about
# what the guest can learn.
CASES_SLOT = "__WINDUP_CASES__"


@dataclass(frozen=True)
class RunnerSpec:
    """How to invoke the guest for one language."""

    language: str
    # Argv for the wasm module, with PROGRAM_SLOT standing in for the source.
    argv: tuple[str, ...]
    # The interpreter to instantiate. Resolved relative to the backend package
    # root when it isn't absolute.
    wasm_path: str
    # None means "use settings.JUDGE_FUEL". A pack whose interpreter starts up
    # far cheaper or dearer than CPython's 0.24G sets its own.
    fuel: int | None = None
    # For an interpreter with no way to take a program on argv (php-cgi), the
    # program goes on stdin instead and the cases are substituted into it at
    # CASES_SLOT. Nothing else changes.
    program_on_stdin: bool = False
    # Set for a language with no interpreter at all. The source is built to wasm
    # on the host first, and *that* module is what the sandbox instantiates —
    # same fuel, same memory limit, same absence of a filesystem.
    compile: CompileSpec | None = None


@dataclass(frozen=True)
class ProgramSpec:
    """One assembled program, and what to run it with."""

    source: str
    runner: RunnerSpec
    # Set by a pack that needs the cases *inside* the source rather than on
    # stdin — the compiled languages, which render them as typed literals so the
    # guest has no JSON to parse. The runner calls it with the case list and
    # uses what comes back as the final source.
    bind_cases: Callable[[list[dict[str, Any]]], str] | None = None

    def source_for(self, cases: list[dict[str, Any]]) -> str:
        return self.source if self.bind_cases is None else self.bind_cases(cases)


@runtime_checkable
class LanguagePack(Protocol):
    """One language's half of the judge."""

    slug: str
    label: str
    extension: str
    # Whether the workbench's Run button can execute this language locally. The
    # server does not care; it ships on the problem payload so the client knows
    # whether to offer the button.
    runs_in_browser: bool

    def wasm_path(self) -> str:
        """The interpreter this pack runs in, for the runner to preload."""
        ...

    def available(self) -> bool:
        """False when the artifact this pack needs isn't on disk yet."""
        ...

    def build_program(
        self,
        *,
        entrypoint: str,
        preamble: str,
        code: str,
        signature: Signature | None = None,
    ) -> ProgramSpec: ...

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        """The stub a toy opens the workbench to, when the problem doesn't override it."""
        ...


__all__ = ["PROGRAM_SLOT", "LanguagePack", "ProgramSpec", "RunnerSpec"]
