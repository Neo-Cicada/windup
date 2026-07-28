"""The C++ pack — wasi-sdk clang, output run in the same wasmtime sandbox.

No JSON anywhere in the guest: the arguments arrive as typed literals the
compiler checks, and only the return value is serialised, by a handful of
`_emit` overloads whose types the signature already told us. See `compiled.py`
for why that road rather than a parser.
"""

from __future__ import annotations

from app.judge.compile import OUTPUT_SLOT, SOURCE_SLOT, CompileSpec
from app.judge.languages.compiled import CASES_SLOT, CompiledPack, json_string, toolchain_dir
from app.judge.signature import Signature, Type

TYPES = {
    "int": "long long",
    "float": "double",
    "bool": "bool",
    "string": "std::string",
    "char": "char",
    "void": "void",
    "listnode": "ListNode*",
    "treenode": "TreeNode*",
}

# The whole of the guest's serialising, and it only ever has to handle what a
# `_dump` can return. Overloads rather than a variant type: the compiler picks,
# and a type nobody wrote an overload for is a build error naming the line.
PRELUDE = """\
#include <cstdio>
#include <cstdlib>
#include <optional>
#include <string>
#include <vector>

static void _emit(bool v) { std::fputs(v ? "true" : "false", stdout); }
static void _emit(long long v) { std::printf("%lld", v); }
static void _emit(int v) { std::printf("%d", v); }
static void _emit(double v) { std::printf("%.17g", v); }

static void _emit(const std::string& s) {
  std::fputc('"', stdout);
  for (unsigned char c : s) {
    switch (c) {
      case '"': std::fputs("\\\\\\"", stdout); break;
      case '\\\\': std::fputs("\\\\\\\\", stdout); break;
      case '\\n': std::fputs("\\\\n", stdout); break;
      case '\\r': std::fputs("\\\\r", stdout); break;
      case '\\t': std::fputs("\\\\t", stdout); break;
      default:
        if (c < 0x20) std::printf("\\\\u%04x", c);
        else std::fputc(c, stdout);
    }
  }
  std::fputc('"', stdout);
}

static void _emit(char c) { _emit(std::string(1, c)); }

template <class T>
static void _emit(const std::vector<T>& xs) {
  std::fputc('[', stdout);
  for (std::size_t i = 0; i < xs.size(); i++) {
    if (i) std::fputc(',', stdout);
    _emit(xs[i]);
  }
  std::fputc(']', stdout);
}

template <class T>
static void _emit(const std::optional<T>& x) {
  if (x.has_value()) _emit(*x); else std::fputs("null", stdout);
}

// The identity adapter. A problem that needs something else defines its own
// `_dump` in its preamble, and overload resolution prefers the exact match.
template <class T>
static const T& _dump(const T& v) { return v; }
"""

MAIN = """
int main() {
__WINDUP_CASES__
  return 0;
}
"""


class CppPack(CompiledPack):
    slug = "cpp"
    label = "C++"
    extension = "cpp"
    source_name = "main.cpp"
    reserved = frozenset(
        """
        alignas alignof and asm auto bool break case catch char class const constexpr continue
        decltype default delete do double else enum explicit export extern false float for
        friend goto if inline int long mutable namespace new noexcept not nullptr operator or
        private protected public register return short signed sizeof static struct switch
        template this throw true try typedef typeid typename union unsigned using virtual void
        volatile wchar_t while xor
        """.split()
    )

    def render_type(self, type_: Type) -> str:
        if type_.kind == "list":
            return f"std::vector<{self.render_type(type_.of)}>" if type_.of else "std::vector<int>"
        if type_.kind == "matrix":
            inner = self.render_type(type_.of) if type_.of else "int"
            return f"std::vector<std::vector<{inner}>>"
        if type_.kind == "null":
            return f"std::optional<{self.render_type(type_.of)}>" if type_.of else "std::nullopt_t"
        return TYPES.get(type_.kind, "auto")

    def render_value(self, type_: Type, value: object) -> str:
        if type_.kind in ("list", "matrix"):
            inner = (
                type_.of
                if type_.kind == "list"
                else Type("list", type_.of or Type("int"))
            )
            items = ", ".join(self.render_value(inner, item) for item in value)
            return f"{self.render_type(type_)}{{{items}}}"
        if type_.kind == "null":
            if value is None:
                return f"{self.render_type(type_)}{{}}"
            inner_type = type_.of or Type("int")
            return f"{self.render_type(type_)}{{{self.render_value(inner_type, value)}}}"
        if type_.kind == "bool":
            return "true" if value else "false"
        if type_.kind == "int":
            return f"{int(value)}LL"
        if type_.kind == "float":
            return repr(float(value))
        if type_.kind in ("string", "char"):
            text = json_string(str(value))
            return f"std::string({text})" if type_.kind == "string" else f"'{value}'"
        raise ValueError(f"C++ has no literal for {type_}")

    def assemble(self, *, entrypoint: str, preamble: str, code: str, returns: Type) -> str:
        return "\n".join([PRELUDE, preamble or "", code, MAIN])

    def render_case(self, *, ordinal: int, call: str) -> str:
        # One line per case, flushed, so a fuel trap mid-run still leaves the
        # cases that finished. There is no per-case error handling: without
        # exceptions in this target a crash ends the program, and grade() already
        # counts a case the guest never reported as a failure.
        return (
            f'  std::printf("{{\\"ordinal\\": {ordinal}, \\"actual\\": ");\n'
            f"  _emit(_dump({call}));\n"
            f'  std::printf(", \\"stdout\\": \\"\\", \\"error\\": null}}\\n");\n'
            f"  std::fflush(stdout);\n"
        )

    def compile_spec(self) -> CompileSpec:
        clang = toolchain_dir() / "wasi-sdk" / "bin" / "clang++"
        return CompileSpec(
            language=self.slug,
            source_name=self.source_name,
            toolchain=clang,
            argv=(
                str(clang),
                "--target=wasm32-wasip1",
                "-std=c++20",
                "-O2",
                # No exceptions in this target; see render_case.
                "-fno-exceptions",
                "-o",
                OUTPUT_SLOT,
                SOURCE_SLOT,
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"void {entrypoint}() {{\n  // your turn, little toy…\n}}\n"
        params = ", ".join(
            f"{self.render_type(p.type)} {p.name}" for p in signature.params
        )
        returns = self.render_type(signature.returns)
        body = "  // your turn, little toy…"
        return f"{returns} {entrypoint}({params}) {{\n{body}\n}}\n"


PACK = CppPack()

__all__ = ["CASES_SLOT", "MAIN", "PACK", "PRELUDE", "CppPack"]
