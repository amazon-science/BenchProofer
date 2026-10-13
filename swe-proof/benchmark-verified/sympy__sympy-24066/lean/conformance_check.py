#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for sympy__sympy-24066.

The bundle models ONE routine: the `Function` branch of
`UnitSystem._collect_factor_and_dimension`. Given the per-argument
(scale_factor, dimension) pairs `fds` (produced by the unchanged recursive
collection), it returns the function rebuilt on the scale factors together with
the per-argument dimensions, each normalised to the unit dimension when the
dimension system regards it as dimensionless.

The soundness-critical decision the patch changes is WHICH dimension each
argument contributes:

    post-patch:  Dimension(1) if is_dimensionless(d) else d
    pre-patch:   d                                      (raw, no canonicalisation)

The dimensionless query `is_dimensionless` and the function reconstruction
`expr.func(*scale_factors)` are UNCHANGED callees; they appear identically in the
oracle and the shadow, so they cancel out and this differential test isolates
exactly the R leg — the per-argument canonicalisation.

A `Dim` is modeled as a pair `(is_dimensionless: bool, tag: int)`: the boolean is
exactly what `is_dimensionless` returns, and the tag distinguishes distinct
dimension expressions (so a dimensionless-but-non-unit dimension, tag != UNIT, is
a real, observable input — the F2P scenario). `UNIT` is the tag of `Dimension(1)`.

ORACLE = faithful in-process replica of the POST-PATCH branch. SHADOW =
op-for-op transliteration of `implementation_collectFunction` (Solution.lean
impl region), per refinement.md.

stdlib-only. Pinned seed: 24066 (also in mapping.md).
"""
import random
import sys

SEED = 24066
N = 120_000

# The unit dimension Dimension(1): dimensionless, canonical tag 0.
UNIT = (True, 0)


def is_dimensionless(dim):
    # Unchanged callee model: byte-identical between oracle and shadow.
    return dim[0]


def apply_func(func, scale_factors):
    # Unchanged callee model: the reconstruction expr.func(*scale_factors).
    return (func, tuple(scale_factors))


# --- ORACLE: faithful replica of the POST-PATCH Function branch ---------------
def oracle(func, fds):
    factor = apply_func(func, [f for (f, d) in fds])
    dims = [UNIT if is_dimensionless(d) else d for (f, d) in fds]
    return (factor, dims)


# --- SHADOW of implementation_collectFunction (the R leg) ---------------------
# Mirrors Solution.lean impl region exactly: accumulate per-argument dimensions
# with the dimensionless canonicalisation, then build the result.
def shadow(func, fds):
    dims = []
    for (f, d) in fds:
        if is_dimensionless(d):
            dims = dims + [UNIT]
        else:
            dims = dims + [d]
    factor = apply_func(func, [f for (f, d) in fds])
    return (factor, dims)


def disagree(func, fds):
    got = oracle(func, fds)
    want = shadow(func, fds)
    if got != want:
        return (func, fds, got, want)
    return None


FUNCS = [1, 2, 3]            # opaque function-head tags
FACTORS = [1, 2, 5, 7, 11]   # opaque scale-factor tags


def _edge_cases():
    cases = []
    # F2P scenario: a single dimensionless-but-NON-unit argument dimension
    # (tag != 0) -> must canonicalise to the unit dimension.
    cases.append((1, [(3, (True, 9))]))
    # already the unit dimension -> stays the unit dimension.
    cases.append((1, [(3, UNIT)]))
    # a genuinely dimensioned argument -> left unchanged.
    cases.append((2, [(5, (False, 4))]))
    # mixed: dimensionless-non-unit, dimensioned, unit.
    cases.append((2, [(1, (True, 7)), (2, (False, 3)), (5, UNIT)]))
    # empty argument list.
    cases.append((3, []))
    # two dimensionless-non-unit dims with DIFFERENT tags -> both -> unit.
    cases.append((1, [(2, (True, 5)), (7, (True, 8))]))
    return cases


def _rand_dim(rng):
    dimless = rng.random() < 0.5
    if dimless:
        # dimensionless: sometimes the canonical unit, sometimes a non-unit tag.
        tag = rng.choice([0, 0, 1, 2, 3, 9, 17])
        return (True, tag)
    return (False, rng.randint(1, 20))


def _rand_case(rng):
    func = rng.choice(FUNCS)
    nargs = rng.randint(0, 5)
    fds = [(rng.choice(FACTORS), _rand_dim(rng)) for _ in range(nargs)]
    return func, fds


def main() -> int:
    checked = 0
    for func, fds in _edge_cases():
        d = disagree(func, fds)
        if d:
            print(f"DISAGREE edge: oracle={d[2]} shadow={d[3]} fds={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        func, fds = _rand_case(rng)
        d = disagree(func, fds)
        if d:
            print(f"DISAGREE fuzz: oracle={d[2]} shadow={d[3]} fds={d[1]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
