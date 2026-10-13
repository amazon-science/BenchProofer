#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-15599.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_modFactors` skeleton (the R/I per-factor reduction loop) and
diffs it against the REAL patched logic over a discrete boundary catalogue plus
>=1e5 randomized draws.

The modeled function is the `non_mod_l` reduction loop the gold patch adds to
`Mod.eval`'s `Mul` branch:

    if q.is_Integer and q is not S.One:
        _ = []
        for i in non_mod_l:
            if i.is_Integer and (i % q is not S.Zero):
                _.append(i % q)
            else:
                _.append(i)
        non_mod_l = _

Two legs:
  * REAL leg  — the exact patched loop executed over sympy objects, using the
    real repo callees `i.is_Integer`, sympy `Integer.__mod__` (`i % q`) and the
    `is not S.Zero` identity test. This is the actual behavior the patch ships.
  * SHADOW leg — transliteration of `implementation_modFactors` /
    `problem_spec_modFactors`: a fresh-list accumulator using `intMod` (floored
    Python remainder, sign of divisor) and `!= 0`.

A `Factor` is modeled as a tagged tuple:
    ('coeff', n)  with n a Python int   <-> a concrete-integer factor (is_Integer)
    ('sym', k)    with k a Python int   <-> a symbolic / non-integer factor

For the REAL leg the coeff factor is the sympy `Integer(n)`; the sym factor is a
distinct sympy `Symbol` (never an Integer, so `is_Integer` is False/None and it
is preserved). The two legs must agree on the resulting factor list for every
case. Exit 0 iff zero disagreements. stdlib + sympy only (pinned seed).
"""
import random
import sys

SEED = 15599
N_RANDOM = 120_000  # >= 1e5


def int_mod(a, b):
    """Lean `intMod a b = a - b * Int.fdiv a b` — Python floored remainder
    (residue carries the sign of the divisor). Matches Python's `%` for ints,
    which is exactly what we assert; computed independently of `%` to be a true
    transliteration of the Lean definition."""
    # Int.fdiv is floored division.
    fdiv = a // b  # Python // is floored for ints
    return a - b * fdiv


def shadow_reduce(q, factors):
    """Python shadow of implementation_modFactors(q, factors).
    factors: list of ('coeff', n) | ('sym', k).  Returns the reduced list."""
    if q == 1:
        return list(factors)
    acc = []
    for f in factors:
        tag = f[0]
        if tag == 'coeff':
            n = f[1]
            r = int_mod(n, q)
            if r != 0:
                acc.append(('coeff', r))
            else:
                acc.append(('coeff', n))
        else:  # 'sym'
            acc.append(('sym', f[1]))
    return acc


def main():
    from sympy import Integer, Symbol, S

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # a pool of distinct symbolic atoms for the 'sym' factors
    syms = [Symbol('s%d' % k) for k in range(8)]

    def real_reduce(q_int, factors):
        """The EXACT patched loop, executed over real sympy objects.
        Returns the reduced factor list back in tagged form for comparison."""
        q = Integer(q_int)
        # rebuild non_mod_l as sympy objects, remembering original tags
        non_mod_l = []
        for f in factors:
            if f[0] == 'coeff':
                non_mod_l.append(Integer(f[1]))
            else:
                non_mod_l.append(syms[f[1]])
        # --- gold patch loop (verbatim semantics) ---
        if q.is_Integer and q is not S.One:
            _ = []
            for i in non_mod_l:
                if i.is_Integer and (i % q is not S.Zero):
                    _.append(i % q)
                else:
                    _.append(i)
            non_mod_l = _
        # map back to tagged form
        out = []
        for i in non_mod_l:
            if i.is_Integer:
                out.append(('coeff', int(i)))
            else:
                # find which symbol
                k = syms.index(i)
                out.append(('sym', k))
        return out

    def gen_case(rng, small):
        nfac = rng.randint(0, 3 if small else 6)
        factors = []
        for _ in range(nfac):
            if rng.random() < 0.6:
                lo, hi = (-6, 6) if small else (-40, 40)
                factors.append(('coeff', rng.randint(lo, hi)))
            else:
                factors.append(('sym', rng.randint(0, len(syms) - 1)))
        # divisor: nonzero integer; include 1 sometimes to exercise short-circuit
        if rng.random() < 0.15:
            q = 1
        else:
            q = rng.choice([-1, 1]) * rng.randint(1, 9 if small else 25)
            if q == 0:
                q = 2
        return q, factors

    # deterministic boundary catalogue (incl. the issue's shapes)
    boundary = [
        (2, [('coeff', 3), ('sym', 0)]),          # Mod(3*i, 2) -> 1*i
        (4, [('coeff', 8), ('sym', 0)]),          # Mod(8*i, 4) -> 8 kept (residue 0)
        (1, [('coeff', 5), ('sym', 0)]),          # q == 1 short-circuit
        (2, [('coeff', -3), ('sym', 0)]),         # negative coeff, floored sign
        (3, [('coeff', 7), ('coeff', -5), ('sym', 1)]),
        (-2, [('coeff', 3), ('sym', 0)]),         # negative divisor
        (5, []),                                   # empty product
        (6, [('coeff', 6)]),                       # residue 0, single int
        (6, [('coeff', 12), ('coeff', 7)]),
    ]
    cases = list(boundary)
    for k in range(N_RANDOM):
        cases.append(gen_case(rng, small=(k % 3 == 0)))

    for q, factors in cases:
        # divisor must be nonzero (precondition q != 0)
        if q == 0:
            continue
        exp = real_reduce(q, factors)
        got = shadow_reduce(q, factors)
        checked += 1
        if got != exp:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH q={q} factors={factors}: real={exp} shadow={got}")

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
