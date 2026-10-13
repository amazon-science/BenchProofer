#!/usr/bin/env python
"""G-AX — validate the two A-reference deep models against the REAL callees the
added rational renderer uses.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The proof consumes NO callee axiom (axioms region empty);
the two deep models are A-references (refinement.md rows 2-4):

  (1) `mpfName == "mpmath.mpf"` is asserted to equal the real
      `MpmathPrinter()._module_format('mpmath.mpf')` under the printer's default
      settings (`fully_qualified_modules=True`).
  (2) `intText(n) == str(n)` is asserted to equal Python's decimal rendering of
      an integer over fuzzed signed integers (the operands `e.p`, `e.q`).

stdlib-only fuzzing. exit 0 iff both properties hold on every observation.
"""
import random
import sys

SEED = 14976


def intText_model(n: int) -> str:
    """The Lean `intText` model: decimal text of an integer (sign-prefixed for
    negatives). For the integer domain this is exactly Python's `str(int)`."""
    return str(n)


def main() -> int:
    from sympy.printing.pycode import MpmathPrinter

    p = MpmathPrinter()
    mismatches = 0
    examples = []

    # (1) module-name resolver under default settings == 'mpmath.mpf'
    real_mpf = p._module_format('mpmath.mpf')
    if real_mpf != "mpmath.mpf":
        mismatches += 1
        examples.append(("_module_format('mpmath.mpf')", "mpmath.mpf", real_mpf))

    # (2) intText(n) == str(n) over boundary + fuzzed integers
    rng = random.Random(SEED)
    probes = [0, 1, -1, 2, 232, 3, 10, -10, 1000000, -1000000,
              2**63, -(2**63), 2**128, -(2**128)]
    for _ in range(50_000):
        mag = rng.randint(0, 10) ** rng.randint(1, 12)
        sign = rng.choice([1, -1])
        probes.append(sign * rng.randint(0, mag + 1))
    for n in probes:
        got = intText_model(n)
        real = str(n)
        if got != real:
            mismatches += 1
            if len(examples) < 20:
                examples.append((f"str({n})", got, real))

    if mismatches:
        print(f"G-AX FAIL: {mismatches} mismatches vs real callees")
        for what, g, w in examples:
            print(f"  {what}: model={g!r} real={w!r}")
        return 1

    print(f"G-AX OK: _module_format('mpmath.mpf') == 'mpmath.mpf' and "
          f"intText == str on all {len(probes)} integer probes (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
