#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-22865
(nagini).

SHADOW: the impl region of model.py's `drawn_separators`, copied verbatim
below with the contract calls (the Invariant block) stripped.  The @Pure
helpers `start_index` / `end_index` copy over as plain functions and are kept
as a redundant internal cross-check of the loop's output.  There is no
@ContractOnly callee.

ORACLE: the REAL patched repo method the model models per mapping.md --
`matplotlib.colorbar.Colorbar._add_solids` (the divider-segment selection it
performs when `drawedges` is true) -- invoked on live Agg colorbars.  The
gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable.  The observation is
`cbar.dividers.get_segments()`: the list of divider segments the collection
reports back, exactly what the repo tests read.

Type bridge (mapping.md section 2): the repo's candidate-segment array
`np.dstack([X, Y])` has shape (n, 2, 2); row i is fully identified by its
first-axis position, so the model carries a `List[int]` of position ids
0..n-1.  Per trial the shadow runs on those ids and its kept ids decode back
through the candidate array: kept id k must match the observed segment row
for row k of `np.dstack([X, Y])`, compared element-exactly.  The model's two
booleans are read from the live object's real unchanged predicates
`_extend_lower()` / `_extend_upper()` at call time.  `set_segments` /
`get_segments` is the identity on the stored segment content.

Input domain: Requires demands len(segments) >= 2, i.e. a candidate mesh of
at least two rows; both booleans are unconstrained.  Fuzzing drives every
(orientation, extend-mode, long-axis inversion) combination -- which covers
all four (lower_open, upper_open) boolean pairs -- with random mesh sizes
n in [2, 40] and random finite float coordinates (mixed magnitudes, signs,
integer-valued and tiny values), calling the real method directly per trial.
Boundary coverage additionally runs full end-to-end colorbar constructions
(a recorder captures the real X, Y handed to the method by the drawing
pipeline) over all extend modes, both orientations, and several boundary
counts, including the minimal ones.

>= 1e5 Requires-satisfying inputs: boundary end-to-end constructions +
100000 direct fuzz trials.  Pinned fuzz seed: 22865.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1.  stdlib + numpy + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.cm import ScalarMappable
from matplotlib.colorbar import Colorbar          # REAL patched repo class
from matplotlib.colors import BoundaryNorm, Normalize

SEED = 22865
N_FUZZ = 100_000


# --- pure region of model.py, contracts stripped ------------------------------

def start_index(lower_open):
    if lower_open:
        return 0
    return 1


def end_index(upper_open, n):
    if upper_open:
        return n
    return n - 1


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def drawn_separators(segments, lower_open, upper_open):
    start = 0 if lower_open else 1
    end = len(segments) if upper_open else len(segments) - 1
    result = []  # type: List[int]
    i = start
    while i < end:
        # (Invariant(...) contract calls stripped here)
        result.append(segments[i])
        i = i + 1
    return result


def run_shadow(n, lower_open, upper_open):
    """Run the shadow on the position-id carrier for an n-row candidate mesh
    and cross-check it against the pure-region helpers."""
    kept = drawn_separators(list(range(n)), lower_open, upper_open)
    s, e = start_index(lower_open), end_index(upper_open, n)
    assert len(kept) == e - s and all(kept[j] == s + j for j in range(len(kept)))
    return kept


# --- comparison ----------------------------------------------------------------

def compare(observed_segments, X, Y, lower_open, upper_open, ctx):
    """Diff the real observed divider segments against the shadow's kept run
    decoded through the candidate array.  Returns an error string or None."""
    candidates = np.dstack([X, Y])           # (n, 2, 2) candidate rows
    n = len(candidates)
    kept_ids = run_shadow(n, lower_open, upper_open)
    obs = [np.asarray(s) for s in observed_segments]
    ok = (len(obs) == len(kept_ids) and
          all(obs[j].shape == candidates[k].shape and
              np.array_equal(obs[j], candidates[k])
              for j, k in enumerate(kept_ids)))
    if ok:
        return None
    return ("DISAGREEMENT\n  %s\n  n=%d lower_open=%r upper_open=%r\n"
            "  shadow kept ids=%r\n  shadow kept rows=%r\n  real=%r"
            % (ctx, n, lower_open, upper_open, kept_ids,
               [candidates[k].tolist() for k in kept_ids],
               [o.tolist() for o in obs]))


# --- oracle plumbing: direct per-trial invocation --------------------------------

class Driver:
    """One live colorbar per (orientation, extend, inverted) configuration.
    Each trial hands the real method a fresh fuzzed coordinate mesh and reads
    the divider segments the collection then reports."""

    def __init__(self, orientation, extend, inverted):
        self.orientation = orientation
        self.extend = extend
        self.inverted = inverted
        self.fig, ax = plt.subplots()
        sm = ScalarMappable(norm=Normalize(0, 1), cmap="viridis")
        self.cbar = self.fig.colorbar(sm, ax=ax, orientation=orientation,
                                      extend=extend, drawedges=True)
        if inverted:
            if orientation == "vertical":
                self.cbar.ax.set_ylim(*self.cbar.ax.get_ylim()[::-1])
            else:
                self.cbar.ax.set_xlim(*self.cbar.ax.get_xlim()[::-1])

    def trial(self, X, Y):
        n = len(X)
        C = np.full((n - 1, 1), 0.5)
        self.cbar._add_solids(X, Y, C)        # REAL patched method
        observed = self.cbar.dividers.get_segments()
        lower_open = self.cbar._extend_lower()   # real unchanged predicates
        upper_open = self.cbar._extend_upper()
        ctx = ("direct orientation=%r extend=%r inverted=%r\n  X=%r\n  Y=%r"
               % (self.orientation, self.extend, self.inverted,
                  X.tolist(), Y.tolist()))
        return compare(observed, X, Y, lower_open, upper_open, ctx)

    def close(self):
        plt.close(self.fig)


def rand_mesh(rng, n):
    """Random (n, 2) coordinate arrays: mixed magnitudes and signs, sometimes
    integer-valued, occasionally tiny, all finite."""
    scale = rng.choice([1.0, 10.0, 1000.0, 1e6, 1e-6])
    X = np.empty((n, 2))
    Y = np.empty((n, 2))
    for arr in (X, Y):
        for i in range(n):
            for j in range(2):
                v = rng.uniform(-scale, scale)
                if rng.random() < 0.25:
                    v = float(round(v))
                arr[i, j] = v
    return X, Y


# --- oracle plumbing: end-to-end constructions -----------------------------------

def end_to_end(orientation, extend, nbounds):
    """Full fresh colorbar construction over a boundary norm; a recorder
    captures the real X, Y the drawing pipeline hands to the method under
    test, and the observation is the constructed object's reported divider
    segments."""
    rec = {}
    orig = Colorbar._add_solids

    def recorder(self, X, Y, C):
        rec["X"] = np.array(X, copy=True)
        rec["Y"] = np.array(Y, copy=True)
        return orig(self, X, Y, C)

    fig, ax = plt.subplots()
    try:
        Colorbar._add_solids = recorder
        try:
            bounds = np.arange(nbounds, dtype=float)
            norm = BoundaryNorm(bounds, nbounds - 1)
            sm = ScalarMappable(norm=norm, cmap=plt.get_cmap("viridis",
                                                             nbounds - 1))
            cbar = fig.colorbar(sm, ax=ax, orientation=orientation,
                                extend=extend, drawedges=True)
        finally:
            Colorbar._add_solids = orig
        if "X" not in rec:
            return ("DISAGREEMENT (method never invoked)\n"
                    "  end-to-end orientation=%r extend=%r nbounds=%d"
                    % (orientation, extend, nbounds))
        observed = cbar.dividers.get_segments()
        ctx = ("end-to-end orientation=%r extend=%r nbounds=%d"
               % (orientation, extend, nbounds))
        return compare(observed, rec["X"], rec["Y"],
                       cbar._extend_lower(), cbar._extend_upper(), ctx)
    finally:
        plt.close(fig)


def main():
    checked = 0

    # boundary: full end-to-end constructions, all extends x orientations x
    # several boundary counts (including the minimal ones)
    for orientation in ("vertical", "horizontal"):
        for extend in ("neither", "min", "max", "both"):
            for nbounds in (2, 3, 4, 5, 8):
                err = end_to_end(orientation, extend, nbounds)
                if err:
                    print(err)
                    return 1
                checked += 1
    n_boundary = checked

    # fuzz: 1e5 direct trials over all configurations, minimal-n cases forced
    configs = [(o, e, inv)
               for o in ("vertical", "horizontal")
               for e in ("neither", "min", "max", "both")
               for inv in (False, True)]
    drivers = [Driver(*cfg) for cfg in configs]
    rng = random.Random(SEED)
    try:
        per = N_FUZZ // len(drivers)
        for drv in drivers:
            for t in range(per):
                if t < 8:
                    n = 2 + (t % 4)          # force the smallest meshes
                else:
                    n = rng.randint(2, 40)
                X, Y = rand_mesh(rng, n)
                err = drv.trial(X, Y)
                if err:
                    print(err)
                    return 1
                checked += 1
    finally:
        for drv in drivers:
            drv.close()

    print("G-CONF OK: shadow impl == real patched method on %d inputs "
          "(%d boundary end-to-end + %d fuzz, seed %d)."
          % (checked, n_boundary, checked - n_boundary, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
