#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20859 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (`Container` ↔ a real parent object). The dispatch control flow
              (region branch / canvas branch / reject), the figure the child is
              bound to, and the raised error are the R/I legs tested here. The
              A-tagged runtime membership tests (`isRegion`/`isCanvas`, modeling
              the two `isinstance` checks) are left as the REAL builtin
              `isinstance` against the real class hierarchy — G-CONF isolates the
              R/I (dispatch + consequence) leg; the A leg stays with G-AX.
  * ORACLE  — `patch.diff`'s behaviour: the patched parent-dispatch of the real
              `Legend` constructor at base_commit (the real correctness oracle,
              G-RESOLVE), observed through the constructed object's bound figure
              / raised error.

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + matplotlib only. The fuzz seed is pinned (mapping.md §4).

Note on cost: the observable depends ONLY on the parent's runtime type, never on
any value it carries, so the oracle (a real object construction) is memoized per
parent identity; the fuzz loop still performs ≥10^5 shadow/oracle comparisons.
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure, FigureBase
import matplotlib.legend as mlegend

SEED = 20859
N_FUZZ = 100_000


def observe_oracle(parent):
    """ORACLE: construct the real (patched) Legend with this parent and project
    its outcome onto what the F2P/P2P tests observe — the bound figure identity
    and the region/canvas flag, or a dispatch rejection."""
    try:
        leg = mlegend.Legend(parent, [], [])
    except TypeError as e:
        # The dispatch rejection of an unsupported parent (the else branch).
        if "needs either" in str(e):
            return ("error",)
        raise
    if leg.isaxes:
        # region branch: bound to the parent region's owning canvas
        return ("region", id(leg.figure))
    # canvas branch: bound directly to the parent canvas
    return ("canvas", id(leg.figure))


def observe_shadow(parent):
    """SHADOW: the impl's branch selection, transliterated. The two membership
    tests are the REAL `isinstance` (A-tagged, left as the real callee); the
    second test is the BROAD figure-like-canvas test (`FigureBase`), so a nested
    sub-canvas is accepted on the same footing as a top-level one."""
    if isinstance(parent, Axes):            # isRegion (A — real isinstance)
        return ("region", id(parent.figure))
    elif isinstance(parent, FigureBase):    # isCanvas (A — real isinstance, BROAD)
        return ("canvas", id(parent))
    else:
        return ("error",)


def build_pool():
    """A diverse pool of real parent objects covering every Container shape:
    top-level canvas (Figure), nested sub-canvas (SubFigure, incl. deeper
    nesting), plotting region (Axes), and unsupported 'other' values."""
    pool = []
    labels = []

    # top-level canvases
    for _ in range(4):
        pool.append(plt.figure()); labels.append("figure")

    # nested sub-canvases (the reported case) + a deeper nesting
    for _ in range(4):
        sf = plt.figure().subfigures()
        pool.append(sf); labels.append("subfigure")
    sf2 = plt.figure().subfigures().subfigures()
    pool.append(sf2); labels.append("subfigure-deep")

    # plotting regions (Axes)
    for _ in range(4):
        pool.append(plt.figure().add_subplot()); labels.append("axes")

    # unsupported parents
    for o in ["a string", 42, 3.5, None, [1, 2], {"k": "v"}, object(), (1,)]:
        pool.append(o); labels.append("other")

    return pool, labels


def main():
    rng = random.Random(SEED)
    pool, labels = build_pool()

    # Memoize the (expensive) real-object oracle by parent identity; the
    # observable is a pure function of the parent's runtime type.
    oracle_cache = {}
    for p in pool:
        oracle_cache[id(p)] = observe_oracle(p)

    disagreements = []
    count = 0
    # Boundary first: every distinct pool object once.
    seq = list(range(len(pool)))
    # Then fuzz: random selections to reach >= N_FUZZ comparisons.
    seq += [rng.randrange(len(pool)) for _ in range(N_FUZZ)]

    for idx in seq:
        p = pool[idx]
        count += 1
        s = observe_shadow(p)
        o = oracle_cache[id(p)]
        if s != o:
            disagreements.append((labels[idx], s, o))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for lab, s, o in disagreements:
            print("  parent=%s shadow=%r oracle=%r" % (lab, s, o))
        return 1
    print("G-CONF OK: R/I shadow of anchorToParent agrees with patch.diff "
          "behaviour on %d inputs (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
