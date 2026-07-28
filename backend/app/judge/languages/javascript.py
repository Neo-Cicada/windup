"""The JavaScript pack — QuickJS-on-WASI, in the same sandbox as everything else.

Assembled exactly like the Python one:

    1. default `_build` / `_dump` adapters (identity)
    2. the problem's `harness_preamble` for this language
    3. the toy's own code
    4. the driver, which reads cases from stdin and writes results to stdout

The wire format is the Python driver's, line for line, so `grade.py` cannot tell
which language produced a result — which is the point.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.judge.languages.base import PROGRAM_SLOT, ProgramSpec, RunnerSpec
from app.judge.signature import Signature, Type

DEFAULT_ADAPTERS = """\
function _build(args) {
  // Turn the JSON argument list into the real call arguments.
  return args;
}

function _dump(value) {
  // Turn the return value back into something JSON can hold.
  return value;
}
"""

ENTRYPOINT_SLOT = "__WINDUP_ENTRYPOINT__"

# Runs after the toy's code. Each case is reported on its own line and flushed,
# so if the fuel runs out mid-run the cases that already finished still arrive.
#
# Two differences from the Python driver, both forced by the language and
# neither visible downstream:
#
# - `JSON.stringify` is far too forgiving to be the plain-data check on its own.
#   It turns NaN into null and drops undefined entirely, either of which would
#   quietly become a wrong answer that reads as a right one, so `__windup_plain`
#   walks the value itself — the moral equivalent of `allow_nan=False`.
# - stdout cannot be swapped out the way `sys.stdout` can, so the two things
#   that write to it (`console.log` and qjs's `print`) are replaced for the
#   duration of each case. `std.out` is untouched, which is what the driver
#   itself reports on.
DRIVER = """

function __windup_plain(value, seen) {
  if (value === null) return value;
  var kind = typeof value;
  if (kind === "number") {
    if (!isFinite(value)) throw new TypeError("returned a number JSON can't hold: " + value);
    return value;
  }
  if (kind === "string" || kind === "boolean") return value;
  if (kind === "undefined") throw new TypeError("returned nothing at all");
  if (kind !== "object") {
    throw new TypeError("returned something that isn't plain data: " + kind);
  }
  if (seen.indexOf(value) !== -1) throw new TypeError("returned something that points at itself");
  seen.push(value);
  var out;
  if (Array.isArray(value)) {
    out = [];
    for (var i = 0; i < value.length; i++) out.push(__windup_plain(value[i], seen));
  } else {
    out = {};
    for (var k in value) {
      if (Object.prototype.hasOwnProperty.call(value, k)) {
        out[k] = __windup_plain(value[k], seen);
      }
    }
  }
  seen.pop();
  return out;
}

function __windup_describe(err) {
  if (err instanceof Error) return (err.name + ": " + err.message).trim();
  return String(err);
}

(function __windup_main() {
  var payload = JSON.parse(std.in.readAsString());
  var tests = payload.tests;

  for (var i = 0; i < tests.length; i++) {
    var testCase = tests[i];
    var row = { ordinal: testCase.ordinal, actual: null, stdout: "", error: null };

    // The toy's own logging is captured rather than allowed onto the result
    // stream — it gets handed back as debugging output instead.
    var captured = [];
    var realLog = console.log;
    var realPrint = globalThis.print;
    var capture = function () {
      var parts = [];
      for (var n = 0; n < arguments.length; n++) parts.push(String(arguments[n]));
      captured.push(parts.join(" "));
    };
    console.log = capture;
    globalThis.print = capture;

    try {
      var value = _dump(__WINDUP_ENTRYPOINT__.apply(null, _build(testCase.args.slice())));
      row.actual = __windup_plain(value, []);
    } catch (err) {
      row.error = __windup_describe(err);
    } finally {
      console.log = realLog;
      globalThis.print = realPrint;
    }

    row.stdout = captured.join("\\n").slice(0, 2000);
    std.out.puts(JSON.stringify(row) + "\\n");
    std.out.flush();
  }
})();
"""

IDENTIFIER = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

# Enough to catch a mis-seeded entrypoint. A name that is merely unusual still
# produces a program that parses; a keyword produces one that doesn't, and that
# would look like every submission failing rather than like a config mistake.
RESERVED = frozenset(
    """
    break case catch class const continue debugger default delete do else enum export extends
    false finally for function if import in instanceof new null return super switch this throw
    true try typeof var void while with yield let static await
    """.split()
)

JSDOC = {
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "string": "string",
    "char": "string",
    "void": "void",
    "listnode": "ListNode|null",
    "treenode": "TreeNode|null",
}


def jsdoc(type_: Type) -> str:
    """Render a signature type as a JSDoc type."""
    if type_.kind == "list":
        return f"{jsdoc(type_.of)}[]" if type_.of else "Array"
    if type_.kind == "matrix":
        return f"{jsdoc(type_.of)}[][]" if type_.of else "Array"
    if type_.kind == "null":
        return f"({jsdoc(type_.of)}|null)" if type_.of else "null"
    return JSDOC.get(type_.kind, "*")


class JavaScriptPack:
    slug = "javascript"
    label = "JavaScript"
    extension = "js"
    runs_in_browser = True

    def wasm_path(self) -> str:
        return f"{settings.JUDGE_WASM_DIR}/quickjs.wasm"

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
        if not IDENTIFIER.match(entrypoint) or entrypoint in RESERVED:
            raise ValueError(f"entrypoint {entrypoint!r} is not a usable JavaScript identifier")
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
                # --std is what puts `std` in reach, which is how the driver
                # reads stdin and writes its results. The program travels on
                # argv, so the guest still gets no filesystem.
                #
                # -C forces a classic script. qjs otherwise autodetects, and
                # module code refuses to let a problem's preamble redefine
                # `_build` — which is exactly what every structural problem
                # does, and how the Python pack has always worked.
                argv=("qjs", "--std", "-C", "-e", PROGRAM_SLOT),
                wasm_path=self.wasm_path(),
                # Measured on this catalogue: startup burns 3.1M (CPython's is
                # 240M) and the heaviest problem — islands on a 200x200 grid —
                # 602M. 3G is ~5x the worst real solve, the same headroom Python
                # gets, and trips an infinite loop in about 170ms.
                fuel=3_000_000_000,
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"function {entrypoint}() {{\n  // your turn, little toy…\n}}\n"
        params = ", ".join(p.name for p in signature.params)
        doc = "".join(f" * @param {{{jsdoc(p.type)}}} {p.name}\n" for p in signature.params)
        doc += f" * @returns {{{jsdoc(signature.returns)}}}\n"
        body = "  // your turn, little toy…"
        return f"/**\n{doc} */\nfunction {entrypoint}({params}) {{\n{body}\n}}\n"


PACK = JavaScriptPack()

__all__ = ["DEFAULT_ADAPTERS", "DRIVER", "ENTRYPOINT_SLOT", "PACK", "JavaScriptPack", "jsdoc"]
