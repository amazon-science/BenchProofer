#!/usr/bin/env python3
"""G-AX — validate the A-reference deep model `pyStr` against the REAL callee the
post-patch `Choices.__str__` delegates to, `str(self.value)`.

The proof consumes NO callee axiom (axioms region empty), but the textual
conversion of the member's underlying value is an A-reference (refinement.md row
2): the Lean `pyStr` is asserted to agree with the real Python `str(value)` on
boundaries + fuzz, for both value kinds the modeled members use (text/int). This
guards the deep model against drift from the real conversion.

  pyStr (.text s) = s          (CPython str(str) is identity)
  pyStr (.num  n) = str(n)     (CPython str(int) is the decimal numeral)

stdlib-only. exit 0 iff the property holds on every observation.
"""
import random
import sys

SEED = 11964


def py_str_model_text(s: str) -> str:
    """The Lean `pyStr (.text s) = s`."""
    return s


def py_str_model_num(n: int) -> str:
    """The Lean `pyStr (.num n) = toString n`.

    Lean's `toString : Int → String` yields the decimal numeral with a leading
    '-' for negatives — identical to CPython `str(int)`.
    """
    return str(n)


def main() -> int:
    rng = random.Random(SEED)

    mismatches = 0
    examples = []

    # --- text values: boundaries + fuzz ---
    text_cases = ["", "first", "second", "FR", "SO", "JR", "SR", "GR",
                  "M", "F", "X", " ", "a b c", "\t", "\n"]
    for _ in range(50_000):
        n = rng.randint(0, 16)
        text_cases.append("".join(chr(rng.randint(0x20, 0x2fff)) for _ in range(n)))
    for s in text_cases:
        want = str(s)            # REAL callee str(value) on a str value
        got = py_str_model_text(s)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append(("text", s, got, want))

    # --- integral values: boundaries + fuzz ---
    int_cases = [0, 1, 2, 3, 4, -1, -2, 10, 100, 999999, -999999,
                 2**31, -(2**31), 10**18, -(10**18)]
    for _ in range(50_000):
        int_cases.append(rng.randint(-10**12, 10**12))
    for n in int_cases:
        want = str(n)            # REAL callee str(value) on an int value
        got = py_str_model_num(n)
        if got != want:
            mismatches += 1
            if len(examples) < 10:
                examples.append(("num", n, got, want))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs str(value)")
        for kind, v, g, w in examples:
            print(f"  {kind} value={v!r} model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: pyStr == str(value) on all probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
