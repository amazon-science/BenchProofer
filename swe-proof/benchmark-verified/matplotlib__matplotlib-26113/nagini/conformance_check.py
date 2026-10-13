#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26113
(nagini).

SHADOW: the impl region of model.py ``populated_bins``, copied VERBATIM below
with only the contract calls (Requires / Ensures / Invariant) stripped. The
@Pure helpers ``decision_count`` and ``decision_agg`` copy over as plain
functions (no sequence shim needed — they are integer predicates) and serve as
an internal cross-check of the executable shadow. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo code the model models per mapping.md section 1 —
the per-bin populated/cleared decision inside ``matplotlib.axes._axes
.Axes.hexbin``. The gate applies patch.diff to /testbed before this script
runs and sets PYTHONPATH so the import resolves to the patched module. Each
model input (an occupancy list plus a threshold) is realized as a concrete
hexbin call: slot ``k`` of a (G+1)x(G+1) first-grid lattice receives
``occupancies[k]`` samples placed exactly at the lattice point
``(k // (G+1) / G, k % (G+1) / G)`` inside ``extent=(0, 1, 0, 1)`` with
``gridsize=(G, G)`` (points at exact lattice coordinates always land in the
first grid; verified by the value read-back below), each sample carrying the
constant payload ``k + 1`` so the surviving bins are identifiable by value as
well as by position. The populated set is observed exactly the way the tested
behaviour observes it: which bins survive into the collection's offsets/array
after the NaN filter. Both regimes are exercised on every input:

  * the value-aggregation regime (``C`` given, ``mincnt`` = the threshold):
    the surviving offsets are lifted back to slot indices and compared
    against the shadow's flag list, and each surviving value must equal the
    slot's constant payload (the default aggregator of a constant list is
    exact), pinning bin identity;
  * the bare-count regime (``C`` absent, same ``mincnt``): the surviving
    offsets are lifted the same way and each surviving value must equal the
    slot's occupancy — this is the cross-regime consistency clause of the
    postcondition (``decision_count``), checked against the real code.

A slice of the inputs is additionally re-run with ``reduce_C_function=sum``
to confirm the populated decision is aggregator-independent on the modeled
domain (occupancies observed only through the threshold comparison).

TYPE BRIDGE (mapping.md section 2): a per-hexagon accumulated value list
``acc`` <-> its occupancy ``len(acc)`` (realized here by placing exactly
``occupancies[k]`` samples in slot ``k``); the positive ``mincnt`` <->
``threshold`` (identity; the precondition ``threshold >= 1`` matches the
documented ``mincnt : int > 0`` regime, so every generated threshold is a
positive int); a bin's real-valued entry vs the missing marker <-> the bool
populated-flag, observed through which bins survive the NaN filter. Slots
beyond ``len(occupancies)`` and all second-lattice bins receive zero samples
and, on the modeled domain, must never survive; an oracle offset that lifts
to no populated first-lattice slot is itself a disagreement.

INPUT PLAN (>= 1e5 Requires-satisfying inputs — the precondition demands a
readable occupancy list and ``threshold >= 1``, so every list of non-negative
ints with a positive int threshold qualifies): hand-picked boundary cases
(empty list, all-zero, singletons, occupancy == threshold exactly, +/-1
neighbourhoods, thresholds far above every occupancy, full grids), an
exhaustive tier (every occupancy pattern of lengths 1..4 over {0,1,2,3}
crossed with thresholds 1..4), and 100000 random fuzz inputs over grid sizes
1..5 with an occupancy distribution concentrated on the threshold boundary
(occ in [t-2, t+2] with high probability). Pinned fuzz seed: 26113 (the
instance number).

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo's own numpy/matplotlib only.
"""
import json
import os
import random
import sys

os.environ.setdefault("MPLBACKEND", "Agg")

SEED = 26113
N_FUZZ = 100000

import numpy as np                  # noqa: E402
import matplotlib                   # noqa: E402
matplotlib.use("Agg")
from matplotlib.figure import Figure  # noqa: E402


# --- pure region of model.py, contracts stripped ------------------------------

def decision_count(occ, t):
    """Per-bin populated decision in the bare-count regime: a bin with the
    given occupancy is populated unless its occupancy falls below the
    threshold.  (i.e. populated iff occ >= t.)"""
    return not (occ < t)


def decision_agg(occ, t):
    """Per-bin populated decision in the value-aggregation regime: a bin is
    populated iff its occupancy reaches the threshold."""
    return occ >= t


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def populated_bins(occupancies, threshold):
    result = []  # type: List[bool]
    i = 0
    while i < len(occupancies):
        occ = occupancies[i]
        flag = occ >= threshold
        result.append(flag)
        i = i + 1
    return result


# --- oracle: the real patched Axes.hexbin per-bin decision ---------------------

_FIG = Figure()
_AX = _FIG.add_subplot()


def realize(occ, G):
    """Lower an occupancy list to concrete samples: slot k of the first
    (G+1)x(G+1) lattice gets occ[k] samples at the exact lattice point, each
    carrying the constant payload k + 1 (so the slot is value-identifiable)."""
    ny1 = G + 1
    xs, ys, cs = [], [], []
    for k, o in enumerate(occ):
        i, j = k // ny1, k % ny1
        for _ in range(o):
            xs.append(i / G)
            ys.append(j / G)
            cs.append(float(k + 1))
    return xs, ys, cs


def kept_slots(hb, G, n_slots):
    """Lift the surviving collection back to {slot index: value}. Returns
    (dict, None) or (None, error string) when an offset lifts to no
    first-lattice slot in range (itself a disagreement with the shadow, whose
    out-of-list / second-lattice bins are all cleared on the modeled domain)."""
    ny1 = G + 1
    offs = np.asarray(hb.get_offsets(), float).reshape(-1, 2)
    vals = np.asarray(hb.get_array(), float).reshape(-1)
    kept = {}
    for (x, y), v in zip(offs, vals):
        fi, fj = x * G, y * G
        i, j = int(round(fi)), int(round(fj))
        if abs(fi - i) > 1e-6 or abs(fj - j) > 1e-6:
            return None, ("surviving bin at offset (%r, %r) lifts to no "
                          "first-lattice slot" % (x, y))
        k = i * ny1 + j
        if not (0 <= k < n_slots):
            return None, ("surviving bin at offset (%r, %r) lifts to slot %d "
                          "outside the occupancy list (an empty bin survived)"
                          % (x, y, k))
        if k in kept:
            return None, "slot %d survived twice" % k
        kept[k] = float(v)
    return kept, None


def run_hexbin(xs, ys, cs, G, t, reduce_fn=None):
    """One real hexbin call; returns the collection (removed by the caller
    via .remove() indirectly -- we remove it here after reading)."""
    kw = {}
    if cs is not None:
        kw["C"] = cs
    if reduce_fn is not None:
        kw["reduce_C_function"] = reduce_fn
    hb = _AX.hexbin(xs, ys, gridsize=(G, G), extent=(0, 1, 0, 1),
                    mincnt=t, **kw)
    return hb


# --- differential driver -------------------------------------------------------

def check(occ, t, G, with_sum=False):
    """Run shadow and oracle (both regimes) on one (occupancies, threshold)
    input; return an error string on disagreement, else None."""
    occ = list(occ)
    shadow = populated_bins(occ, t)

    # internal cross-check: the executable impl agrees with the pure helpers
    for k in range(len(occ)):
        if shadow[k] != decision_agg(occ[k], t) or \
                shadow[k] != decision_count(occ[k], t):
            return ("INTERNAL: impl region and pure helpers disagree at slot "
                    "%d of occ=%r, t=%r: shadow %r, decision_agg %r, "
                    "decision_count %r"
                    % (k, occ, t, shadow[k], decision_agg(occ[k], t),
                       decision_count(occ[k], t)))

    expected = {k: occ[k] for k in range(len(occ)) if shadow[k]}
    xs, ys, cs = realize(occ, G)

    regimes = [("value-aggregation (C given)", cs, None,
                {k: float(k + 1) for k in expected}),
               ("bare-count (C absent)", None, None,
                {k: float(occ[k]) for k in expected})]
    if with_sum:
        regimes.append(("value-aggregation (C given, sum aggregator)", cs,
                        sum, {k: float((k + 1) * occ[k]) for k in expected}))

    for regime, c_arg, reduce_fn, want_vals in regimes:
        hb = run_hexbin(xs, ys, c_arg, G, t, reduce_fn)
        kept, err = kept_slots(hb, G, len(occ))
        hb.remove()
        if err:
            return ("DISAGREEMENT (%s) on occ=%r, t=%r, G=%d:\n"
                    "  shadow (impl region) populated slots = %r\n"
                    "  real (patched hexbin): %s"
                    % (regime, occ, t, G, sorted(expected), err))
        if set(kept) != set(expected):
            return ("DISAGREEMENT (%s) on occ=%r, t=%r, G=%d:\n"
                    "  shadow (impl region) populated slots = %r\n"
                    "  real (patched hexbin) surviving slots = %r"
                    % (regime, occ, t, G, sorted(expected), sorted(kept)))
        for k, v in kept.items():
            if v != want_vals[k]:
                return ("DISAGREEMENT (%s) on occ=%r, t=%r, G=%d:\n"
                        "  slot %d survived with value %r, expected %r "
                        "(bin identity / payload mismatch)"
                        % (regime, occ, t, G, k, v, want_vals[k]))
    return None


def grid_for(n):
    """Smallest G in 1..5 whose first lattice has at least n slots."""
    G = 1
    while (G + 1) ** 2 < n and G < 5:
        G += 1
    return G


def boundary_cases():
    """Hand-picked (occupancies, threshold) boundary inputs."""
    cases = [
        ([], 1), ([], 7),
        ([0], 1), ([1], 1), ([2], 1),
        ([0, 0, 0], 1), ([0, 0, 0, 0], 5),
        ([1, 1, 1], 1),
        ([1, 0, 1, 2], 1),
    ]
    # occupancy exactly at / around the threshold, thresholds 1..10
    for t in range(1, 11):
        cases.append(([t], t))
        if t >= 1:
            cases.append(([t - 1], t))
        cases.append(([t + 1], t))
        cases.append(([max(t - 1, 0), t, t + 1, 0], t))
    # thresholds far above every occupancy
    cases += [([3, 5], 50), ([1, 2, 3], 17), ([10, 10], 11)]
    # occupancies far above the threshold
    cases += [([40, 0, 40], 1), ([25, 24, 26], 25)]
    # full first lattice, G = 5 (36 slots), mixed pattern
    full = [(k * 7) % 5 for k in range(36)]
    cases += [(full, 1), (full, 2), (full, 3), (full, 4), (full, 5)]
    # long all-populated / all-cleared grids
    cases += [([2] * 36, 2), ([1] * 36, 2), ([3] * 36, 2)]
    return cases


def main():
    checked = 0

    def run_one(occ, t, with_sum=False):
        nonlocal checked
        G = grid_for(len(occ))
        err = check(occ, t, G, with_sum=with_sum)
        if err:
            print(err)
            sys.exit(1)
        checked += 1

    # 1) hand-picked boundary inputs (all also on the sum-aggregator tier)
    boundary = boundary_cases()
    for occ, t in boundary:
        run_one(occ, t, with_sum=True)

    # 2) exhaustive tier: every occupancy pattern of lengths 1..4 over
    #    {0,1,2,3}, crossed with thresholds 1..4
    n_exhaustive = 0
    for n in range(1, 5):
        for code in range(4 ** n):
            occ, c = [], code
            for _ in range(n):
                occ.append(c % 4)
                c //= 4
            for t in range(1, 5):
                run_one(occ, t)
                n_exhaustive += 1

    # 3) randomized fuzz: grid sizes 1..5, occupancies concentrated on the
    #    threshold boundary, occasional large thresholds and sparse patterns
    #    (pinned seed); ~5% of inputs also on the sum-aggregator tier
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        G = rng.randint(1, 5)
        n_slots = (G + 1) ** 2
        n = rng.randint(0, n_slots)
        if rng.random() < 0.05:
            t = rng.randint(9, 60)
        else:
            t = rng.randint(1, 8)
        occ = []
        budget = 200
        for _ in range(n):
            if rng.random() < 0.6:
                o = max(0, t + rng.randint(-2, 2))
            else:
                o = rng.randint(0, 6)
            o = min(o, budget)
            budget -= o
            occ.append(o)
        run_one(occ, t, with_sum=(rng.random() < 0.05))

    print("G-CONF OK: shadow impl == real patched hexbin per-bin decision on "
          "%d inputs (%d boundary + %d exhaustive + %d fuzz, seed %d), each "
          "checked in BOTH regimes (value-aggregation and bare-count) plus a "
          "sum-aggregator slice; 0 disagreements."
          % (checked, len(boundary), n_exhaustive, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; no "
                                "@ContractOnly callees; pure helpers as "
                                "internal cross-check)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
