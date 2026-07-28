"""The Ruby pack — CRuby-on-WASI, same sandbox, same wire format."""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.judge.languages.base import PROGRAM_SLOT, ProgramSpec, RunnerSpec
from app.judge.signature import Signature, Type

DEFAULT_ADAPTERS = """\
def _build(args)
  # Turn the JSON argument list into the real call arguments.
  args
end

def _dump(value)
  # Turn the return value back into something JSON can hold.
  value
end
"""

ENTRYPOINT_SLOT = "__WINDUP_ENTRYPOINT__"

# Runs after the toy's code. Same contract as every other pack: one JSON object
# per case, flushed, so a fuel trap mid-run still leaves the finished cases.
#
# `$stdout` is swapped for a StringIO around each call, which catches `puts` and
# `print` alike — the moral equivalent of the Python driver's redirect. The
# driver keeps its own handle to the real one.
#
# JSON.generate refuses NaN and Infinity by default, which is the check the
# Python driver spells `allow_nan=False`.
DRIVER = '''

def __windup_describe(err)
  "#{err.class}: #{err.message}".strip
end

def __windup_main
  require "json"
  require "stringio"

  real_stdout = $stdout
  payload = JSON.parse($stdin.read)

  payload["tests"].each do |test_case|
    row = { "ordinal" => test_case["ordinal"], "actual" => nil, "stdout" => "", "error" => nil }
    captured = StringIO.new
    $stdout = captured
    begin
      value = _dump(__WINDUP_ENTRYPOINT__(*_build(test_case["args"].dup)))
      begin
        JSON.generate([value])
      rescue StandardError => generator_error
        raise TypeError, "returned something JSON can't hold: #{generator_error.message}"
      end
      row["actual"] = value
    rescue Exception => err
      row["error"] = __windup_describe(err)
    ensure
      $stdout = real_stdout
    end
    row["stdout"] = captured.string[0, 2000]
    real_stdout.puts JSON.generate(row)
    real_stdout.flush
  end
end

__windup_main
'''

# Ruby methods may end in ? or !, but a problem's entrypoint is shared across
# languages, so anything that isn't a plain identifier would not survive the
# trip anyway.
IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

RESERVED = frozenset(
    """
    BEGIN END alias and begin break case class def defined? do else elsif end ensure false for
    if in module next nil not or redo rescue retry return self super then true undef unless
    until when while yield
    """.split()
)

# Ruby is untyped, so these only ever appear in the stub's comment. They still
# earn their keep: `list<int>` versus `matrix<string>` is the difference between
# reaching for `each` and reaching for `each_with_index`.
RBS = {
    "int": "Integer",
    "float": "Float",
    "bool": "bool",
    "string": "String",
    "char": "String",
    "void": "void",
    "listnode": "ListNode?",
    "treenode": "TreeNode?",
}


def rbs(type_: Type) -> str:
    """Render a signature type the way RBS would spell it."""
    if type_.kind == "list":
        return f"Array[{rbs(type_.of)}]" if type_.of else "Array"
    if type_.kind == "matrix":
        return f"Array[Array[{rbs(type_.of)}]]" if type_.of else "Array"
    if type_.kind == "null":
        return f"{rbs(type_.of)}?" if type_.of else "nil"
    return RBS.get(type_.kind, "untyped")


class RubyPack:
    slug = "ruby"
    label = "Ruby"
    extension = "rb"
    runs_in_browser = False

    def wasm_path(self) -> str:
        return f"{settings.JUDGE_WASM_DIR}/ruby.wasm"

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
            raise ValueError(f"entrypoint {entrypoint!r} is not a usable Ruby identifier")
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
                argv=("ruby", "-e", PROGRAM_SLOT),
                wasm_path=self.wasm_path(),
                # Measured on this catalogue: booting the interpreter and
                # requiring json costs 0.54G on its own — twice CPython's whole
                # startup — and the heaviest problem finishes at 1.13G. 6G keeps
                # the same ~5x headroom the other packs get.
                fuel=6_000_000_000,
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"def {entrypoint}\n  # your turn, little toy…\nend\n"
        params = ", ".join(p.name for p in signature.params)
        doc = "".join(f"# @param {p.name} [{rbs(p.type)}]\n" for p in signature.params)
        doc += f"# @return [{rbs(signature.returns)}]\n"
        return f"{doc}def {entrypoint}({params})\n  # your turn, little toy…\nend\n"


PACK = RubyPack()

__all__ = ["DEFAULT_ADAPTERS", "DRIVER", "ENTRYPOINT_SLOT", "PACK", "RubyPack", "rbs"]
