#!/usr/bin/env python3
"""G-CONF differential conformance check for pydata__xarray-6744 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the *real* repo carrier. Solution.lean models the
              two per-position index arrays of a 1-d moving-window traversal as
              `List Int`; mapping.md's bijection is `List Int` <-> the integer
              index arrays the traversal builds. The shadow reproduces the impl
              region's integer arithmetic (`endAt` / `beginAt`, with
              `endShift = (w+1)//2` centred else `1`) with plain ints.
  * ORACLE  — `patch.diff`'s behaviour: the patched 1-d moving-window traversal
              applied at base_commit (the real correctness oracle, G-RESOLVE).
              For each position the half-open block [start, stop) that the
              traversal exposes is recovered from the real object and compared
              to the shadow's (begin_i, end_i).

They must agree on every Requires-satisfying input (w > 0). Exit 0 iff zero
disagreements; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), stdlib + numpy +
xarray (already present). The fuzz seed is pinned for a deterministic verdict.
"""
import random
import sys

SEED = 6744
N_FUZZ = 4000


# --- the R/I shadow: Solution.lean endShift/endAt/beginAt, transliterated -----
def shadow_ranges(n, w, center):
    """The impl region's per-position (begin, end) ranges, with plain ints.
    endShift = (w+1)//2 when centred else 1; endAt(i)=i+endShift;
    beginAt(i)=max(0, endAt(i)-w)."""
    shift = (w + 1) // 2 if center else 1
    ends = [i + shift for i in range(n)]
    begins = [(e - w) if (e - w) > 0 else 0 for e in ends]
    return list(zip(begins, ends))


# --- the oracle: the patched 1-d moving-window traversal at base_commit -------
def oracle_ranges(n, w, center):
    """patch.diff's behaviour. Build a length-n DataArray, construct the
    rolling object, iterate, and record the EXACT half-open index range
    [start, stop) the traversal hands to the underlying sequence slicing
    (`self.obj.isel({dim: slice(start, stop)})`), by spying on `isel`
    during the iteration.

    This observes the changed operation (the START/END index arithmetic)
    directly at the modeling boundary of mapping.md §1 — the slice bounds
    themselves, un-truncated and unaffected by the min_periods NaN mask.
    An earlier revision recovered the range by matching the window's
    non-NaN values back to positions; that heuristic cannot recover the
    bounds of a fully-masked window (min_periods = w by default masks any
    right-edge-truncated window), producing spurious disagreements. The
    spy has no such blind spot and is strictly more discriminating: it
    sees stop > n exactly as the traversal computes it."""
    import numpy as np
    import xarray as xr

    vals = np.arange(n, dtype=float) + 1.0
    da = xr.DataArray(vals, dims="x")
    rolling = da.rolling(x=w, center=center)

    recorded = []
    orig_isel = xr.DataArray.isel

    def spy_isel(self, indexers=None, *args, **kwargs):
        if (isinstance(indexers, dict) and set(indexers) == {"x"}
                and isinstance(indexers["x"], slice)):
            s = indexers["x"]
            recorded.append((int(s.start), int(s.stop)))
        return orig_isel(self, indexers, *args, **kwargs)

    xr.DataArray.isel = spy_isel
    try:
        for (label, window) in rolling:
            pass
    finally:
        xr.DataArray.isel = orig_isel
    return recorded


def fuzz_inputs(n_fuzz, rng):
    # boundary cases first: edges + the issue's worked example (n=9,w=3,center)
    for n in (0, 1, 2, 3, 4, 5, 9, 21):
        for w in (1, 2, 3, 7):
            for center in (True, False):
                yield (n, w, center)
    for _ in range(n_fuzz):
        n = rng.randint(0, 30)
        w = rng.randint(1, 30)
        center = rng.random() < 0.5
        yield (n, w, center)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for (n, w, center) in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_ranges(n, w, center)
        oracle = oracle_ranges(n, w, center)
        if shadow != oracle:
            disagreements.append((n, w, center, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for n, w, center, sh, orc in disagreements:
            print("  n=%d w=%d center=%s shadow=%r oracle=%r"
                  % (n, w, center, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of blockEnds/blockBegins agrees with "
          "patch.diff window ranges on %d (n,w,center) inputs (seed=%d), "
          "0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
