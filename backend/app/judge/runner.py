"""Sandboxes that execute a submitted program.

Two implementations behind one protocol:

- `WasmRunner` — an interpreter compiled to WASI, executed by wasmtime. The
  isolation comes from the runtime rather than from anything we write: fuel
  metering caps CPU (an infinite loop traps in about a second), a store memory
  limit caps allocation, and because no directory is ever preopened the guest
  has no filesystem and no sockets at all. ~36ms per run once the module is
  compiled. Which interpreter it instantiates comes from the program's
  `RunnerSpec`, so every language shares this one sandbox.
- `SubprocessRunner` — plain CPython with rlimits. Weaker isolation, no vendored
  artifact required; the fallback for environments without python.wasm, and
  Python-only by nature.

Both are stateless per call, so a worker can hold one and reuse it.
"""

from __future__ import annotations

import os
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Protocol

from app.core.config import settings
from app.judge.harness import RunResult, build_stdin, parse_results
from app.judge.languages import PROGRAM_SLOT, ProgramSpec, enabled_packs

# Everything relative resolves against the backend package root, so a worker
# started from anywhere finds the same artifacts.
BACKEND_ROOT = Path(__file__).resolve().parents[2]


def resolve_artifact(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else BACKEND_ROOT / candidate


class Runner(Protocol):
    def run(self, spec: ProgramSpec, cases: list[dict[str, Any]]) -> RunResult: ...


# ---- wasm -------------------------------------------------------------------
class WasmRunner:
    """Executes the program inside an interpreter-on-WASI under wasmtime."""

    def __init__(self, wasm_path: str | Path | None = None) -> None:
        import wasmtime

        self._wasmtime = wasmtime
        # An override applies to Python, which is what this argument has always
        # meant and what the tests construct it with.
        self._python_override = str(wasm_path) if wasm_path is not None else None

        config = wasmtime.Config()
        config.consume_fuel = True
        self._engine = wasmtime.Engine(config)
        # Compiling a module costs ~1s, so it is paid once per language per
        # worker rather than once per submission.
        self._modules: dict[str, Any] = {}
        # Every offered language is compiled up front. A worker missing an
        # artifact should say which one at startup, with the command to fetch
        # it — not judge Python happily for an hour and then fail the first
        # JavaScript submission it is handed.
        self._module_for(self._python_override or settings.JUDGE_WASM_PATH, "python")
        for pack in enabled_packs():
            if pack.slug != "python":
                self._module_for(pack.wasm_path(), pack.slug)

    def _module_for(self, wasm_path: str, language: str) -> Any:
        cached = self._modules.get(wasm_path)
        if cached is not None:
            return cached

        path = resolve_artifact(wasm_path)
        if not path.exists():
            fetch = (
                "`./scripts/fetch_python_wasm.sh`, or set JUDGE_RUNNER=subprocess"
                if language == "python"
                else f"`./scripts/fetch_language_wasm.sh {language}`"
            )
            raise FileNotFoundError(
                f"No WASI build for {language} at {path}. Fetch it with {fetch}."
            )

        module = self._wasmtime.Module(self._engine, path.read_bytes())
        self._modules[wasm_path] = module
        return module

    def run(self, spec: ProgramSpec, cases: list[dict[str, Any]]) -> RunResult:
        wasmtime = self._wasmtime
        language = spec.runner.language
        wasm_path = (
            self._python_override
            if language == "python" and self._python_override is not None
            else spec.runner.wasm_path
        )
        module = self._module_for(wasm_path, language)

        store = wasmtime.Store(self._engine)
        store.set_fuel(spec.runner.fuel if spec.runner.fuel is not None else settings.JUDGE_FUEL)
        store.set_limits(memory_size=settings.JUDGE_MEMORY_MB * 1024 * 1024)

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            stdin_f, stdout_f, stderr_f = tmp / "in", tmp / "out", tmp / "err"
            stdin_f.write_text(build_stdin(cases))
            stdout_f.touch()
            stderr_f.touch()

            wasi = wasmtime.WasiConfig()
            # The program travels on argv, which is why no language here needs a
            # writable directory to be handed a file.
            wasi.argv = [arg.replace(PROGRAM_SLOT, spec.source) for arg in spec.runner.argv]
            wasi.stdin_file = str(stdin_f)
            wasi.stdout_file = str(stdout_f)
            wasi.stderr_file = str(stderr_f)
            # Deliberately no preopen_dir(): the guest gets no filesystem.
            store.set_wasi(wasi)

            linker = wasmtime.Linker(self._engine)
            linker.define_wasi()

            timed_out = False
            fatal: str | None = None
            started = time.monotonic()
            try:
                instance = linker.instantiate(store, module)
                instance.exports(store)["_start"](store)
            except wasmtime.ExitTrap as exit_trap:
                if exit_trap.code != 0:
                    fatal = f"exited with status {exit_trap.code}"
            except wasmtime.Trap as trap:
                # Fuel exhaustion is the interesting one; everything else is a
                # genuine crash inside the guest.
                if store.get_fuel() == 0:
                    timed_out = True
                else:
                    fatal = str(trap).splitlines()[0]
            runtime_ms = int((time.monotonic() - started) * 1000)

            return RunResult(
                outcomes=parse_results(stdout_f.read_text(errors="replace")),
                timed_out=timed_out,
                runtime_ms=runtime_ms,
                stderr=stderr_f.read_text(errors="replace")[-4000:],
                fatal=fatal,
            )


# ---- subprocess -------------------------------------------------------------
def _drop_privileges() -> None:
    """Applied in the child between fork and exec.

    Each limit is applied best-effort — they behave differently across platforms
    (RLIMIT_AS is a no-op on some macOS builds) and a limit we cannot set is not
    a reason to refuse to run. The CPU limit is the one that matters, and it is
    portable.
    """
    _limit(resource.RLIMIT_CPU, settings.JUDGE_TIMEOUT_SECONDS)
    _limit(resource.RLIMIT_AS, settings.JUDGE_MEMORY_MB * 1024 * 1024)
    _limit(resource.RLIMIT_FSIZE, 0)  # no writing anything, anywhere
    _limit(resource.RLIMIT_NPROC, 0)  # no forking
    try:
        os.setsid()  # detach, so a stray child can't reach the worker's terminal
    except OSError:
        pass


def _limit(what: int, value: int) -> None:
    try:
        resource.setrlimit(what, (value, value))
    except (ValueError, OSError, AttributeError):  # pragma: no cover - platform dependent
        pass


class SubprocessRunner:
    """Plain CPython with rlimits. **Development only, and Python only.**

    The rlimits cap CPU, memory and file *writes*, and that is all they do. This
    runner does not sandbox: submitted code can read the host filesystem and
    open sockets, both verified. It exists so the judge is runnable without the
    20MB wasm artifact, not because it is safe.

    Like `Settings` refusing to boot outside development with the committed
    SECRET_KEY, this refuses to be selected outside development — silently
    executing untrusted code unsandboxed in production is not a thing to
    discover later.
    """

    def __init__(self) -> None:
        if settings.ENV != "development":
            raise RuntimeError(
                f"JUDGE_RUNNER='subprocess' does not sandbox submitted code and cannot be "
                f"used when ENV={settings.ENV!r}. Fetch the CPython-WASI build with "
                "./scripts/fetch_python_wasm.sh and set JUDGE_RUNNER=wasm."
            )

    def run(self, spec: ProgramSpec, cases: list[dict[str, Any]]) -> RunResult:
        if spec.runner.language != "python":
            # There is no host interpreter to reach for here, and quietly
            # running someone's Ruby through CPython would be a baffling
            # verdict. The wasm runner is the one that speaks every language.
            raise RuntimeError(
                f"JUDGE_RUNNER='subprocess' only runs Python; {spec.runner.language} needs "
                "the wasm runner. Fetch its build and set JUDGE_RUNNER=wasm."
            )

        started = time.monotonic()
        with tempfile.TemporaryDirectory() as td:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-S", "-c", spec.source],
                    input=build_stdin(cases),
                    capture_output=True,
                    text=True,
                    timeout=settings.JUDGE_TIMEOUT_SECONDS,
                    cwd=td,
                    env={"PATH": "", "HOME": td, "PYTHONHASHSEED": "0"},
                    preexec_fn=_drop_privileges,
                )
            except subprocess.TimeoutExpired as expired:
                return RunResult(
                    outcomes=parse_results(_as_text(expired.stdout)),
                    timed_out=True,
                    runtime_ms=int((time.monotonic() - started) * 1000),
                    stderr=_as_text(expired.stderr)[-4000:],
                )

        fatal = None
        if proc.returncode != 0:
            # A CPU rlimit kill reads as a signal, not a clean non-zero exit.
            if proc.returncode in (-9, -24, -6):
                return RunResult(
                    outcomes=parse_results(proc.stdout),
                    timed_out=True,
                    runtime_ms=int((time.monotonic() - started) * 1000),
                    stderr=proc.stderr[-4000:],
                )
            fatal = f"exited with status {proc.returncode}"

        return RunResult(
            outcomes=parse_results(proc.stdout),
            runtime_ms=int((time.monotonic() - started) * 1000),
            stderr=proc.stderr[-4000:],
            fatal=fatal,
        )


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def get_runner() -> Runner:
    """The runner named by JUDGE_RUNNER."""
    if settings.JUDGE_RUNNER == "subprocess":
        return SubprocessRunner()
    if settings.JUDGE_RUNNER == "wasm":
        return WasmRunner()
    raise ValueError(
        f"Unknown JUDGE_RUNNER {settings.JUDGE_RUNNER!r} — use 'wasm' or 'subprocess'."
    )


__all__ = [
    "ProgramSpec",
    "RunResult",
    "Runner",
    "SubprocessRunner",
    "WasmRunner",
    "get_runner",
    "resolve_artifact",
]
