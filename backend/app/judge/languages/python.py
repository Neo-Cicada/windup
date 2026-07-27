"""The Python pack — the original judge, expressed as a language.

Layout of the assembled program:

    1. default `_build` / `_dump` adapters (identity)
    2. the problem's `harness_preamble`, which may override them and define
       whatever structures the problem needs (ListNode, TreeNode)
    3. the toy's own code
    4. the driver, which reads cases from stdin and writes results to stdout

Every other pack mirrors this shape in its own syntax, so a problem's preamble
is the only per-language authoring a structural problem needs.
"""

from __future__ import annotations

import keyword
from pathlib import Path

from app.core.config import settings
from app.judge.languages.base import PROGRAM_SLOT, ProgramSpec, RunnerSpec
from app.judge.signature import Signature, Type

DEFAULT_ADAPTERS = '''\
def _build(args):
    """Turn the JSON argument list into the real call arguments."""
    return args


def _dump(value):
    """Turn the return value back into something JSON can hold."""
    return value
'''

# Runs after the toy's code. Each case is reported on its own line and flushed,
# so if the fuel runs out mid-run the cases that already finished still arrive
# and the timeout can be pinned to a specific case.
#
# The entrypoint is substituted by plain replacement, not str.format — the
# driver is full of dict literals and subscripts that format() would try to
# interpret as fields.
ENTRYPOINT_SLOT = "__WINDUP_ENTRYPOINT__"

DRIVER = '''\

def __windup_main():
    import io as _io
    import json as _json
    import sys as _sys
    import traceback as _traceback

    _real_stdout = _sys.stdout
    _payload = _json.load(_sys.stdin)

    for _case in _payload["tests"]:
        _result = {"ordinal": _case["ordinal"], "actual": None, "stdout": "", "error": None}
        # The toy's own prints are captured rather than allowed onto the result
        # stream — they get handed back as debugging output instead.
        _captured = _io.StringIO()
        _sys.stdout = _captured
        try:
            _value = _dump(__WINDUP_ENTRYPOINT__(*_build(list(_case["args"]))))
            try:
                _json.dumps(_value, allow_nan=False)
            except (TypeError, ValueError):
                raise TypeError(
                    "returned something that isn't plain data: " + type(_value).__name__
                )
            _result["actual"] = _value
        except Exception:
            _lines = _traceback.format_exception_only(*_sys.exc_info()[:2])
            _result["error"] = "".join(_lines).strip()
        except BaseException:
            # RecursionError arrives as an Exception, but a bare `raise SystemExit`
            # in submitted code should not look like a clean finish.
            _result["error"] = "the toy stopped itself mid-run"
        finally:
            _sys.stdout = _real_stdout
        _result["stdout"] = _captured.getvalue()[:2000]
        _real_stdout.write(_json.dumps(_result) + "\\n")
        _real_stdout.flush()


__windup_main()
'''

ANNOTATIONS = {
    "int": "int",
    "float": "float",
    "bool": "bool",
    "string": "str",
    "char": "str",
    "void": "None",
    "listnode": "ListNode | None",
    "treenode": "TreeNode | None",
}


def annotate(type_: Type) -> str:
    """Render a signature type as a Python annotation."""
    if type_.kind == "list":
        return f"list[{annotate(type_.of)}]" if type_.of else "list"
    if type_.kind == "matrix":
        return f"list[list[{annotate(type_.of)}]]" if type_.of else "list[list]"
    if type_.kind == "null":
        return f"{annotate(type_.of)} | None" if type_.of else "None"
    return ANNOTATIONS.get(type_.kind, "object")


class PythonPack:
    slug = "python"
    label = "Python"
    extension = "py"
    runs_in_browser = True

    def wasm_path(self) -> str:
        return settings.JUDGE_WASM_PATH

    def available(self) -> bool:
        path = Path(self.wasm_path())
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / path
        return path.exists()

    def build_program(
        self,
        *,
        entrypoint: str,
        preamble: str,
        code: str,
        signature: Signature | None = None,
    ) -> ProgramSpec:
        """Assemble the full guest program for one submission."""
        # `"class".isidentifier()` is True, so the keyword check is not redundant —
        # without it a mis-seeded entrypoint produces a program that cannot compile
        # and shows up as every submission failing rather than as a config mistake.
        if not entrypoint.isidentifier() or keyword.iskeyword(entrypoint):
            raise ValueError(f"entrypoint {entrypoint!r} is not a usable Python identifier")
        source = "\n".join(
            [
                DEFAULT_ADAPTERS,
                preamble or "",
                code,
                DRIVER.replace(ENTRYPOINT_SLOT, entrypoint),
            ]
        )
        return ProgramSpec(
            source=source,
            runner=RunnerSpec(
                language=self.slug,
                argv=("python", "-I", "-c", PROGRAM_SLOT),
                wasm_path=self.wasm_path(),
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"def {entrypoint}():\n    # your turn, little toy…\n    pass\n"
        params = ", ".join(f"{p.name}: {annotate(p.type)}" for p in signature.params)
        returns = annotate(signature.returns)
        return f"def {entrypoint}({params}) -> {returns}:\n    # your turn, little toy…\n    pass\n"


PACK = PythonPack()


def build_program(
    *,
    entrypoint: str,
    preamble: str,
    code: str,
    signature: Signature | None = None,
) -> ProgramSpec:
    """Module-level shorthand, kept because it is what the judge has always called."""
    return PACK.build_program(
        entrypoint=entrypoint, preamble=preamble, code=code, signature=signature
    )


__all__ = [
    "DEFAULT_ADAPTERS",
    "DRIVER",
    "ENTRYPOINT_SLOT",
    "PACK",
    "PythonPack",
    "annotate",
    "build_program",
]
