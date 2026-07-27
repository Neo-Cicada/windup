"""The typed shape of a problem's entrypoint.

Python and JavaScript can call `entrypoint(*args)` and never think about types,
but a stub for a statically typed language cannot be written without them: a `[]`
in a test case is an `int[]` in one problem and a `String[]` in the next. The
signature is what each language pack renders its starter code from — and, where
the language needs it, the JSON decoding in its driver too.

The type language is deliberately tiny. It covers what the catalogue's problems
actually take and return, and nothing else:

    int  float  bool  string  char  void
    list<T>  matrix<T>  null<T>
    listnode  treenode

`matrix<T>` is sugar for `list<list<T>>` — spelled out because a grid reads as a
grid, and a language that wants the long form can call `expand()`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

SCALARS = frozenset({"int", "float", "bool", "string", "char", "void"})
STRUCTURED = frozenset({"listnode", "treenode"})
GENERICS = frozenset({"list", "matrix", "null"})


@dataclass(frozen=True)
class Type:
    kind: str
    of: Type | None = None

    def __str__(self) -> str:
        return self.kind if self.of is None else f"{self.kind}<{self.of}>"


def parse_type(text: str) -> Type:
    """Read one type. Recursive, because `list<list<int>>` is a real thing."""
    text = text.strip()
    if not text:
        raise ValueError("a type cannot be empty")

    if "<" in text:
        kind, _, rest = text.partition("<")
        kind = kind.strip()
        if not rest.endswith(">"):
            raise ValueError(f"unbalanced angle brackets in type {text!r}")
        if kind not in GENERICS:
            raise ValueError(f"type {kind!r} does not take a parameter")
        return Type(kind, parse_type(rest[:-1]))

    if text in GENERICS:
        raise ValueError(f"type {text!r} needs a parameter, e.g. {text}<int>")
    if text not in SCALARS | STRUCTURED:
        raise ValueError(f"unknown type {text!r}")
    return Type(text)


def expand(type_: Type) -> Type:
    """`matrix<T>` as the `list<list<T>>` it stands for. Other types unchanged."""
    if type_.kind == "matrix":
        assert type_.of is not None
        return Type("list", Type("list", expand(type_.of)))
    if type_.of is not None:
        return Type(type_.kind, expand(type_.of))
    return type_


@dataclass(frozen=True)
class Param:
    name: str
    type: Type


@dataclass(frozen=True)
class Signature:
    """What the entrypoint takes and gives back."""

    params: tuple[Param, ...]
    returns: Type

    @classmethod
    def parse(cls, raw: Any) -> Signature:
        """Read the `signature_json` a problem carries.

        Param names are checked because they are interpolated straight into
        generated source — a name that isn't an identifier would produce a stub
        that cannot compile, and that would look like every submission failing
        rather than like the config mistake it is.
        """
        if not isinstance(raw, dict):
            raise ValueError("a signature must be an object")

        params: list[Param] = []
        seen: set[str] = set()
        for entry in raw.get("params", []):
            if not isinstance(entry, dict):
                raise ValueError("each param must be an object with a name and a type")
            name = str(entry.get("name", "")).strip()
            if not name.isidentifier():
                raise ValueError(f"param name {name!r} is not a usable identifier")
            if name in seen:
                raise ValueError(f"param {name!r} appears twice")
            seen.add(name)
            params.append(Param(name, parse_type(str(entry.get("type", "")))))

        returns = parse_type(str(raw.get("returns", "void")))
        return cls(tuple(params), returns)


def parse_signature(raw: Any) -> Signature | None:
    """`None` in, `None` out — a problem without a signature is allowed.

    Only the statically typed packs actually need one; Python and JavaScript can
    generate a perfectly good stub from the entrypoint name alone.
    """
    return None if raw is None else Signature.parse(raw)


__all__ = [
    "Param",
    "Signature",
    "Type",
    "expand",
    "parse_signature",
    "parse_type",
]
