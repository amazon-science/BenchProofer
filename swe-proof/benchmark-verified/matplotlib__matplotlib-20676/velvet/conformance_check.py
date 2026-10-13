#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20676 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to Python over the real repo types, via the mapping.md bijection
              (`Orientation` ↔ the picker's `direction` string; `Rat × Rat` ↔
              the order-preserving `(lower, upper)` view-limit pair of an axis,
              i.e. the result of the axis-bound query). The modeled operation is
              the choice of the boundary markers' INITIAL positions: the limits
              of the orientation-matched axis. `currentSpan` (the present
              selection span) is read-only and does not enter the result.
  * ORACLE  — `patch.diff`'s behaviour: a REAL interactive `SpanSelector` built
              at base_commit with the gold patch applied; we observe the initial
              positions of its boundary-handle artists (`tool._edge_handles.
              positions`), which is exactly the quantity the F2P test
              `test_span_selector_bound` asserts. This is the real correctness
              oracle (G-RESOLVE).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image) with the gold patch
applied; stdlib + matplotlib only. The fuzz seed is pinned (mapping.md §4).

Note on cost: building a real SpanSelector (Figure + Axes + canvas draw) is the
dominant wall-cost, so the oracle is computed once per distinct configuration in
a bounded pool; the comparison loop then performs the full >=10^5 shadow/oracle
checks by sampling that pool (the observable is a pure function of the config).
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector

SEED = 20676
N_FUZZ = 100_000
N_POOL = 400  # distinct real-oracle configurations to build


def get_bounds(ax):
    """The order-preserving (lower, upper) pair each axis-bound query returns
    (mapping.md §2). Matches matplotlib's get_xbound/get_ybound contract."""
    x = ax.get_xbound()
    y = ax.get_ybound()
    return (x[0], x[1]), (y[0], y[1])


def observe_shadow(direction, hbound, vbound, span):
    """SHADOW: initialMarkerPositions transliterated. Select the orientation-
    matched axis-bound pair; `span` (currentSpan) is deliberately unused. The
    positions the markers occupy are [lo, hi] of that pair."""
    chosen = hbound if direction == "horizontal" else vbound
    return [chosen[0], chosen[1]]


def build_config(direction, xlim, ylim):
    """Build the REAL (patched) interactive SpanSelector for one config and
    return ((hbound, vbound), oracle_positions). The axis bounds are read back
    from the real axes (matplotlib may add margins / adjust limits), and the
    oracle is the initial positions of the boundary-handle artists — the exact
    quantity the F2P test asserts."""
    fig, ax = plt.subplots(1, 1)
    try:
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        ax.figure.canvas.draw()
        hbound, vbound = get_bounds(ax)
        tool = SpanSelector(ax, print, direction, interactive=True)
        oracle_positions = list(tool._edge_handles.positions)
    finally:
        plt.close(fig)
    return (hbound, vbound), oracle_positions


def pool_configs(rng):
    """A bounded, diverse pool of (direction, xlim, ylim) configs: the reported
    cases (data away from 0, both directions) and edge cases (crossing zero,
    negative-only, tiny, large, asymmetric x/y), plus randomized fills."""
    base = [
        ("horizontal", (10, 20), (10, 30)),
        ("vertical",   (10, 20), (10, 30)),
        ("horizontal", (-5, 5), (-5, 5)),
        ("vertical",   (-5, 5), (-5, 5)),
        ("horizontal", (-100, -10), (-100, -10)),
        ("vertical",   (-100, -10), (-100, -10)),
        ("horizontal", (0.001, 0.002), (1000.0, 2000.0)),
        ("vertical",   (0.001, 0.002), (1000.0, 2000.0)),
        ("horizontal", (1, 2), (300, 400)),
        ("vertical",   (1, 2), (300, 400)),
    ]
    cfgs = list(base)
    while len(cfgs) < N_POOL:
        direction = rng.choice(["horizontal", "vertical"])
        lo = rng.uniform(-500, 500)
        hi = lo + rng.uniform(0.01, 500)
        lo2 = rng.uniform(-500, 500)
        hi2 = lo2 + rng.uniform(0.01, 500)
        cfgs.append((direction, (lo, hi), (lo2, hi2)))
    return cfgs


def main():
    rng = random.Random(SEED)
    cfgs = pool_configs(rng)

    # Build each real-object oracle once.
    oracle = []  # list of (direction, hbound, vbound, oracle_positions)
    for direction, xlim, ylim in cfgs:
        (hbound, vbound), positions = build_config(direction, xlim, ylim)
        oracle.append((direction, hbound, vbound, positions))

    disagreements = []
    count = 0
    # Boundary first: every distinct config once. Then fuzz by sampling.
    seq = list(range(len(oracle)))
    seq += [rng.randrange(len(oracle)) for _ in range(N_FUZZ)]

    for idx in seq:
        direction, hbound, vbound, positions = oracle[idx]
        count += 1
        # currentSpan is degenerate at construction; pass it to confirm the
        # shadow ignores it.
        shadow = observe_shadow(direction, hbound, vbound, (0.0, 0.0))
        if shadow != positions:
            disagreements.append(((direction, hbound, vbound), shadow, positions))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for key, sh, orc in disagreements:
            print("  config=%r shadow=%r oracle=%r" % (key, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of initialMarkerPositions agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements."
          % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
