"""How one problem is written down.

`seed_catalogue` reads plain dicts, and for a long time the catalogue wrote them
out by hand. At ninety-odd problems that stopped being readable: three quarters
of every entry was the same four derived keys, and the interesting part — the
prompt, the help shelf, the cases — was buried in them.

So the shape is declared once here. `problem()` returns exactly the dict the
seeder already understood, with the mechanical parts filled in:

- `weight_label` and `xp_reward` follow from the difficulty, so a "hard" toy
  cannot accidentally pay out like an easy one;
- `starter_code` is generated from the entrypoint and signature, in the same
  shape the hand-written stubs used, unless a problem needs its own;
- `languages` defaults to every pack, which is the common case.

`example()` and `hidden()` exist for the same reason: a case is two values and a
label, and spelling out `visibility` ninety times obscured which cases a toy
actually gets to see.
"""

from __future__ import annotations

from typing import Any

from app.db.seed_data.preambles import ALL_LANGUAGES

# Difficulty is the single knob: it names the weight on the toy's shelf tag and
# what solving it pays. Keeping the pair here is what stops the two drifting.
WEIGHTS: dict[str, tuple[str, int]] = {
    "easy": ("LIGHT WEIGHT", 50),
    "medium": ("MEDIUM WEIGHT", 60),
    "hard": ("HEAVY WEIGHT", 80),
}

STUB_COMMENT = "    # your turn, little toy…\n    pass"


def _stub(entrypoint: str, signature: dict | None) -> str:
    """A Python starter, in the shape the hand-written ones had."""
    if not entrypoint:
        return ""
    params = ", ".join(p["name"] for p in (signature or {}).get("params", []))
    return f"def {entrypoint}({params}):\n{STUB_COMMENT}"


def problem(
    *,
    zone: str,
    slug: str,
    title: str,
    difficulty: str,
    prompt: str,
    example_input: str,
    example_output: str,
    explainer: str,
    hint: str,
    approach: str,
    solution: str,
    tests: list[dict],
    entrypoint: str = "",
    signature: dict | None = None,
    starter_code: str | None = None,
    languages: dict[str, dict] | None = None,
    harness_preamble: str = "",
    compare_mode: str = "exact",
    language: str = "python",
    graded: bool = True,
) -> dict[str, Any]:
    if difficulty not in WEIGHTS:
        raise ValueError(f"{slug}: {difficulty!r} is not a difficulty")
    weight_label, xp_reward = WEIGHTS[difficulty]
    return {
        "zone": zone,
        "slug": slug,
        "title": title,
        "difficulty": difficulty,
        "weight_label": weight_label,
        "prompt": prompt,
        "example_input": example_input,
        "example_output": example_output,
        "language": language,
        "starter_code": _stub(entrypoint, signature) if starter_code is None else starter_code,
        "entrypoint": entrypoint,
        "signature": signature,
        "harness_preamble": harness_preamble,
        "graded": graded,
        "compare_mode": compare_mode,
        "explainer": explainer,
        "hint": hint,
        "approach": approach,
        "solution": solution,
        "xp_reward": xp_reward,
        "languages": ALL_LANGUAGES if languages is None else languages,
        "tests": tests,
    }


def example(args: list, expected: Any, label: str = "") -> dict:
    """A case the toy can see — and the only kind the Run button executes."""
    return {"visibility": "example", "label": label, "args": args, "expected": expected}


def hidden(label: str, args: list, expected: Any) -> dict:
    """A case that grades. Never leaves the server; see `ProblemDetailOut`."""
    return {"visibility": "hidden", "label": label, "args": args, "expected": expected}


def sig(returns: str, **params: str) -> dict:
    """`sig("list<int>", nums="list<int>", target="int")` — order is kwarg order."""
    return {
        "params": [{"name": name, "type": type_} for name, type_ in params.items()],
        "returns": returns,
    }


__all__ = ["WEIGHTS", "example", "hidden", "problem", "sig"]
