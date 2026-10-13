#!/usr/bin/env python3
"""G-AX — validate the deep-model A-references for sympy__sympy-20438.

The modeled function (the new `is_subset_sets(ProductSet, FiniteSet)` dispatch)
delegates to two UNCHANGED behaviors, both modeled DEEPLY in Solution.lean
(A-references, not consumed axioms):

  (1) iterating a `ProductSet` enumerates the cartesian product of its factors
      -- modeled as `productSet : List (List Int) -> List (List Int)`;
  (2) `FiniteSet.contains(tuple)` on concrete integer tuples is structural tuple
      membership -- modeled as `List.contains` (structural BEq on List Int).

This check runs the REAL repo callees on boundary + fuzzed concrete integer
products and asserts the deep model reproduces them exactly.

Property (1):  set(map(tuple, productSet(factors))) == set(real ProductSet enum)
Property (2):  (model: tuple in candidate_tuples) == bool(b_fs.contains(tuple))
               for every product tuple AND fuzzed non-member tuples.

sympy-only (runs in-container). exit 0 iff the deep model matches the real
callees on every input.
"""
import itertools
import random
import sys

from sympy import FiniteSet, ProductSet

SEED = 20438          # pinned in mapping.md
N = 120_000           # >= 10^5 fuzzed product configs; each expands many tuples


def product_set(factors):
    """Python mirror of Lean `productSet` (front-recursive cartesian product)."""
    if not factors:
        return [[]]
    out = []
    for a in factors[0]:
        for rest in product_set(factors[1:]):
            out.append([a] + rest)
    return out


def rand_factors(rng):
    """A random finite product of finite integer collections (1..3 factors)."""
    k = rng.randint(1, 3)
    factors = []
    for _ in range(k):
        m = rng.randint(1, 4)
        # dedup so the FiniteSet factor has the same cardinality as the list
        vals = list({rng.randint(-3, 5) for _ in range(m)})
        if not vals:
            vals = [0]
        factors.append(sorted(vals))
    return factors


def main() -> int:
    rng = random.Random(SEED)

    fixed = [
        [[1, 2], [1, 2]],          # the F2P case: ProductSet(a, a)
        [[1]],                     # single 1-element factor
        [[1, 2], [3]],
        [[0, 1, 2]],
        [[1, 2, 3], [4, 5]],
    ]
    cases = fixed + [rand_factors(rng) for _ in range(N)]

    enum_mismatch = 0
    contains_mismatch = 0
    examples = []

    for factors in cases:
        sym_factors = [FiniteSet(*f) for f in factors]
        ps = ProductSet(*sym_factors)

        # (1) enumeration: model vs real ProductSet iteration
        model_tuples = {tuple(t) for t in product_set(factors)}
        real_tuples = {tuple(int(c) for c in t) for t in ps}
        if model_tuples != real_tuples:
            enum_mismatch += 1
            if len(examples) < 10:
                examples.append(("enum", factors, model_tuples, real_tuples))
            continue

        # (2) membership: build a candidate FiniteSet of tuples (subset of the
        # product) and check model `in` == real FiniteSet.contains for member
        # and fuzzed non-member tuples.
        all_t = sorted(real_tuples)
        take = rng.randint(0, len(all_t))
        members = set(rng.sample(all_t, take)) if all_t else set()
        cand = FiniteSet(*[tuple(m) for m in members]) if members else FiniteSet()

        probe = set(members)
        # add some non-member integer tuples of the same arities
        for _ in range(3):
            arity = len(all_t[0]) if all_t else rng.randint(1, 3)
            probe.add(tuple(rng.randint(-5, 9) for _ in range(arity)))

        for t in probe:
            model_in = t in members
            real_in = bool(cand.contains(tuple(int(x) for x in t)))
            if model_in != real_in:
                contains_mismatch += 1
                if len(examples) < 10:
                    examples.append(("contains", t, model_in, real_in))

    if enum_mismatch or contains_mismatch:
        print(f"G-AX FAIL: enum_mismatch={enum_mismatch} "
              f"contains_mismatch={contains_mismatch}")
        for ex in examples:
            print("  ", ex)
        return 1

    print(f"G-AX OK: deep model == real ProductSet/FiniteSet callees on "
          f"{len(cases)} product configs (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
