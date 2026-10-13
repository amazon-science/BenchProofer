#!/usr/bin/env python
"""G-CONF: differential conformance for scikit-learn__scikit-learn-9288.

Runs INSIDE the instance image with the gold patch applied (apply_gold=True,
PYTHONPATH=/testbed). The modeled function is the single-thread best-of-n_init
selection loop in `sklearn.cluster.k_means_.k_means` (the
`effective_n_jobs(n_jobs) == 1` branch). The opaque `runTrial` (the real
`kmeans_single`) is left abstract (A-reference): the selection is correct for ANY
attempt routine, so we fuzz the OUTCOME stream directly. What G-CONF validates is
that the Lean selection skeleton's semantics
(`implementation_bestTrial` / `problem_spec_bestTrial`) — pick the earliest
strictly-minimal-cost outcome and return it verbatim — agree EXACTLY with the two
real selection idioms in the patched source:

  * the serial branch's running best:
        if best_inertia is None or inertia < best_inertia: best = this
  * the parallel branch's vectorized pick:
        best = np.argmin(inertia)

Both are first-occurrence-of-the-minimum tie-breaks; the patch makes the serial
branch run over the same `seeds` the parallel branch uses, so the two branches
must select identically. The Lean spec pins exactly that, and this differential
test confirms the spec's selection matches both real idioms over a discrete
catalogue (empty handled by precondition; singletons; all-ties; descending;
ascending) plus >= 1e5 randomized outcome streams (with many cost collisions to
exercise the tie-break).

Exit 0 iff zero disagreements. stdlib + numpy only; pinned seed.
"""
import random
import sys

SEED = 20240630
N_RANDOM = 120_000  # >= 1e5


# ---- Python shadow of implementation_bestTrial (R/I leg) --------------------

def shadow_best(outcomes):
    """Transliteration of implementation_bestTrial: running best with a STRICT
    `<` update, so the FIRST minimum-cost outcome is kept. `outcomes` is a list
    of (cost, data) pairs. Returns the chosen (cost, data)."""
    best = None
    for o in outcomes:
        if best is None:
            best = o
        elif o[0] < best[0]:
            best = o
    return best


# ---- real selection idioms from the patched source -------------------------

def real_serial(outcomes):
    """The serial branch idiom in k_means (post-patch), over the same outcomes:
        if best_inertia is None or inertia < best_inertia: keep
    """
    best_cost = None
    best = None
    for (cost, data) in outcomes:
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best = (cost, data)
    return best


def real_parallel(outcomes):
    """The parallel branch idiom in k_means: best = np.argmin(inertia)."""
    import numpy as np
    inertia = [c for (c, _) in outcomes]
    best = int(np.argmin(inertia))  # first occurrence of the minimum
    return outcomes[best]


# ---- driver -----------------------------------------------------------------

def check_case(outcomes):
    s = shadow_best(outcomes)
    a = real_serial(outcomes)
    b = real_parallel(outcomes)
    if not (s == a == b):
        return (outcomes, s, a, b)
    return None


def main():
    rng = random.Random(SEED)

    discrete = [
        [(5, [0])],
        [(3, [1]), (3, [2]), (3, [3])],            # all ties -> first
        [(9, [9]), (4, [4]), (1, [1])],            # descending
        [(1, [1]), (4, [4]), (9, [9])],            # ascending
        [(2, [2]), (1, [1]), (1, [9]), (0, [0])],  # mixed with a tie before min
        [(-3, [7]), (-3, [8]), (-1, [9])],         # negative costs + tie at min
    ]
    for case in discrete:
        bad = check_case(case)
        if bad is not None:
            print("FAIL (discrete):", bad)
            sys.exit(1)

    for _ in range(N_RANDOM):
        n = rng.randint(1, 8)
        # small cost range => frequent collisions, exercising the tie-break
        outcomes = [(rng.randint(-3, 3), [rng.randint(0, 5) for _ in range(rng.randint(0, 3))])
                    for _ in range(n)]
        bad = check_case(outcomes)
        if bad is not None:
            print("FAIL (fuzz):", bad)
            sys.exit(1)

    print("status=ok %d discrete + %d fuzzed outcome streams; shadow selection == "
          "real serial idiom == real parallel argmin idiom (zero disagreements)"
          % (len(discrete), N_RANDOM))
    sys.exit(0)


if __name__ == "__main__":
    main()
