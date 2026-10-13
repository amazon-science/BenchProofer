#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21847 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo types, via the mapping.md bijection
              (one enumerated candidate `item` ↔ its multiplicity vector
              `List Nat`; `min_degree:int` ↔ `minDeg:Nat`). The keep decision is
              the deep Lean model `selectByDegree` (`minDeg <= totalDegree p`,
              i.e. `min_degree <= sum(multiplicities)`). The UNCHANGED, R/I-shared
              machinery — the candidate enumerator, the per-candidate counting
              loop, `Mul(*item)`, and the final `set(...)` dedup — is reused
              verbatim (it is identical pre/post-patch and folded into the
              `candidates` input). There are NO A-tagged callees, so the shadow
              is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the patched `itermonomials` applied at
              base_commit (the real correctness oracle, G-RESOLVE), called on the
              integer-`max_degrees`/integer-`min_degrees` configuration (the
              total-degree branch the patch edits).

They must agree (as sets of monomials) on every input. Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), sympy + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys
from itertools import combinations_with_replacement, product

from sympy import symbols, Mul, S
from sympy.polys.monomials import itermonomials  # patched oracle (total-degree branch)

SEED = 21847
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean selectByDegree, transliterated ------------
def shadow_select(variables, max_degree, min_degree):
    """The total-degree branch with the Lean model's keep decision: enumerate
    candidates (UNCHANGED itertools machinery), summarise each as its
    multiplicity vector (mapping.md §2), and keep it iff its total degree (the
    SUM of multiplicities — `selectByDegree`/`totalDegree`) is at least
    `min_degree`. Reconstruct kept monomials with the UNCHANGED `Mul`/`set`."""
    if min_degree > max_degree:
        return set()
    if not variables or max_degree == 0:
        return {S.One}
    vars2 = list(variables) + [S.One]
    commutative = all(v.is_commutative for v in variables)
    if commutative:
        enum = combinations_with_replacement(vars2, max_degree)
    else:
        enum = product(vars2, repeat=max_degree)
    kept = []
    for item in enum:
        # per-candidate multiplicity vector: count each non-1 factor.
        powers = {v: 0 for v in vars2}
        for v in item:
            if v != 1:
                powers[v] += 1
        mult_vector = list(powers.values())   # the `List Nat` carrier
        # selectByDegree decision: minDeg <= totalDegree p  (p.sum)
        if min_degree <= sum(mult_vector):
            kept.append(Mul(*item))
    return set(kept)


def oracle_select(variables, max_degree, min_degree):
    """patch.diff's behaviour: the patched itermonomials, integer-degree branch."""
    return set(itermonomials(variables, max_degree, min_degrees=min_degree))


def fuzz_inputs(n, rng):
    # commutative and non-commutative generator pools
    cx, cy, cz = symbols('cx cy cz')
    ni, nj, nk = symbols('ni nj nk', commutative=False)
    comm_pools = [[cx], [cx, cy], [cx, cy, cz]]
    ncomm_pools = [[ni, nj], [ni, nj, nk]]

    # boundary cases first (plan §4.1 step 4): the issue's own examples + edges
    # ([x,y],3,3) and ([x,y],3,2) — the reported-missing total-degree monomials
    yield ([cx, cy], 3, 3)
    yield ([cx, cy], 3, 2)
    yield ([ni, nj, nk], 2, 2)
    yield ([ni, nj, nk], 3, 2)
    yield ([cx, cy, cz], 3, 3)       # the problem_statement's 3-variable example
    yield ([cx], 0, 0)               # max_degree == 0
    yield ([cx, cy], 2, 0)           # min_degree == 0 (keep all)
    yield ([cx, cy], 2, 3)           # min_degree > max_degree (empty)
    yield ([], 3, 0)                 # no variables
    yield ([cx, cy], 1, 1)
    yield ([ni, nj], 0, 0)

    for _ in range(n):
        commutative = rng.random() < 0.5
        pool = rng.choice(comm_pools if commutative else ncomm_pools)
        max_degree = rng.randint(0, 4)
        min_degree = rng.randint(0, 5)
        yield (list(pool), max_degree, min_degree)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for variables, max_degree, min_degree in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_select(variables, max_degree, min_degree)
        oracle = oracle_select(variables, max_degree, min_degree)
        if shadow != oracle:
            disagreements.append((variables, max_degree, min_degree, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for v, mx, mn, sh, orc in disagreements:
            print("  vars=%r max=%r min=%r\n    shadow=%r\n    oracle=%r"
                  % (v, mx, mn, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of selectMonomials agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
