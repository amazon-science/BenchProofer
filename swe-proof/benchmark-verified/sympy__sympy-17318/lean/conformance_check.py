#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-17318.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_decompose` skeleton — specifically its R-content, the changed
GUARD `allSquarePosRat` and the branch it selects — and diffs it against the
REAL patched predicate executed over sympy objects, over a discrete boundary
catalogue (incl. the issue's `4 + I` shape) plus >=1e5 randomized draws.

The modeled function is the guard at the top of `_sqrt_match`'s `p.is_Add`
branch, which the gold patch changes from

    if all((x**2).is_Rational for x in pargs):            # base_commit

to

    sqargs = [x**2 for x in pargs]
    if all(sq.is_Rational and sq.is_positive for sq in sqargs):   # patched

and then either calls the fast routine `split_surds(p)` (guard True) or falls
through to the general depth-based matcher (guard False). The OBSERVABLE the
patch changes is WHICH branch is selected; the two routines are unchanged opaque
callees (A-reference) and are NOT re-implemented here.

Two legs:
  * REAL leg  — the EXACT patched predicate `all(sq.is_Rational and
    sq.is_positive for sq in [x**2 for x in pargs])` evaluated over real sympy
    addends, returning the selected branch ("fast" / "general").
  * SHADOW leg — transliteration of `allSquarePosRat`: over the modeled addends
    (`sq : Option Rat`), `all(squarePosRat a)` where `squarePosRat (some q) = (0
    < q)` and `squarePosRat none = False`.

An `Addend` is modeled as one of three kinds, chosen so its sympy square has the
target classification:
    ('pos', q)   q a positive Fraction  -> addend sqrt(q)  (q>0 rational) : x**2 == q  (rational, positive)
    ('neg', q)   q a positive Fraction  -> addend I*sqrt(q)               : x**2 == -q (rational, negative)
    ('imag',)                            -> addend I                       : x**2 == -1 (rational, negative)
    ('irr', k)                           -> addend distinct Symbol s_k     : x**2 == s_k**2 (NOT rational)
The shadow `sq` is `some q` for 'pos', `some (-q)` for 'neg', `some (-1)` for
'imag', `none` for 'irr'. Both legs must agree on the selected branch for every
case. Exit 0 iff zero disagreements. sympy + stdlib only (pinned seed).
"""
import random
import sys
from fractions import Fraction

SEED = 17318
N_RANDOM = 120_000  # >= 1e5


def shadow_branch(addends):
    """Python shadow of implementation_decompose's branch selection.
    addends: list of modeled addends with a shadow square `sq`:
       ('pos', q) -> some(q);  ('neg', q) -> some(-q);
       ('imag',)  -> some(-1); ('irr', k) -> none
    Returns 'fast' if allSquarePosRat is True, else 'general'."""
    def square_pos_rat(a):
        tag = a[0]
        if tag == 'pos':
            q = a[1]          # some q,  q > 0
            return q > 0
        if tag == 'neg':
            q = -a[1]         # some (-q), q > 0  => negative
            return q > 0      # always False
        if tag == 'imag':
            return -1 > 0     # some (-1) => False
        # 'irr' -> none
        return False
    return 'fast' if all(square_pos_rat(a) for a in addends) else 'general'


def main():
    from sympy import sqrt, S, Symbol, Rational
    I = S.ImaginaryUnit

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    syms = [Symbol('s%d' % k, positive=False) for k in range(6)]

    def to_sympy(a):
        tag = a[0]
        if tag == 'pos':
            q = a[1]
            return sqrt(Rational(q.numerator, q.denominator))
        if tag == 'neg':
            q = a[1]
            return I * sqrt(Rational(q.numerator, q.denominator))
        if tag == 'imag':
            return I
        # 'irr' -> a symbolic atom: its square is symbolic, not Rational
        return syms[a[1]]

    def real_branch(addends):
        """The EXACT patched predicate over real sympy addends."""
        pargs = [to_sympy(a) for a in addends]
        sqargs = [x**2 for x in pargs]
        if all(sq.is_Rational and sq.is_positive for sq in sqargs):
            return 'fast'
        return 'general'

    def gen_addend(rng):
        r = rng.random()
        if r < 0.45:
            num = rng.randint(1, 30)
            den = rng.randint(1, 12)
            return ('pos', Fraction(num, den))
        if r < 0.70:
            num = rng.randint(1, 30)
            den = rng.randint(1, 12)
            return ('neg', Fraction(num, den))
        if r < 0.85:
            return ('imag',)
        return ('irr', rng.randint(0, len(syms) - 1))

    def gen_case(rng):
        n = rng.randint(1, 5)
        return [gen_addend(rng) for _ in range(n)]

    # deterministic boundary catalogue (incl. the issue's shapes)
    boundary = [
        [('imag',)],                                   # _sqrt_match(... I ...): I**2 == -1 -> general
        [('pos', Fraction(4, 1)), ('imag',)],          # 4 + I  : 16, -1 -> general (the issue)
        [('pos', Fraction(2, 1))],                     # sqrt(2): square 2>0 -> fast
        [('pos', Fraction(2, 1)), ('pos', Fraction(3, 1))],   # all positive rational -> fast
        [('pos', Fraction(1, 2)), ('pos', Fraction(7, 3))],   # positive rational fractions -> fast
        [('neg', Fraction(3, 1))],                     # I*sqrt(3): square -3 -> general
        [('pos', Fraction(5, 1)), ('neg', Fraction(2, 1))],   # mixed sign rational -> general
        [('irr', 0)],                                  # symbolic atom: square not rational -> general
        [('pos', Fraction(2, 1)), ('irr', 1)],         # one irrational square -> general
        [('imag',), ('imag',)],                        # two imaginary -> general
    ]
    cases = list(boundary)
    for _ in range(N_RANDOM):
        cases.append(gen_case(rng))

    for addends in cases:
        exp = real_branch(addends)
        got = shadow_branch(addends)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH addends={addends}: real={exp} shadow={got}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
