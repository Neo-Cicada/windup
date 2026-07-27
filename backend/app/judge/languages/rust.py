"""The Rust pack — rustc straight to wasm32-wasip1, no cargo and no crates.

`serde_json` would be the obvious way to talk to the driver, and it is exactly
what this pack avoids needing: the arguments arrive as typed literals and only
the return value is serialised, by an `Emit` trait with an impl per shape. That
is what lets a submission build with plain `rustc` — no manifest, no registry,
no network at build time.
"""

from __future__ import annotations

from pathlib import Path

from app.judge.compile import OUTPUT_SLOT, SOURCE_SLOT, CompileSpec
from app.judge.languages.compiled import CASES_SLOT, CompiledPack, json_string, toolchain_dir
from app.judge.signature import Signature, Type

TYPES = {
    "int": "i64",
    "float": "f64",
    "bool": "bool",
    "string": "String",
    "char": "char",
    "void": "()",
    "listnode": "Option<Box<ListNode>>",
    "treenode": "Option<Box<TreeNode>>",
}

PRELUDE = """\
#![allow(dead_code, unused_imports, unused_mut, non_snake_case)]
use std::io::Write;

trait Emit {
    fn emit(&self);
}

impl Emit for i64 {
    fn emit(&self) { print!("{}", self); }
}
impl Emit for i32 {
    fn emit(&self) { print!("{}", self); }
}
impl Emit for usize {
    fn emit(&self) { print!("{}", self); }
}
impl Emit for f64 {
    fn emit(&self) { print!("{}", self); }
}
impl Emit for bool {
    fn emit(&self) { print!("{}", if *self { "true" } else { "false" }); }
}
impl Emit for () {
    fn emit(&self) { print!("null"); }
}

fn _emit_str(s: &str) {
    print!("\\"");
    for c in s.chars() {
        match c {
            '"' => print!("\\\\\\""),
            '\\\\' => print!("\\\\\\\\"),
            '\\n' => print!("\\\\n"),
            '\\r' => print!("\\\\r"),
            '\\t' => print!("\\\\t"),
            c if (c as u32) < 0x20 => print!("\\\\u{:04x}", c as u32),
            c => print!("{}", c),
        }
    }
    print!("\\"");
}

impl Emit for String {
    fn emit(&self) { _emit_str(self); }
}
impl Emit for &str {
    fn emit(&self) { _emit_str(self); }
}
impl Emit for char {
    fn emit(&self) { _emit_str(&self.to_string()); }
}

impl<T: Emit> Emit for Vec<T> {
    fn emit(&self) {
        print!("[");
        for (i, x) in self.iter().enumerate() {
            if i > 0 { print!(","); }
            x.emit();
        }
        print!("]");
    }
}

impl<T: Emit> Emit for Option<T> {
    fn emit(&self) {
        match self {
            Some(x) => x.emit(),
            None => print!("null"),
        }
    }
}
"""

# Rust has no function overloading, so the identity adapter would collide with a
# problem's own. It stands down instead — the same rule PHP needs, for the same
# reason, reached the same way.
DEFAULT_DUMP = """
fn _dump<T: Emit>(v: T) -> T { v }
"""

MAIN = """
fn main() {
__WINDUP_CASES__
}
"""


def _rustc() -> Path:
    """The real compiler, not rustup's shim.

    The shim resolves which toolchain to run by reading `~/.rustup`, and the
    compile step deliberately hands the child a scrubbed HOME — so it would find
    nothing and refuse. Reaching past it into the installed toolchain is both
    more direct and one less thing in the way.
    """
    vendored = toolchain_dir() / "rust" / "bin" / "rustc"
    if vendored.exists():
        return vendored
    toolchains = Path.home() / ".rustup" / "toolchains"
    if toolchains.is_dir():
        for entry in sorted(toolchains.iterdir()):
            candidate = entry / "bin" / "rustc"
            if candidate.exists():
                return candidate
    return Path.home() / ".cargo" / "bin" / "rustc"


class RustPack(CompiledPack):
    slug = "rust"
    label = "Rust"
    extension = "rs"
    source_name = "main.rs"
    reserved = frozenset(
        """
        as async await break const continue crate dyn else enum extern false fn for if impl in
        let loop match mod move mut pub ref return self static struct super trait true type
        unsafe use where while
        """.split()
    )

    def render_type(self, type_: Type) -> str:
        if type_.kind == "list":
            return f"Vec<{self.render_type(type_.of)}>" if type_.of else "Vec<i64>"
        if type_.kind == "matrix":
            inner = self.render_type(type_.of) if type_.of else "i64"
            return f"Vec<Vec<{inner}>>"
        if type_.kind == "null":
            return f"Option<{self.render_type(type_.of)}>" if type_.of else "Option<i64>"
        return TYPES.get(type_.kind, "()")

    def render_value(self, type_: Type, value: object) -> str:
        if type_.kind in ("list", "matrix"):
            inner = type_.of if type_.kind == "list" else Type("list", type_.of or Type("int"))
            items = ", ".join(self.render_value(inner, item) for item in value)
            return f"vec![{items}]"
        if type_.kind == "null":
            if value is None:
                return "None"
            return f"Some({self.render_value(type_.of or Type('int'), value)})"
        if type_.kind == "bool":
            return "true" if value else "false"
        if type_.kind == "int":
            return f"{int(value)}i64"
        if type_.kind == "float":
            return f"{float(value)}f64"
        if type_.kind == "string":
            return f"String::from({json_string(str(value))})"
        if type_.kind == "char":
            return f"'{value}'"
        raise ValueError(f"Rust has no literal for {type_}")

    def assemble(self, *, entrypoint: str, preamble: str, code: str, returns: Type) -> str:
        parts = [PRELUDE, preamble or "", code]
        if "fn _dump" not in (preamble or ""):
            parts.append(DEFAULT_DUMP)
        parts.append(MAIN)
        return "\n".join(parts)

    def render_case(self, *, ordinal: int, call: str) -> str:
        return (
            f'  print!("{{{{\\"ordinal\\": {ordinal}, \\"actual\\": ");\n'
            f"  _dump({call}).emit();\n"
            f'  println!(", \\"stdout\\": \\"\\", \\"error\\": null}}}}");\n'
            f"  std::io::stdout().flush().ok();\n"
        )

    def compile_spec(self) -> CompileSpec:
        rustc = _rustc()
        return CompileSpec(
            language=self.slug,
            source_name=self.source_name,
            toolchain=rustc,
            argv=(
                str(rustc),
                "--target",
                "wasm32-wasip1",
                "-O",
                "--edition",
                "2021",
                "-o",
                OUTPUT_SLOT,
                SOURCE_SLOT,
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"fn {entrypoint}() {{\n    // your turn, little toy…\n}}\n"
        params = ", ".join(f"{p.name}: {self.render_type(p.type)}" for p in signature.params)
        returns = self.render_type(signature.returns)
        arrow = "" if returns == "()" else f" -> {returns}"
        body = "    // your turn, little toy…"
        if arrow:
            body += "\n    todo!()"
        return f"fn {entrypoint}({params}){arrow} {{\n{body}\n}}\n"


PACK = RustPack()

__all__ = ["CASES_SLOT", "DEFAULT_DUMP", "MAIN", "PACK", "PRELUDE", "RustPack"]
