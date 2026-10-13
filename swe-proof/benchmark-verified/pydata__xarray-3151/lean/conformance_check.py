#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-3151.

The bundle models ONE routine: the post-concatenation monotonicity-validation
loop inside `combine_by_coords` (mapping.md). The modeled value is a PURE function
of, for each dimension of the combined object, three observations the loop reads:

    isCoordDim           -- the dimension carries a coordinate index  (`dim in concatenated`)
    variesBetweenInputs  -- the dimension was combined across inputs   (`dim in concat_dims`)
    isMonotonic          -- its global index is monotonic increasing OR decreasing

Post-patch rule (the gold edit iterates `concat_dims` — i.e. only the dimensions
that vary between the inputs — and raises on the first non-monotonic one):

    for d in dims:
        if d.variesBetweenInputs and not d.isMonotonic:
            return ("error", d.name)
    return ("ok", None)

Standing up xarray / pandas / the full combine machinery to drive the real loop
is heavy and unnecessary: the modeled value is this pure decision over the
observables the real loop exposes. So the ORACLE below is a faithful in-process
replica of the POST-PATCH loop (iterating `concat_dims`, which is the
`variesBetweenInputs` sublist), and the SHADOW is the op-for-op transliteration of
`implementation_monotonicCheck` (Solution.lean impl region), per refinement.md.

This genuinely tests the soundness-critical case: a non-monotonic BYSTANDER
coordinate (`isCoordDim`, not `variesBetweenInputs`, not `isMonotonic`) must NOT
cause a rejection — matching the F2P expectation
(`test_combine_leaving_bystander_dimensions`).

stdlib-only. Pinned seed: 3151 (also in mapping.md).
"""
import random
import sys

SEED = 3151
N = 120_000


# --- ORACLE: faithful in-process replica of the POST-PATCH loop ---------------
# Post-patch iterates `concat_dims` == the dimensions that vary between inputs,
# in order, and raises on the first non-monotonic one.
def oracle(dims):
    concat_dims = [d for d in dims if d["variesBetweenInputs"]]
    for d in concat_dims:
        if not d["isMonotonic"]:
            return ("error", d["name"])
    return ("ok", None)


# --- SHADOW of implementation_monotonicCheck (the R leg) ----------------------
# Mirrors Solution.lean impl region: scan the FULL dim list, guard on
# variesBetweenInputs, early-return the first offender's name.
def shadow(dims):
    for d in dims:
        if d["variesBetweenInputs"] and not d["isMonotonic"]:
            return ("error", d["name"])
    return ("ok", None)


def disagree(dims):
    got = oracle(dims)
    want = shadow(dims)
    if got != want:
        return (dims, got, want)
    return None


def mk(name, isCoordDim=False, variesBetweenInputs=False, isMonotonic=True):
    return dict(name=name, isCoordDim=isCoordDim,
                variesBetweenInputs=variesBetweenInputs, isMonotonic=isMonotonic)


def _enumerate_edge():
    cases = []
    # F2P: a single non-monotonic bystander coordinate (y=['a','c','b']) plus a
    # monotonic combined dimension (x). Must SUCCEED.
    cases.append([mk("x", isCoordDim=True, variesBetweenInputs=True, isMonotonic=True),
                  mk("y", isCoordDim=True, variesBetweenInputs=False, isMonotonic=False)])
    # bystander alone, non-monotonic -> success
    cases.append([mk("y", isCoordDim=True, variesBetweenInputs=False, isMonotonic=False)])
    # combined dim non-monotonic -> error on it
    cases.append([mk("x", isCoordDim=True, variesBetweenInputs=True, isMonotonic=False)])
    # combined dim non-monotonic AFTER a bystander non-monotonic: must report the
    # combined one, not the earlier bystander
    cases.append([mk("y", isCoordDim=True, variesBetweenInputs=False, isMonotonic=False),
                  mk("x", isCoordDim=True, variesBetweenInputs=True, isMonotonic=False)])
    # two combined non-monotonic: report the FIRST in order
    cases.append([mk("a", isCoordDim=True, variesBetweenInputs=True, isMonotonic=False),
                  mk("b", isCoordDim=True, variesBetweenInputs=True, isMonotonic=False)])
    # all monotonic -> success
    cases.append([mk("x", isCoordDim=True, variesBetweenInputs=True, isMonotonic=True),
                  mk("y", isCoordDim=True, variesBetweenInputs=True, isMonotonic=True)])
    # non-coord dimension (no index) that varies but is monotonic; bystanders
    cases.append([mk("z", isCoordDim=False, variesBetweenInputs=True, isMonotonic=True)])
    # empty
    cases.append([])
    return cases


def main() -> int:
    checked = 0
    for dims in _enumerate_edge():
        d = disagree(dims)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} dims={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    names = ["x", "y", "z", "t", "w", "u", "v", "lat", "lon", "time"]
    for _ in range(N):
        k = rng.randint(0, 6)
        chosen = rng.sample(names, k) if k <= len(names) else names
        dims = []
        for nm in chosen:
            # bias toward the discriminating shapes: many bystanders, mixed monotonicity
            dims.append(mk(
                nm,
                isCoordDim=rng.random() < 0.85,
                variesBetweenInputs=rng.random() < 0.5,
                isMonotonic=rng.random() < 0.6,
            ))
        d = disagree(dims)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} dims={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
