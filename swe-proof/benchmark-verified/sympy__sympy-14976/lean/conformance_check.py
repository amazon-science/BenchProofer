#!/usr/bin/env python
"""G-CONF — differential test of the R/I shadow of implementation_mpfRational
against the patch.diff behaviour (post-patch `MpmathPrinter._print_Rational`).

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The impl region is NOT all-A-tagged (it has I/R structure:
the literal string assembly of the template `{0}({1})/{0}({2})`). The two
A-reference ops (`self._module_format('mpmath.mpf')` and `str(int)`) are left as
the REAL repo callees — exactly what the post-patch `_print_Rational` consumes.
The shadow therefore reproduces the post-patch behaviour op-for-op over fuzzed
`(p, q)` integer pairs. We assert zero disagreements vs the real patched
`MpmathPrinter._print_Rational` over >=10^5 fuzzed inputs.

stdlib-only fuzzing. exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 14976          # pinned in mapping.md
N = 120_000           # >= 10^5


def shadow(printer, p_num: int, q_den: int) -> str:
    """R/I shadow of implementation_mpfRational:
        func = self._module_format('mpmath.mpf')
        return func + '(' + str(p) + ')/' + func + '(' + str(q) + ')'
    The A-reference ops (_module_format, str(int)) are realised by REAL callees.
    """
    func = printer._module_format('mpmath.mpf')   # real callee
    return func + "(" + str(p_num) + ")/" + func + "(" + str(q_den) + ")"


def main() -> int:
    from sympy.printing.pycode import MpmathPrinter
    from sympy import Rational

    printer = MpmathPrinter()
    rng = random.Random(SEED)

    disagreements = 0
    examples = []

    # Deterministic boundary cases first (incl. the F2P input 1/2 and the
    # issue value 232/3).
    fixed = [(1, 2), (232, 3), (-3, 4), (-1, 7), (7, 1000000),
             (5, 2), (-5, 2), (10, 3), (1, 3), (2, 3)]
    cases = list(fixed)
    for _ in range(N):
        p_num = rng.choice([1, -1]) * rng.randint(1, 10 ** rng.randint(1, 12))
        q_den = rng.randint(2, 10 ** rng.randint(1, 12))   # q != 1 (canonical Rational)
        cases.append((p_num, q_den))

    for p_num, q_den in cases:
        e = Rational(p_num, q_den)
        if e.q == 1:
            continue  # canonicalized to an Integer; not dispatched to _print_Rational
        got = shadow(printer, e.p, e.q)
        want = printer._print_Rational(e)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((p_num, q_den, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for pn, qd, g, w in examples:
            print(f"  p={pn} q={qd} shadow={g!r} real={w!r}")
        return 1

    print(f"G-CONF OK: {len(cases)} inputs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
