#!/usr/bin/env python3
"""G-AX for astropy__astropy-13033 — A-reference validation.

The bundle deep-models the mismatch-message construction of
`BaseTimeSeries._check_required_columns`; ONE building block is left abstract
in the Lean model: `opaque pyReprStr : String -> String`, the platform's
canonical rendering of one text value as it appears inside a rendered list.
Its declared binding (Solution.lean axioms region, mapping.md) is Python's
`repr` of a `str` — the per-element rendering `str(list)` applies. This is an
UNCHANGED builtin of the platform (the patch only decides WHICH collections
are rendered and WHEN the single-name vs whole-list form is used).

This check validates the binding executably, in-container at base_commit:

1. `pyListRepr` leg: for adversarial lists of names (embedded single/double
   quotes, backslashes, control characters, non-ASCII, empty strings), the
   Lean-side composition `"[" ++ ", ".join(pyReprStr x) ++ "]"` with
   `pyReprStr := repr` must equal the REAL `str(list)` byte-for-byte — this
   is exactly how the modeled call site renders a multi-name collection.
2. `repr`-shape sanity on each individual name: `repr(s)` evaluates back to
   `s` (round-trip via `ast.literal_eval`), pinning that the abstract symbol
   is bound to a genuine canonical rendering, not an accident of str(list).

stdlib-only. Pinned seed: 13033 (also in mapping.md). exit 0 iff sound.
"""
import ast
import json
import random
import sys

SEED = 13033
N = 50_000

ADVERSARIAL = [
    "a'b", 'a"b', "a'b\"c", "'", '"', "''", "\\", "a\\b", "a\\\\b",
    "a\tb", "a\nb", "a\rb", "\x00", "\x1b[31m", "\x7f", "\x80", "\xa0",
    "écolønne", "列名", "time", "flux", "", " ", " lead", "trail ",
    "it's", 'she said "hi"', "mix'ed\"and\\slash", " ", "\U0001F600",
]

PLAIN = ["time", "a", "b", "flux", "banana", "x", "y", "z", "col_1"]


def lean_py_list_repr(xs):
    """Transliteration of Lean pyListRepr with pyReprStr bound to repr."""
    return "[" + ", ".join(repr(x) for x in xs) + "]"


def rand_name(rng):
    kind = rng.randint(0, 3)
    if kind == 0:
        return rng.choice(PLAIN)
    if kind == 1:
        return rng.choice(ADVERSARIAL)
    # random codepoint soup, heavy on quote/backslash/control chars
    alphabet = "ab'\"\\\t\n\r\x00\x1f\x7f\xa0é€𝛼 z"
    return "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 6)))


def main() -> int:
    checked = 0

    # --- leg 2: repr round-trips each name (canonical-rendering sanity) ---
    for s in ADVERSARIAL + PLAIN:
        if ast.literal_eval(repr(s)) != s:
            print(f"DISAGREE roundtrip: repr({s!r}) does not evaluate back")
            print("status=fail")
            return 1
        checked += 1

    # --- leg 1, edges: str(list) == pyListRepr composition ---
    edge_lists = (
        [[]] +
        [[s] for s in ADVERSARIAL] +
        [["time", s] for s in ADVERSARIAL] +
        [ADVERSARIAL, PLAIN, ["time", "a'b"], ["time", "flux"]]
    )
    for xs in edge_lists:
        real = str(xs)
        model = lean_py_list_repr(xs)
        if real != model:
            print(f"DISAGREE edge: str({xs!r}) = {real!r} != model {model!r}")
            print("status=fail")
            return 1
        checked += 1

    # --- leg 1, fuzz ---
    rng = random.Random(SEED)
    for _ in range(N):
        xs = [rand_name(rng) for _ in range(rng.randint(0, 5))]
        real = str(xs)
        model = lean_py_list_repr(xs)
        if real != model:
            print(f"DISAGREE fuzz: str({xs!r}) = {real!r} != model {model!r}")
            print("status=fail")
            return 1
        # keep the per-element binding honest under fuzz too
        for s in xs:
            if ast.literal_eval(repr(s)) != s:
                print(f"DISAGREE roundtrip fuzz: {s!r}")
                print("status=fail")
                return 1
        checked += 1

    print(json.dumps({
        "status": "pass",
        "instance": "astropy__astropy-13033",
        "checked": checked,
        "disagreements": 0,
        "callee": "str.__repr__ / str(list) per-element rendering",
        "kind": "A-reference",
        "binds": "pyReprStr (opaque)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
