#!/usr/bin/env python
"""G-CONF: differential conformance for sympy__sympy-21847.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). Builds the Python shadow of the Lean
`implementation_selectMonomials` skeleton — the per-candidate acceptance filter
that keeps a candidate monomial iff its TOTAL degree (`sum` of the exponent
vector) is at least `min_degree` — and diffs the resulting set of monomials
against the REAL patched `itermonomials(variables, max_degree, min_degree)` over
a boundary catalogue plus >=1e5 randomized draws, in BOTH the commutative and
non-commutative configurations (the two byte-identical patched sub-branches).

  observable: `set(itermonomials(variables, max_degree, min_degree))` for an
  integer `max_degree`/`min_degree` and a list of symbolic `variables`.

Shadow (transliteration of implementation_selectMonomials): mirror the real
candidate enumeration exactly — `combinations_with_replacement(variables+[1],
max_degree)` for commutative variables, `product(variables+[1], repeat=
max_degree)` for non-commutative — tally each candidate's per-variable exponents
into a vector, KEEP the candidate iff `sum(exponents) >= min_degree`, build
`Mul(*item)` for the kept candidates, and dedup with `set(...)`. The ONLY logic
that differs from the (unchanged) repo enumeration is the accept predicate; we
also replicate the early outs (`min_degree > max_degree` -> empty;
`not variables or max_degree == 0` -> {S.One}).

Exit 0 iff zero disagreements. stdlib-only fuzzing (pinned seed).
"""
import random
import sys

SEED = 21847
N_RANDOM = 120_000  # >= 1e5


def main():
    from itertools import combinations_with_replacement, product
    from sympy import symbols as mk_symbols, Mul, S
    from sympy.polys.monomials import itermonomials

    rng = random.Random(SEED)
    disagreements = 0
    checked = 0

    def shadow(variables, max_degree, min_degree):
        """Shadow of implementation_selectMonomials, replicating the real
        integer-branch enumeration but with the sum (total-degree) accept test."""
        # early outs (unchanged context, lines 113-118 of monomials.py)
        if min_degree > max_degree:
            return set()
        if not variables or max_degree == 0:
            return {S.One}
        vs = list(variables) + [S.One]
        commutative = all(v.is_commutative for v in vs)
        enumerator = (combinations_with_replacement(vs, max_degree)
                      if commutative else product(vs, repeat=max_degree))
        kept = []
        for item in enumerator:
            powers = dict()
            for v in vs:
                powers[v] = 0
            for v in item:
                if v != 1:
                    powers[v] += 1
            # THE MODELED PREDICATE: total degree (sum) reaches the threshold
            if sum(powers.values()) >= min_degree:
                kept.append(Mul(*item))
        return set(kept)

    def real(variables, max_degree, min_degree):
        return set(itermonomials(variables, max_degree, min_degrees=min_degree))

    def check(variables, max_degree, min_degree):
        nonlocal checked, disagreements
        r = real(variables, max_degree, min_degree)
        s = shadow(variables, max_degree, min_degree)
        checked += 1
        if r != s:
            disagreements += 1
            if disagreements <= 5:
                print(f"MISMATCH nvars={len(variables)} max={max_degree} "
                      f"min={min_degree} real-shadow={r - s} shadow-real={s - r}")

    # symbol pools: commutative and non-commutative
    comm = list(mk_symbols("x1:7"))                      # x1..x6, commutative
    ncomm = list(mk_symbols("a1:7", commutative=False))  # a1..a6, non-commutative

    # deterministic boundary catalogue (incl. the issue's shape)
    x, y = comm[0], comm[1]
    i, j, k = ncomm[0], ncomm[1], ncomm[2]
    boundary = [
        ([x, y], 3, 3),     # issue: degree-3 monomials with spread degree
        ([x, y], 3, 2),     # F2P: x*y (max exp 1) must survive on total deg 2
        ([x, y, comm[2]], 3, 3),  # x1,x2,x3 issue example
        ([x], 3, 1),
        ([x], 3, 2),
        ([x, y], 0, 0),
        ([x, y], 2, 0),
        ([x, y], 2, 2),
        ([], 3, 0),         # no variables -> {S.One}
        ([x, y], 0, 0),
        ([x, y], 2, 3),     # min > max -> empty
        ([i, j, k], 2, 2),  # non-commutative issue example
        ([i, j, k], 3, 2),  # non-commutative issue example
        ([i, j], 2, 1),
        ([i], 3, 2),
    ]
    for variables, mx, mn in boundary:
        check(variables, mx, mn)

    # randomized draws over both configurations
    for _ in range(N_RANDOM):
        commutative = rng.random() < 0.5
        pool = comm if commutative else ncomm
        nvars = rng.randint(1, 4)
        variables = pool[:nvars]
        max_degree = rng.randint(0, 4)
        # draw min_degree across the full validated range [0, max_degree] plus a
        # few values above max_degree (the min>max early-out path)
        min_degree = rng.randint(0, max_degree + 1)
        check(variables, max_degree, min_degree)

    print(f"checked={checked} disagreements={disagreements}")
    if disagreements == 0:
        print(f"status=pass conformance OK ({checked} checks, 0 disagreements)")
        return 0
    print(f"status=fail {disagreements} disagreement(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
