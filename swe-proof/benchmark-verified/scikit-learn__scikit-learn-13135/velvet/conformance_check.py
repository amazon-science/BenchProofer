#!/usr/bin/env python3
"""G-CONF differential conformance check for scikit-learn__scikit-learn-13135.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region (the deep model
              `asc` + the `mids` fold + the `boundaries` bracketing),
              transliterated to Python over the *real* repo type (a NumPy 1-D
              float array of cluster representatives), via the mapping.md
              bijection (List Rat ↔ ndarray; exact `/2` ↔ float `*0.5`). This is
              an INDEPENDENT transliteration of the Lean defs, not a copy of the
              patch — so a wrong fold / off-by-one / mis-bracketing surfaces as a
              disagreement. The changed reordering op is the A-reference `asc`;
              per the §4.1 convention the A leg is run as the REAL callee
              (`ndarray.sort`) here, its model-soundness being G-AX's job.
  * ORACLE  — patch.diff's behaviour: the exact patched fragment of
              KBinsDiscretizer.fit's kmeans branch that maps the representatives
              and the column endpoints to the bin-edge sequence:
                  centers.sort()
                  bin_edges = (centers[1:] + centers[:-1]) * 0.5
                  bin_edges = np.r_[col_min, bin_edges, col_max]
              (the only lines patch.diff touches; the surrounding KMeans call is
              upstream and unchanged, so the representatives are the input here).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image); NumPy is the repo's
mandatory dependency. The fuzz seed is pinned (mapping.md §4) for a
deterministic verdict.
"""
import random
import sys

import numpy as np

SEED = 13135
N_FUZZ = 100_000


# --- the R/I shadow: Solution.lean asc / mids / boundaries, transliterated ----

def shadow_boundaries(centers, lo, hi):
    """boundaries(centers, lo, hi) of Solution.lean, transliterated.

    asc           -> ndarray.sort (the A-reference real callee)
    mids (fold)    -> adjacent-pair averages, exact `/2` ↔ float `*0.5`
    boundaries     -> [lo] ++ mids ++ [hi]
    """
    c = np.array(centers, dtype=np.float64)
    c.sort()                                          # asc (A-reference callee)
    cl = list(c)
    mids = [(cl[k] + cl[k + 1]) * 0.5 for k in range(len(cl) - 1)]
    return [float(lo)] + mids + [float(hi)]


# --- the oracle: patch.diff's behaviour --------------------------------------

def oracle_boundaries(centers, lo, hi):
    """The patched kmeans-branch fragment, verbatim in NumPy ops."""
    centers = np.array(centers, dtype=np.float64)
    centers.sort()                                    # the line the patch adds
    bin_edges = (centers[1:] + centers[:-1]) * 0.5
    bin_edges = np.r_[lo, bin_edges, hi]
    return [float(x) for x in bin_edges]


def fuzz_inputs(n, rng):
    # boundary cases first
    yield ([], 0.0, 1.0)
    yield ([0.5], 0.0, 1.0)
    yield ([1.0, 2.0], 0.0, 3.0)
    yield ([2.0, 1.0], 0.0, 3.0)                      # reversed reps
    yield ([3.0, 1.0, 2.0], 0.0, 4.0)
    yield ([1.0, 1.0, 1.0], 0.0, 2.0)                 # ties
    yield ([9.5, 0.25, 2.5, 6.0, 1.25], 0.0, 10.0)    # issue reproducer shape
    yield ([-2.0, -5.0, 0.0, 3.0], -6.0, 4.0)
    for _ in range(n):
        m = rng.randint(0, 10)
        centers = [rng.uniform(-1e4, 1e4) for _ in range(m)]
        if m and rng.random() < 0.3:                  # inject ties
            centers[rng.randrange(m)] = rng.choice(centers)
        lo = rng.uniform(-1e4, 1e4)
        hi = rng.uniform(-1e4, 1e4)
        yield (centers, lo, hi)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for centers, lo, hi in fuzz_inputs(N_FUZZ, rng):
        count += 1
        shadow = shadow_boundaries(centers, lo, hi)
        oracle = oracle_boundaries(centers, lo, hi)
        if shadow != oracle:
            disagreements.append((centers, lo, hi, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for centers, lo, hi, sh, orc in disagreements:
            print("  centers=%r lo=%r hi=%r shadow=%r oracle=%r"
                  % (centers, lo, hi, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of computeBoundaries agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
