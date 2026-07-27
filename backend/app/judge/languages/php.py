"""The PHP pack — php-cgi-on-WASI, the one language that comes in a different door.

Every other pack hands its program to the interpreter on argv. The only PHP
build with a WASI target is `php-cgi`, which has no `-r`: it takes a *file*, and
the guest has no filesystem, or it reads the script from **stdin**.

So this pack sends the program down stdin and carries the cases inside it, at
`CASES_SLOT`. That changes nothing that matters — the payload is the same one
`build_stdin` produces for everyone else, arguments only and never expected
values, so there is still nothing in the sandbox to forge a pass from.

`-q` suppresses the CGI headers that would otherwise land on top of the results.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.config import settings
from app.judge.languages.base import ProgramSpec, RunnerSpec
from app.judge.signature import Signature, Type

# The other packs put the identity adapters *first* and let a problem's preamble
# redefine them. PHP is the one language that refuses to redeclare a function at
# all, so here they go last and stand down if the problem already supplied its
# own. Same rule — the problem's adapters win — reached the only way PHP allows.
DEFAULT_ADAPTERS = """\
if (!function_exists('_build')) {
  // Turn the JSON argument list into the real call arguments.
  function _build($args) { return $args; }
}

if (!function_exists('_dump')) {
  // Turn the return value back into something JSON can hold.
  function _dump($value) { return $value; }
}
"""

ENTRYPOINT_SLOT = "__WINDUP_ENTRYPOINT__"

# `JSON_THROW_ON_ERROR` without `JSON_PARTIAL_OUTPUT_ON_ERROR`, so NAN and INF
# make json_encode fail rather than quietly becoming 0 — the same refusal the
# Python driver spells `allow_nan=False`.
#
# Output buffering catches the toy's own `echo`. The driver then writes its own
# row with `echo` too, but *after* `ob_get_clean()` has closed the buffer, so the
# two never mix. That indirection is forced: php-cgi defines neither the `STDOUT`
# constant nor the `php://stdout` stream, both verified absent in this build.
DRIVER = """

function __windup_plain($value) {
  $encoded = json_encode($value, JSON_THROW_ON_ERROR);
  return json_decode($encoded, true);
}

function __windup_main($payload) {
  foreach ($payload["tests"] as $case) {
    $row = ["ordinal" => $case["ordinal"], "actual" => null, "stdout" => "", "error" => null];
    ob_start();
    try {
      $value = _dump(__WINDUP_ENTRYPOINT__(...array_values(_build($case["args"]))));
      $row["actual"] = __windup_plain($value);
    } catch (Throwable $err) {
      $row["error"] = get_class($err) . ": " . $err->getMessage();
    }
    $row["stdout"] = substr((string) ob_get_clean(), 0, 2000);
    echo json_encode($row), "\\n";
    flush();
  }
}

// A nowdoc, because it is the one PHP string literal with no escaping at all.
// The payload is a single line of JSON, so it cannot contain the terminator,
// and a quote or backslash inside it means exactly itself.
__windup_main(json_decode(<<<'__WINDUP_JSON__'
__WINDUP_CASES__
__WINDUP_JSON__, true));
"""

IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

RESERVED = frozenset(
    """
    abstract and array as break callable case catch class clone const continue declare default
    do echo else elseif empty enddeclare endfor endforeach endif endswitch endwhile enum extends
    final finally fn for foreach function global goto if implements include instanceof insteadof
    interface isset list match namespace new or print private protected public readonly require
    return static switch throw trait try unset use var while xor yield
    """.split()
)

PHPDOC = {
    "int": "int",
    "float": "float",
    "bool": "bool",
    "string": "string",
    "char": "string",
    "void": "void",
    "listnode": "?ListNode",
    "treenode": "?TreeNode",
}


def phpdoc(type_: Type) -> str:
    """Render a signature type as a PHPDoc type."""
    if type_.kind == "list":
        return f"{phpdoc(type_.of)}[]" if type_.of else "array"
    if type_.kind == "matrix":
        return f"{phpdoc(type_.of)}[][]" if type_.of else "array"
    if type_.kind == "null":
        return f"?{phpdoc(type_.of)}" if type_.of else "null"
    return PHPDOC.get(type_.kind, "mixed")


class PhpPack:
    slug = "php"
    label = "PHP"
    extension = "php"
    runs_in_browser = False

    def wasm_path(self) -> str:
        return f"{settings.JUDGE_WASM_DIR}/php.wasm"

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
        if not IDENTIFIER.match(entrypoint) or entrypoint.lower() in RESERVED:
            raise ValueError(f"entrypoint {entrypoint!r} is not a usable PHP identifier")
        # One `<?php` opens the whole program; the toy writes bare PHP, as it
        # would in any editor that already knows the file is PHP.
        source = "\n".join(
            [
                "<?php",
                preamble or "",
                code,
                DEFAULT_ADAPTERS,
                DRIVER.replace(ENTRYPOINT_SLOT, entrypoint),
            ]
        )
        return ProgramSpec(
            source=source,
            runner=RunnerSpec(
                language=self.slug,
                # -q drops the CGI headers. html_errors=0 keeps a fatal from
                # arriving wrapped in <b> tags, so what the toy is shown when
                # its code will not even parse is the message PHP wrote.
                argv=("php", "-q", "-d", "html_errors=0"),
                wasm_path=self.wasm_path(),
                fuel=6_000_000_000,
                program_on_stdin=True,
            ),
        )

    def starter_code(self, *, entrypoint: str, signature: Signature | None = None) -> str:
        if signature is None:
            return f"function {entrypoint}() {{\n  // your turn, little toy…\n}}\n"
        params = ", ".join(f"${p.name}" for p in signature.params)
        doc = "".join(f" * @param {phpdoc(p.type)} ${p.name}\n" for p in signature.params)
        doc += f" * @return {phpdoc(signature.returns)}\n"
        body = "  // your turn, little toy…"
        return f"/**\n{doc} */\nfunction {entrypoint}({params}) {{\n{body}\n}}\n"


PACK = PhpPack()

__all__ = ["DEFAULT_ADAPTERS", "DRIVER", "ENTRYPOINT_SLOT", "PACK", "PhpPack", "phpdoc"]
