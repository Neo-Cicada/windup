"""Compiling a submission to wasm, on the host, before the sandbox runs it.

C++, Rust and Go have no interpreter to hand a program to — they have to be
built first. All three target `wasm32-wasip1` natively, so the *output* runs in
the same wasmtime sandbox as everything else: one sandbox for every language,
with the same fuel cap, the same memory limit and the same absence of a
filesystem.

The compiler itself is the one place untrusted input touches the host, so it
gets the same treatment `SubprocessRunner` gives CPython — rlimits, a scratch
directory, no network, and a wall clock of its own — plus a cap on how large an
artifact it may produce.

A compile failure is a first-class verdict, not a crash: the toy gets the
compiler's own diagnostics, which is the most useful thing anyone could hand it.
"""

from __future__ import annotations

import os
import resource
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings

# Substituted into a CompileSpec's argv when the compiler is invoked.
SOURCE_SLOT = "__WINDUP_SOURCE__"
OUTPUT_SLOT = "__WINDUP_OUTPUT__"


@dataclass(frozen=True)
class CompileSpec:
    """How to turn one language's source into a wasm module."""

    language: str
    # What the source file must be called. Some toolchains care (Go does).
    source_name: str
    argv: tuple[str, ...]
    # Absolute path to the binary that must exist for this language to be
    # offered at all. Reported as "not offered" rather than crashing a worker.
    toolchain: Path
    # Anything the toolchain needs beyond a bare environment — TinyGo wants the
    # Go toolchain and wasm-opt on PATH.
    env: dict[str, str] = field(default_factory=dict)
    # Some toolchains insist on a writable home or cache.
    needs_home: bool = True


@dataclass
class CompileResult:
    wasm: bytes | None
    # The compiler's own diagnostics, trimmed. Shown to the toy on failure.
    diagnostics: str = ""
    ms: int = 0


def _limits() -> None:
    """Applied in the child between fork and exec. Best-effort, like the runner's."""
    for what, value in (
        (resource.RLIMIT_CPU, settings.JUDGE_COMPILE_TIMEOUT_SECONDS),
        (resource.RLIMIT_FSIZE, settings.JUDGE_COMPILE_MAX_OUTPUT_MB * 1024 * 1024),
    ):
        try:
            resource.setrlimit(what, (value, value))
        except (ValueError, OSError, AttributeError):  # pragma: no cover - platform dependent
            pass
    try:
        os.setsid()
    except OSError:
        pass


def toolchain_ready(spec: CompileSpec) -> bool:
    """Whether this language can be built on this host at all."""
    return spec.toolchain.exists()


def compile_to_wasm(spec: CompileSpec, source: str) -> CompileResult:
    """Build `source` into a wasm module, or explain why it wouldn't build."""
    started = time.monotonic()

    with tempfile.TemporaryDirectory() as td:
        work = Path(td)
        (work / spec.source_name).write_text(source)
        output = work / "out.wasm"

        argv = [
            arg.replace(SOURCE_SLOT, spec.source_name).replace(OUTPUT_SLOT, str(output))
            for arg in spec.argv
        ]
        env = {"PATH": os.environ.get("PATH", ""), **spec.env}
        if spec.needs_home:
            env["HOME"] = str(work)
            env["TMPDIR"] = str(work)

        try:
            proc = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=settings.JUDGE_COMPILE_TIMEOUT_SECONDS,
                cwd=work,
                env=env,
                preexec_fn=_limits,
            )
        except subprocess.TimeoutExpired:
            return CompileResult(
                wasm=None,
                diagnostics="The compiler took too long over this one.",
                ms=int((time.monotonic() - started) * 1000),
            )
        except OSError as err:  # pragma: no cover - a missing toolchain is checked earlier
            return CompileResult(
                wasm=None,
                diagnostics=f"The {spec.language} toolchain wouldn't start: {err}",
                ms=int((time.monotonic() - started) * 1000),
            )

        ms = int((time.monotonic() - started) * 1000)
        # Warnings on a successful build are not worth showing; a failure's
        # diagnostics are the whole point.
        if proc.returncode != 0 or not output.exists():
            return CompileResult(wasm=None, diagnostics=_trim(proc.stderr or proc.stdout), ms=ms)

        size_mb = output.stat().st_size / (1024 * 1024)
        if size_mb > settings.JUDGE_COMPILE_MAX_OUTPUT_MB:
            return CompileResult(
                wasm=None,
                diagnostics=f"That built to {size_mb:.0f}MB, which is more than the rig will run.",
                ms=ms,
            )
        return CompileResult(wasm=output.read_bytes(), ms=ms)


def _trim(diagnostics: str) -> str:
    """Enough of the compiler's complaint to act on, and no more.

    The first errors are the ones worth reading — everything after tends to be
    the same mistake echoing through the rest of the file.
    """
    lines = [line for line in diagnostics.splitlines() if line.strip()]
    return "\n".join(lines[:40])[:4000]


def which(name: str) -> Path | None:
    """A toolchain on PATH, for a host that installed one system-wide."""
    found = shutil.which(name)
    return Path(found) if found else None


__all__ = [
    "OUTPUT_SLOT",
    "SOURCE_SLOT",
    "CompileResult",
    "CompileSpec",
    "compile_to_wasm",
    "toolchain_ready",
    "which",
]
