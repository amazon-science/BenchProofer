#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-24539.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_asExpr` skeleton (the R/I symbol-selection + error logic) and
diffs it against the REAL patched `PolyElement.as_expr` over a discrete
catalogue plus >=1e5 randomized draws.

  observable: the result of `f.as_expr(*symbols)` for a polynomial `f` of a ring
  with `ngens` generators and a caller-supplied list `symbols` of arbitrary
  length (including empty, correct, and wrong sizes). The result is either a
  symbolic expression (compared structurally) or a raised ValueError (compared
  as the error outcome).

Shadow (transliteration of implementation_asExpr / problem_spec_asExpr) — note
the only changed logic is the symbol SELECTION; the unchanged callee
`expr_from_dict` is invoked via the REAL `f.as_expr(*gens)` with the
shadow-selected `gens` (A-reference: real callee left in place):
    if not symbols:                       gens = ring.symbols   -> ok(as_expr(*gens))
    elif len(symbols) != ngens:           -> error
    else:                                 gens = symbols        -> ok(as_expr(*gens))

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 24539
N_RANDOM = 120_000  # >= 1e5


def main():
    from sympy import ring, ZZ, symbols as mk_symbols

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    # A small alphabet of distinct symbol names to draw caller symbols from.
    POOL = list("abcdefghijklmnop")

    def make_ring(ngens):
        names = ",".join(f"x{i}" for i in range(ngens))
        R, *gens = ring(names, ZZ)
        return R, gens

    def random_poly(R, gens, rng):
        # build a small random polynomial in the ring's generators
        f = R.zero
        nterms = rng.randint(1, 4)
        for _ in range(nterms):
            coeff = rng.randint(-5, 5)
            term = R.one * coeff
            for g in gens:
                term = term * g ** rng.randint(0, 3)
            f = f + term
        return f

    def caller_symbols(rng, k):
        # k distinct sympy symbols with fresh names
        names = rng.sample(POOL, k) if k <= len(POOL) else \
            [f"s{i}" for i in range(k)]
        if k == 0:
            return []
        syms = mk_symbols(",".join(names))
        if k == 1:
            return [syms]
        return list(syms)

    def real_outcome(f, syms):
        """('ok', expr) or ('error',) from the REAL patched as_expr."""
        try:
            return ('ok', f.as_expr(*syms))
        except ValueError:
            return ('error',)

    def shadow_outcome(f, R, syms):
        """Shadow of implementation_asExpr; uses the REAL callee for the ok leg
        by calling as_expr with the shadow-selected generator list."""
        if len(syms) == 0:
            gens = list(R.symbols)
        elif len(syms) != R.ngens:
            return ('error',)
        else:
            gens = list(syms)
        # invoke the unchanged callee through the real method on the SAME list
        return ('ok', f.as_expr(*gens))

    def check(f, R, syms):
        nonlocal checked, disagreements
        real = real_outcome(f, syms)
        shadow = shadow_outcome(f, R, syms)
        checked += 1
        ok = (real[0] == shadow[0]) and (
            real[0] == 'error' or real[1] == shadow[1])
        if not ok:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH ngens={R.ngens} k={len(syms)} "
                      f"real={real} shadow={shadow}")

    # deterministic boundary catalogue: the exact issue shape + edge sizes
    R3, g3 = make_ring(3)
    x, y, z = g3
    f_issue = 3 * x ** 2 * y - x * y * z + 7 * z ** 3 + 1
    U, V, W = mk_symbols("u,v,w")
    boundary = [
        (f_issue, R3, []),            # no symbols -> ring symbols
        (f_issue, R3, [U, V, W]),     # correct count -> use caller symbols
        (f_issue, R3, [U]),           # wrong count (too few) -> error
        (f_issue, R3, [U, V]),        # wrong count -> error
        (f_issue, R3, list(mk_symbols("a,b,c,d"))),  # too many -> error
    ]
    for f, R, syms in boundary:
        check(f, R, syms)

    # randomized draws
    for _ in range(N_RANDOM):
        ngens = rng.randint(1, 5)
        R, gens = make_ring(ngens)
        f = random_poly(R, gens, rng)
        # caller list size: 0 (empty), ngens (correct), or a wrong size
        choice = rng.randint(0, 3)
        if choice == 0:
            k = 0
        elif choice == 1:
            k = ngens
        else:
            k = rng.randint(0, ngens + 3)
            if k == ngens:
                k = ngens + 1  # force a wrong size for this branch
        syms = caller_symbols(rng, k)
        check(f, R, syms)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
