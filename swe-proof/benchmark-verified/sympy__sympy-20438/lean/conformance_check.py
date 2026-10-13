#!/usr/bin/env python3
"""G-CONF — differential test of the R/I shadow of implementation_isSubset
against the patch.diff behaviour (the new ProductSet.is_subset(FiniteSet) path).

The impl region has R/I content (the accumulator `for` loop with boolean-AND
short-circuit over the product's tuples), so this runs a real fuzz. The shadow
reproduces the Lean impl's control flow op-for-op: start acc=True, walk every
tuple of the product, AND in the membership test, return the accumulation. The
enumeration of the product and the membership test are A-tagged (deep-model
references to the real callees), so — per the G-CONF protocol — they are realised
here by the REAL repo callees: iterate the real `ProductSet` and use the real
`FiniteSet.contains`.

The patched side is an independent reconstruction of the POST-patch dispatch:
`fuzzy_and(b_fs.contains(x) for x in a_ps)`. Over the concrete integer domain
every membership is definite, so fuzzy_and is boolean AND; the result is a
definite bool.

We assert zero disagreements over >=10^5 fuzzed (tuple-level) inputs.

sympy-only (runs in-container). exit 0 iff zero disagreements.
"""
import random
import sys

from sympy import FiniteSet, ProductSet
from sympy.core.logic import fuzzy_and

SEED = 20438
N = 120_000           # >= 10^5 product configs (each a full subset-test observation)


def shadow(ps, cand):
    """R/I shadow of implementation_isSubset:
        acc = True                          -- let mut acc := true
        for x in ps:                        -- for x in productSet factors  (A: real ProductSet iter)
            acc = acc and bool(cand.contains(x))  -- acc := acc && candidate.contains x (A: real contains)
        return acc                          -- return acc
    """
    acc = True
    for x in ps:
        acc = acc and bool(cand.contains(x))
    return acc


def patched(ps, cand):
    """Independent reconstruction of the POST-patch dispatch body:
    fuzzy_and(b_fs.contains(x) for x in a_ps). On the concrete domain the
    memberships are definite, so this yields a definite bool."""
    return bool(fuzzy_and(bool(cand.contains(x)) for x in ps))


def rand_case(rng):
    k = rng.randint(1, 3)
    factors = []
    for _ in range(k):
        m = rng.randint(1, 4)
        vals = list({rng.randint(-3, 5) for _ in range(m)})
        if not vals:
            vals = [0]
        factors.append(sorted(vals))
    ps = ProductSet(*[FiniteSet(*f) for f in factors])
    all_t = [tuple(int(c) for c in t) for t in ps]
    # candidate: random subset of product tuples, sometimes plus stray tuples
    take = rng.randint(0, len(all_t))
    members = list({all_t[i] for i in rng.sample(range(len(all_t)), take)}) if all_t else []
    if rng.random() < 0.3:
        arity = len(all_t[0]) if all_t else rng.randint(1, 3)
        members.append(tuple(rng.randint(-9, 12) for _ in range(arity)))
    cand = FiniteSet(*members) if members else FiniteSet()
    return ps, cand


def main() -> int:
    rng = random.Random(SEED)

    a = FiniteSet(1, 2)
    fixed = [
        (ProductSet(a, a), FiniteSet((1, 1), (1, 2), (2, 1), (2, 2))),  # True
        (ProductSet(a, a), FiniteSet(1)),                              # False
        (ProductSet(FiniteSet(1)), FiniteSet((1,))),                   # True
        (ProductSet(FiniteSet(1), FiniteSet(2)), FiniteSet((1, 2))),   # True
        (ProductSet(a), FiniteSet(1)),                                 # True (1-tuples vs scalar)
    ]
    cases = fixed + [rand_case(rng) for _ in range(N)]

    disagreements = 0
    examples = []
    for ps, cand in cases:
        got = shadow(ps, cand)
        want = patched(ps, cand)
        if got != want:
            disagreements += 1
            if len(examples) < 10:
                examples.append((ps, cand, got, want))

    if disagreements:
        print(f"G-CONF FAIL: {disagreements} disagreements")
        for ps, cand, g, w in examples:
            print(f"  ps={ps} cand={cand} shadow={g} patched={w}")
        return 1

    print(f"G-CONF OK: {len(cases)} product configs, 0 disagreements (seed={SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
