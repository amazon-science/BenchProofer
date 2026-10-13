#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pydata__xarray-7233.

The bundle models ONE observable: the set of names re-promoted to coordinates of
the reshaped result inside `Coarsen.construct` — the `should_be_coords` argument
handed to `set_coords` (mapping.md). It is a PURE function of two name
collections the code reads:

* `set(window_dim)`  — the names of the dimensions being reshaped, and
* `set(self.obj.coords)` — the names that were coordinates of the input.

Standing up the full xarray Dataset/Coarsen machinery to drive the real method is
heavy and unnecessary: the modeled value depends only on those two name sets. So
the ORACLE below is a faithful in-process replica of the POST-PATCH expression
`(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)`, and the SHADOW
is the op-for-op transliteration of `implementation_retainedCoordNames`
(Solution.lean impl region: `filter` then `++`), per refinement.md.

Both sides are compared AS SETS (mapping.md: `should_be_coords` is a `set[str]`;
order and multiplicity carry no downstream meaning because `set_coords` consumes
a set).

This genuinely tests the soundness-critical clause: a prior coordinate name that
is NOT itself a reshaped dimension (a non-dimensional coordinate, e.g. `day`)
must remain in the coordinate set — exactly the F2P scenario.

stdlib-only. Pinned seed: 7233 (also in mapping.md).
"""
import random
import sys

SEED = 7233
N = 120_000

NAME_POOL = ["time", "x", "y", "year", "month", "day", "lat", "lon", "z"]


# --- ORACLE: faithful in-process replica of the POST-PATCH expression ---------
def oracle(inp):
    window_dim = inp["reshapedDims"]
    coords = inp["priorCoordNames"]
    should_be_coords = (set(window_dim) & set(coords)) | set(coords)
    return should_be_coords


# --- SHADOW of implementation_retainedCoordNames (the R legs) -----------------
# Mirrors Solution.lean impl region exactly: filter (the common names) then ++.
def shadow(inp):
    reshaped_dims = inp["reshapedDims"]
    prior_coord_names = inp["priorCoordNames"]
    common = [d for d in reshaped_dims if d in prior_coord_names]  # .filter (· ∈ ·)
    result = common + prior_coord_names                            # ++
    return set(result)  # compared as a set (membership), per mapping.md


def disagree(inp):
    got = oracle(inp)
    want = shadow(inp)
    if got != want:
        return (inp, got, want)
    return None


def _enumerate_edge():
    cases = []
    # F2P: a non-dimensional coordinate (`day`) must stay a coordinate even though
    # it is not the reshaped dimension (`time`).
    cases.append(dict(reshapedDims=["time"], priorCoordNames=["day"]))
    # the reshaped dim is itself a coordinate AND there is a non-dim coordinate
    cases.append(dict(reshapedDims=["time"], priorCoordNames=["time", "day"]))
    # no prior coordinates -> empty result
    cases.append(dict(reshapedDims=["time", "x"], priorCoordNames=[]))
    # disjoint: reshaped dims none of which are coordinates
    cases.append(dict(reshapedDims=["x", "y"], priorCoordNames=["day", "lat"]))
    # reshaped dim equals the only coordinate
    cases.append(dict(reshapedDims=["time"], priorCoordNames=["time"]))
    # multiple reshaped dims, multiple coords, partial overlap
    cases.append(dict(reshapedDims=["time", "x"], priorCoordNames=["time", "day", "lat"]))
    # no reshaped dims at all
    cases.append(dict(reshapedDims=[], priorCoordNames=["day", "lat"]))
    return cases


def _rand_names(rng, n):
    return [rng.choice(NAME_POOL) for _ in range(n)]


def main() -> int:
    checked = 0
    for inp in _enumerate_edge():
        d = disagree(inp)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N):
        reshaped_dims = _rand_names(rng, rng.randint(0, 4))
        prior_coords = _rand_names(rng, rng.randint(0, 5))
        inp = dict(reshapedDims=reshaped_dims, priorCoordNames=prior_coords)
        d = disagree(inp)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} inp={d[0]}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
