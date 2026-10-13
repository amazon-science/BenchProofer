#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-4695.

The bundle models ONE routine: the construction of the underlying label-based
selection call inside `_LocIndexer.__getitem__` (mapping.md). Given the resolved
indexer mapping `key` (a list of (dimension-name, label) pairs), the modeled
output is the argument bundle handed to the selection routine:

    indexers : list[(name, label)]
    method, tolerance, drop : optional label  (None = default / unset)

Post-patch rule (the gold edit replaces `sel(**key)` with `sel(key)`, so the
whole mapping is passed positionally as `indexers` and no optional matching
parameter is ever populated from it):

    indexers = key
    method = tolerance = drop = None

Standing up numpy / the full DataArray machinery to drive the real `.sel` call is
heavy and unnecessary: the modeled value is this pure construction of the call
arguments from the mapping. So the ORACLE below is a faithful in-process replica
of the POST-PATCH construction (`canonicalSelArgs`), and the SHADOW is the
op-for-op transliteration of `implementation_labelSelection` (Solution.lean impl
region), per refinement.md.

This genuinely tests the soundness-critical behavior: a dimension whose name
collides with a reserved matching parameter ("method"/"tolerance"/"drop") must
still be used as an ordinary selector (it stays in `indexers`) and must NOT
populate that optional parameter — matching the F2P expectation
(`da.loc[dict(dim1=..., method=...)]` selects along `method` instead of raising).

stdlib-only. Pinned seed: 4695 (also in mapping.md).
"""
import random
import sys

SEED = 4695
N = 120_000

RESERVED = ("method", "tolerance", "drop")
# Pool of dimension names: reserved collision names + ordinary names.
NAME_POOL = list(RESERVED) + ["dim1", "dim2", "x", "y", "time", "lat", "lon", "z"]
LABELS = ["a", "b", "c", "x", "y", "0", "1"]


# --- ORACLE: faithful in-process replica of the POST-PATCH construction -------
# `sel(key)` -> whole mapping is `indexers`; no optional parameter populated.
def oracle(key):
    return {"indexers": list(key), "method": None, "tolerance": None, "drop": None}


# --- SHADOW of implementation_labelSelection (the R leg) ----------------------
# Mirrors Solution.lean impl region: rebuild indexers from the whole mapping,
# all optional parameters None.
def shadow(key):
    indexers = []
    for entry in key:
        indexers = indexers + [entry]
    return {"indexers": indexers, "method": None, "tolerance": None, "drop": None}


def disagree(key):
    got = oracle(key)
    want = shadow(key)
    if got != want:
        return (key, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P mapping: a dimension literally named "method" must stay a selector.
    cases.append([("dim1", "x"), ("method", "a")])
    cases.append([("dim1", "x"), ("dim2", "a")])           # no collision
    cases.append([("tolerance", "a")])                     # tolerance-named dim
    cases.append([("drop", "b")])                          # drop-named dim
    cases.append([("method", "a"), ("tolerance", "b"), ("drop", "c")])  # all three
    cases.append([])                                       # empty mapping
    cases.append([("x", "0")])                             # single ordinary
    cases.append([("method", "a"), ("method", "b")])       # duplicate name (order kept)
    return cases


def main() -> int:
    checked = 0
    for key in _enumerate_edge():
        d = disagree(key)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} key={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        n = rng.randint(0, 5)
        key = [(rng.choice(NAME_POOL), rng.choice(LABELS)) for _ in range(n)]
        d = disagree(key)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} key={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
