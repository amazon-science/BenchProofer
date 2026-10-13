#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-21596 (nagini).

SHADOW: the impl regions of model.py's two modeled functions
(`collect_real_indices`, the aggregate view, and
`collect_real_indices_two_step`, the per-site view), copied verbatim below
with the contract calls (Requires/Ensures/Invariant/Assert) stripped; the
@Pure helpers `contains`/`survives` copy over as plain functions operating on
plain lists (ToSeq becomes the identity on the list carrier). There are no
@ContractOnly callees in this bundle.

ORACLE: the REAL patched repo function per mapping.md section 1 —
`intersection_sets(ImageSet, Reals)` (sympy/sets/handlers/intersection.py),
driven through its public entry `imageset(Lambda(n, f), S.Integers)
.intersect(S.Reals)`. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed resolves the patched module.

Type bridge (mapping.md section 2): index sets map to List[int] over a finite
candidate window (the decision is pointwise, so a window is sound). Per
scenario (an expression f = re + I*im over the integer index n):
  * base  = the window of candidate integer indices (covering every root the
    scenario places, plus margin);
  * keep  = the integer per-factor linear roots of the imaginary part's
    numerator, recomputed from the REAL unchanged callees the fixed routine
    consults (`numer`, `Mul.make_args`, `solve_linear(i, 0, [n])`) — a
    non-integer root contributes no integer index, matching its empty
    integer-membership;
  * drop  = the window indices at which any REAL denominator of f
    (`denoms(f)`) vanishes (linear or not — matching the condition-set
    semantics of the difference site).
The shadow's output index list maps back to real membership: window index k
is in the shadow output iff the real fixed result retains index k, observed
as `result.contains(f(k)) is true` — a full index-level biconditional with no
one-sided masking (an over-kept pole index is caught, not hidden).

Input domain: both Requires demand only three read-only int lists, i.e. any
window/keep/drop triple. Scenarios stay in the modeled regime of mapping.md
section 2.1 (every numerator factor of the imaginary part linear in the
index): im is a product of 1..3 distinct linear factors (integer roots, an
occasional non-integer rational root or constant coefficient), re is drawn
from rational functions of n (plain, scaled, with linear or quadratic
denominators). A scenario whose real per-factor solve is non-linear would be
out of regime and is skipped (none are generated). Boundary scenarios cover
the issue example and the in-scope regression family (pole coinciding with a
kept root -> empty result; non-integer root -> empty; plain multi-root
cases). Per scenario the shadows also run on 3 random sub-windows of base
(distinct Requires-satisfying triples at no extra oracle cost).

>= 1e5 Requires-satisfying inputs: each counted check is one index-level
differential comparison inside one (base, keep, drop) shadow call; scenarios
are generated until the count exceeds 100000. Pinned fuzz seed: 21596.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (sympy is the system under test).
"""
import json
import random
import sys

SEED = 21596
TARGET = 100_000


# --- pure helpers from model.py, contracts stripped ----------------------------

def contains(s, v):
    if len(s) == 0:
        return False
    return s[0] == v or contains(s[1:], v)


def survives(v, keep, drop):
    return contains(keep, v) and not contains(drop, v)


# --- the impl regions of model.py, verbatim, contract calls stripped ----------
# (ToSeq is the identity bridge on the plain-list carrier)

def ToSeq(lst):
    return list(lst)


def collect_real_indices(base, keep, drop):
    result = []
    i = len(base)
    while i > 0:
        c = base[i - 1]
        if survives(c, ToSeq(keep), ToSeq(drop)):
            result = [c] + result
        i = i - 1
    return result


def collect_real_indices_two_step(base, keep, drop):
    # Step 1: intersection with the keep collection (base_set &= keep-roots).
    kept = []
    i = len(base)
    while i > 0:
        c = base[i - 1]
        if contains(ToSeq(keep), c):
            kept = [c] + kept
        i = i - 1

    # Step 2: difference with the drop collection (base_set -= drop-roots),
    # applied to the result of step 1.
    result = []
    j = len(kept)
    while j > 0:
        d = kept[j - 1]
        if not contains(ToSeq(drop), d):
            result = [d] + result
        j = j - 1

    return result


def main():
    sys.path.insert(0, "/testbed")
    from sympy import (S, I, Lambda, Rational, imageset, Mul, Symbol)
    from sympy.simplify.radsimp import numer
    from sympy.solvers.solvers import solve_linear, denoms

    n = Symbol("n")
    WINDOW = list(range(-8, 9))

    checked = [0]
    scenarios = [0]

    def bridge_keep(im):
        """Integer keep indices from the REAL unchanged callees; None if the
        scenario leaves the modeled regime (a non-linear factor)."""
        keep = []
        for fac in Mul.make_args(numer(im)):
            if n not in fac.free_symbols:
                continue
            x, xis = solve_linear(fac, 0, [n])
            if x != n:
                return None  # out of modeled regime
            if xis.is_Integer:
                keep.append(int(xis))
        return keep

    def bridge_drop(f):
        """Window indices at which any REAL denominator of f vanishes."""
        ds = [d for d in denoms(f) if n in d.free_symbols]
        drop = []
        for k in WINDOW:
            for d in ds:
                if d.subs(n, k) == 0:
                    drop.append(k)
                    break
        return drop

    def check_scenario(rng, re_expr, im_expr):
        f = re_expr + I * im_expr
        keep = bridge_keep(im_expr)
        if keep is None:
            return None  # out of modeled regime; not generated in practice
        drop = bridge_drop(f)

        # --- oracle: the REAL fixed intersection --------------------------------
        try:
            res = imageset(Lambda(n, f), S.Integers).intersect(S.Reals)
        except Exception as e:
            return ("DISAGREEMENT f=%s\n  real intersect raised %r" % (f, e))
        real_kept = []
        for k in WINDOW:
            val = f.subs(n, k)
            if res.contains(val) is S.true:
                real_kept.append(k)

        # --- shadows over the full window and 3 sub-windows ---------------------
        bases = [WINDOW]
        for _ in range(3):
            bases.append([k for k in WINDOW if rng.random() < 0.6])
        for base in bases:
            expect = [k for k in real_kept if k in base]
            got1 = collect_real_indices(base, keep, drop)
            got2 = collect_real_indices_two_step(base, keep, drop)
            if got1 != expect or got2 != expect:
                return ("DISAGREEMENT f=%s\n  base=%r keep=%r drop=%r\n"
                        "  shadow aggregate: %r\n  shadow two-step:  %r\n"
                        "  real kept:        %r\n  real result:      %s"
                        % (f, base, keep, drop, got1, got2, expect, res))
            checked[0] += len(base)
        scenarios[0] += 1
        return None

    def run(rng, re_expr, im_expr):
        err = check_scenario(rng, re_expr, im_expr)
        if err:
            print(err)
            sys.exit(1)

    rng = random.Random(SEED)

    # --- boundary scenarios ------------------------------------------------------
    boundary = [
        (n, (n - 1) * (n + 1)),                    # two kept roots
        (n, n * (n - 2)),                          # root at zero
        (1 / (n - 1), (n + 3)),                    # pole away from the root
        (n / (n ** 2 - 9), (n - 3)),               # pole ON the kept root -> empty
        (n, n - Rational(5, 2)),                   # non-integer root -> empty
        (n, Rational(1, 2) * (n - 1) * (n + 3)),   # rational coefficient
        (n, 2 * (n - 4)),                          # integer coefficient factor
        (-n + 1, (n - 1) * (n + 2) * (n - 5)),     # three roots
        (n / ((n - 1) * (n + 2)), (n - 1) * (n + 2)),  # both roots are poles
        (Rational(1, 3), (n - 6)),                 # constant real part
    ]
    for re_e, im_e in boundary:
        run(rng, re_e, im_e)
    n_boundary = len(boundary)

    # --- fuzz scenarios until the differential count exceeds the target ----------
    def rand_im(rng):
        nroots = rng.randint(1, 3)
        roots = rng.sample(range(-6, 7), nroots)
        e = S.One
        for r in roots:
            e = e * (n - r)
        roll = rng.random()
        if roll < 0.15:
            e = e * (n - Rational(rng.choice([1, 3, 5, 7]),
                                  rng.choice([2, 3, 4])))
        if rng.random() < 0.3:
            e = rng.choice([2, -1, 3, Rational(1, 2), Rational(-2, 3)]) * e
        return e

    def rand_re(rng):
        roll = rng.random()
        if roll < 0.25:
            return n
        if roll < 0.35:
            return -n + rng.randint(-3, 3)
        if roll < 0.45:
            return n / rng.choice([2, 3])
        if roll < 0.6:
            return 1 / (n - rng.randint(-6, 6))
        if roll < 0.75:
            d1, d2 = rng.sample(range(-6, 7), 2)
            return n / ((n - d1) * (n - d2))
        if roll < 0.9:
            m = rng.randint(1, 5)
            return n / (n ** 2 - m * m)
        return Rational(rng.randint(-5, 5), rng.choice([1, 2, 3]))

    while checked[0] < TARGET:
        run(rng, rand_re(rng), rand_im(rng))

    print("G-CONF OK: shadow impls == real fixed Reals-intersection on %d "
          "index-level comparisons across %d scenarios (%d boundary, "
          "seed %d)." % (checked[0], scenarios[0], n_boundary, SEED))
    print(json.dumps({"checked": checked[0], "disagreements": 0, "seed": SEED,
                      "scenarios": scenarios[0],
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
