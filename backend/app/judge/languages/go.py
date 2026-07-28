"""The Go pack — TinyGo to wasm32-wasip1.

The one compiled language with JSON in its standard library, so this is the one
place a compiled pack lets the guest do its own serialising: `encoding/json` is
stdlib, tested by people who are not us, and using it removes the only
hand-written emitter Go would otherwise need. The *arguments* still arrive as
typed literals, exactly as in C++ and Rust — nothing is parsed in the guest.
"""

from __future__ import annotations

from app.judge.compile import OUTPUT_SLOT, SOURCE_SLOT, CompileSpec, which
from app.judge.languages.compiled import CASES_SLOT, CompiledPack, json_string, toolchain_dir
from app.judge.signature import Signature, Type

TYPES = {
    "int": "int64",
    "float": "float64",
    "bool": "bool",
    "string": "string",
    "char": "rune",
    "void": "any",
    "listnode": "*ListNode",
    "treenode": "*TreeNode",
}

PRELUDE = """\
package main

import (
\t"encoding/json"
\t"fmt"
\t"os"
)

var _ = fmt.Sprintf
var _ = os.Stdout

func _report(ordinal int, actual any) {
\trow := map[string]any{"ordinal": ordinal, "actual": actual, "stdout": "", "error": nil}
\tout, err := json.Marshal(row)
\tif err != nil {
\t\tfmt.Fprintln(os.Stderr, "returned something JSON can't hold:", err)
\t\tos.Exit(1)
\t}
\tos.Stdout.Write(append(out, '\\n'))
\tos.Stdout.Sync()
}
"""

# Go has no function overloading, so the identity adapter would collide with a
# problem's own. It stands down instead, the same rule PHP and Rust need.
DEFAULT_DUMP = """
func _dump[T any](v T) T { return v }
"""

MAIN = """
func main() {
__WINDUP_CASES__
}
"""


class GoPack(CompiledPack):
    slug = "go"
    label = "Go"
    extension = "go"
    source_name = "main.go"
    reserved = frozenset(
        """
        break case chan const continue default defer else fallthrough for func go goto if
        import interface map package range return select struct switch type var
        """.split()
    )

    def render_type(self, type_: Type) -> str:
        if type_.kind == "list":
            return f"[]{self.render_type(type_.of)}" if type_.of else "[]int64"
        if type_.kind == "matrix":
            inner = self.render_type(type_.of) if type_.of else "int64"
            return f"[][]{inner}"
        if type_.kind == "null":
            # Go's zero values can't express "absent" for a scalar, so a
            # nullable one becomes a pointer.
            return f"*{self.render_type(type_.of)}" if type_.of else "*int64"
        return TYPES.get(type_.kind, "any")

    def render_value(self, type_: Type, value: object) -> str:
        if type_.kind in ("list", "matrix"):
            inner = type_.of if type_.kind == "list" else Type("list", type_.of or Type("int"))
            items = ", ".join(self.render_value(inner, item) for item in value)
            return f"{self.render_type(type_)}{{{items}}}"
        if type_.kind == "null":
            inner = type_.of or Type("int")
            if value is None:
                return f"({self.render_type(type_)})(nil)"
            # No address-of a literal in Go, so it goes through a helper call.
            return f"_ptr[{self.render_type(inner)}]({self.render_value(inner, value)})"
        if type_.kind == "bool":
            return "true" if value else "false"
        if type_.kind == "int":
            return f"int64({int(value)})"
        if type_.kind == "float":
            return f"float64({float(value)})"
        if type_.kind == "string":
            return json_string(str(value))
        if type_.kind == "char":
            return f"'{value}'"
        raise ValueError(f"Go has no literal for {type_}")

    def assemble(self, *, entrypoint: str, preamble: str, code: str, returns: Type) -> str:
        parts = [PRELUDE, "\nfunc _ptr[T any](v T) *T { return &v }\n", preamble or "", code]
        if "func _dump" not in (preamble or ""):
            parts.append(DEFAULT_DUMP)
        parts.append(MAIN)
        return "\n".join(parts)

    def render_case(self, *, ordinal: int, call: str) -> str:
        return f"\t_report({ordinal}, _dump({call}))\n"

    def compile_spec(self) -> CompileSpec:
        tinygo = toolchain_dir() / "tinygo" / "bin" / "tinygo"
        if not tinygo.exists():
            tinygo = which("tinygo") or tinygo
        # TinyGo shells out to the Go toolchain and to wasm-opt, so unlike the
        # other two it needs a PATH with more than nothing on it.
        extra_path = ":".join(["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin", "/bin"])
        return CompileSpec(
            language=self.slug,
            source_name=self.source_name,
            toolchain=tinygo,
            argv=(str(tinygo), "build", "-target=wasip1", "-o", OUTPUT_SLOT, SOURCE_SLOT),
            env={"PATH": extra_path},
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"func {entrypoint}() {{\n\t// your turn, little toy…\n}}\n"
        params = ", ".join(f"{p.name} {self.render_type(p.type)}" for p in signature.params)
        returns = self.render_type(signature.returns)
        suffix = "" if signature.returns.kind == "void" else f" {returns}"
        return f"func {entrypoint}({params}){suffix} {{\n\t// your turn, little toy…\n}}\n"


PACK = GoPack()

__all__ = ["CASES_SLOT", "DEFAULT_DUMP", "MAIN", "PACK", "PRELUDE", "GoPack"]
