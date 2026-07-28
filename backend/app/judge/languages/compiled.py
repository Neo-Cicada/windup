"""What C++, Rust and Go share: no interpreter, and no JSON in the guest.

The interpreted packs hand their driver a JSON payload on stdin and let the
language parse it. A statically typed language cannot do that without a variant
type and a parser — several hundred lines of correctness-critical code per
language, where a bug is a *wrong verdict* rather than an error.

So the compiled packs take the other road: the host knows the types (that is
what `signature_json` is for) and the case data is tiny — the largest problem in
the catalogue carries 346 bytes of arguments — so the arguments are rendered
straight into the source as **native literals**. The guest parses nothing, the
compiler type-checks every call, and the only serialising left is the return
value, whose type is also known.

Two consequences worth knowing:

- **`args_signature`.** The signature describes the *call*, and for most
  problems the JSON arguments match it. Where they don't — linked-list-cycle
  folds a list and an index into one `head` — the problem also declares what the
  raw JSON holds, and its preamble supplies a `_build` that turns those into the
  single call argument.
- **The toy's own prints are not captured.** WASI gives the guest no pipe and no
  filesystem to redirect stdout into, so a `printf` lands on the result stream,
  where `parse_results` discards it as noise. Nothing is graded wrongly; there
  is simply no debugging output on the way back.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.judge.compile import CompileSpec, toolchain_ready
from app.judge.languages.base import ProgramSpec, RunnerSpec
from app.judge.signature import Signature, Type

# Where each case's rendered call goes in the assembled program.
CASES_SLOT = "__WINDUP_CASES__"

BACKEND_ROOT = Path(__file__).resolve().parents[3]


def toolchain_dir() -> Path:
    directory = Path(settings.JUDGE_TOOLCHAIN_DIR)
    return directory if directory.is_absolute() else BACKEND_ROOT / directory


def dumped_type(returns: Type) -> Type:
    """What `_dump` hands back, which is what actually gets serialised.

    A structural return is dumped as a list of its values — exactly what every
    interpreted pack's `_dump` already produces for a ListNode or a TreeNode, so
    one set of expected values keeps grading every language.
    """
    if returns.kind in ("listnode", "treenode"):
        return Type("list", Type("int"))
    return returns


@dataclass(frozen=True)
class Emitted:
    """One case, rendered into the target language."""

    ordinal: int
    call: str


class CompiledPack:
    """A language that has to be built before it can be run.

    Subclasses supply the syntax: how to spell a type, how to spell a literal,
    and the program around them. Everything about *when* those are needed is
    here.
    """

    slug: str
    label: str
    extension: str
    runs_in_browser = False
    source_name: str
    # Words that are identifiers as far as Python is concerned and keywords as
    # far as the target is. Without this a mis-seeded entrypoint produces a
    # program that cannot build, which reads as every submission failing rather
    # than as the config mistake it is.
    reserved: frozenset[str] = frozenset()

    # ---- syntax, per language -----------------------------------------------
    def render_type(self, type_: Type) -> str:
        raise NotImplementedError

    def render_value(self, type_: Type, value: Any) -> str:
        raise NotImplementedError

    def assemble(self, *, entrypoint: str, preamble: str, code: str, returns: Type) -> str:
        """The whole program, with CASES_SLOT where the calls go."""
        raise NotImplementedError

    def render_case(self, *, ordinal: int, call: str) -> str:
        """One case: run the call, print one JSON result line."""
        raise NotImplementedError

    def compile_spec(self) -> CompileSpec:
        raise NotImplementedError

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        raise NotImplementedError

    # ---- the shared half ----------------------------------------------------
    def wasm_path(self) -> str:
        # Nothing to preload: every submission compiles to its own module.
        return ""

    def available(self) -> bool:
        return toolchain_ready(self.compile_spec())

    def call_for(self, *, entrypoint: str, signature: Signature, args: list[Any]) -> str:
        """The source text calling the toy's function with one case's arguments.

        `args_signature` — carried on the signature as the raw JSON shape when it
        differs from the call — is what makes a structural problem expressible:
        the literals are the raw values, and the problem's `_build` turns them
        into the single argument the entrypoint actually takes.
        """
        raw = signature.arg_params
        if len(raw) != len(args):
            raise ValueError(
                f"{self.slug}: this problem's cases carry {len(args)} arguments but its "
                f"signature describes {len(raw)}"
            )
        literals = [
            self.render_value(param.type, value)
            for param, value in zip(raw, args, strict=True)
        ]
        if signature.bridged:
            # The raw arguments are not the call arguments; the preamble bridges.
            return f"_build({', '.join(literals)})"
        return f"{entrypoint}({', '.join(literals)})"

    def build_program(
        self,
        *,
        entrypoint: str,
        preamble: str,
        code: str,
        signature: Signature | None = None,
    ) -> ProgramSpec:
        # Name first: a bad entrypoint is the same config mistake in every
        # language, and it should read the same way whether or not the problem
        # also happens to be missing its signature.
        if not entrypoint.isidentifier() or entrypoint in self.reserved:
            raise ValueError(
                f"entrypoint {entrypoint!r} is not a usable {self.label} identifier"
            )
        if signature is None:
            raise ValueError(
                f"{self.label} needs the problem's signature to know what to pass — "
                "a problem without one cannot offer it."
            )

        source = self.assemble(
            entrypoint=entrypoint,
            preamble=preamble,
            code=code,
            returns=dumped_type(signature.returns),
        )
        def bind_cases(cases: list[dict[str, Any]]) -> str:
            rendered = []
            for case in cases:
                call = self.call_for(
                    entrypoint=entrypoint, signature=signature, args=case["args"]
                )
                if signature.bridged:
                    call = f"{entrypoint}({call})"
                rendered.append(self.render_case(ordinal=case["ordinal"], call=call))
            return source.replace(CASES_SLOT, "\n".join(rendered))

        return ProgramSpec(
            source=source,
            runner=RunnerSpec(
                language=self.slug,
                argv=(),
                wasm_path="",
                compile=self.compile_spec(),
            ),
            bind_cases=bind_cases,
        )


def json_string(value: str) -> str:
    """A JSON string literal, which every language here accepts verbatim."""
    return json.dumps(value)


__all__ = ["CASES_SLOT", "CompiledPack", "Emitted", "dumped_type", "json_string", "toolchain_dir"]
