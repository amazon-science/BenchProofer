#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24177
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped and PSeq realized as an
immutable tuple shim (ToSeq lifts a list into it). The @Pure helpers
`seq_max` / `_imax` and the two proof lemmas copy over as plain functions
(the lemma bodies, after stripping, are ghost recursions with no effect on
the computed result — kept for verbatim fidelity). The @ContractOnly
`subsel_*` callees are consumed only by the prepatch model; the impl region
under check never calls them, so no real-callee stand-in is needed.

ORACLE: the REAL patched repo method the model models per mapping.md —
`matplotlib.axes._base._AxesBase._update_patch_limits`. Its observable is a
mutation of the axes' data-limit bbox: the method gathers the patch path's
vertices and feeds them to `update_datalim`, whose per-axis upper end is the
enclosing bound the model returns. The gate applies patch.diff to /testbed
before this script runs; PYTHONPATH=/testbed makes the patched module
importable.

Type bridge (mapping.md section 2): the model carrier `List[int]` is one
axis of the gathered coordinate sequence. A generated integer list becomes
one coordinate column of a polyline path (the other column carries an
independent sample, so each oracle call checks two inputs at once); the
method is invoked on a fresh null data-limit box with the patch transform
equal to the axes' data transform (so coordinates pass through unchanged),
and the resulting per-axis `dataLim` upper end is compared against the
shadow's returned bound. For a pure polyline every path vertex appears
among the gathered points, and the upper end is their maximum, so feeding
the raw per-axis coordinate list to the shadow is exactly the mapping's
`verts`. Integer coordinates are exact in float64 far beyond the generated
range, so the comparison is exact (mapping.md A2: the modeled behaviour is
which values are covered, not floating-point precision).

Scaled regime: long step-outline inputs are additionally bridged through an
exact power-of-two scaling (coordinate = value * 2**-7). Scaling by a
positive constant commutes with max, and small integers times a power of
two are exact in float64, so the comparison stays exact — while the
geometry becomes small enough that gathering EVERY vertex is load-bearing
for the enclosing bound. (Confirmed discriminating: on the unpatched repo
these scaled step outlines disagree with the shadow; on the patched repo
they agree.)

Input domain: Requires demands a non-empty integer list. Generation covers
single elements, duplicates, extremes at every position, negative and
large-magnitude values, and long (>= 128 vertex) step outlines with an
interior extreme, run in the scaled regime.

>= 1e5 Requires-satisfying inputs: boundary cases + 2 x 50000 fuzz lists
(each oracle call bridges two independent lists, one per axis).
Pinned fuzz seed: 24177.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy only.
"""
import json
import random
import sys

import numpy as np

SEED = 24177
N_FUZZ_CALLS = 50_000  # x2 lists per call = 100_000 fuzz inputs


# --- PSeq shim: immutable sequence with the operations the impl uses ---------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ---------------------------

def seq_max(s):
    if len(s) == 1:
        return s[0]
    return _imax(s[0], seq_max(s.drop(1)))


def _imax(a, b):
    return a if a >= b else b


# --- proof lemmas, contracts stripped (ghost recursions, no computed effect) --

def lemma_seq_max_dominates(s):
    if len(s) > 1:
        lemma_seq_max_dominates(s.drop(1))
        t = s.drop(1)


def lemma_seq_max_attained(s):
    if len(s) == 1:
        pass
    else:
        t = s.drop(1)
        lemma_seq_max_attained(t)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def enclosing_upper_bound(verts):
    lemma_seq_max_dominates(ToSeq(verts))
    best = verts[len(verts) - 1]
    i = len(verts) - 1
    while i > 0:
        if verts[i - 1] > best:
            best = verts[i - 1]
        i = i - 1
    lemma_seq_max_dominates(ToSeq(verts))
    lemma_seq_max_attained(ToSeq(verts))
    return best


# --- oracle: the real patched repo method, observed via the data-limit box ----

def make_axes():
    # Backend-free figure: no GUI, no pyplot state.
    from matplotlib.figure import Figure
    fig = Figure()
    return fig.add_subplot()


def real_upper_ends(ax, xs, ys, scale=1.0):
    """Invoke the REAL `_update_patch_limits` on a polyline patch whose
    coordinate columns are (xs, ys) times `scale`, starting from a null
    data-limit box, and return the per-axis upper ends of the resulting
    data limits."""
    from matplotlib.path import Path
    import matplotlib.patches as mpatches
    from matplotlib.transforms import Bbox

    path = Path(np.column_stack([np.asarray(xs, float) * scale,
                                 np.asarray(ys, float) * scale]))
    patch = mpatches.PathPatch(path)
    # Patch coordinates == data coordinates: values pass through unchanged.
    patch.set_transform(ax.transData)
    ax.dataLim.set_points(Bbox.null().get_points())
    ax.ignore_existing_data_limits = True
    ax._update_patch_limits(patch)
    return float(ax.dataLim.intervalx[1]), float(ax.dataLim.intervaly[1])


def check_pair(ax, xs, ys, scale=1.0):
    """One oracle call bridges two model inputs (one per axis). `scale` is
    an exact power of two (max commutes with positive scaling; small ints
    times a power of two are exact in float64, so equality stays exact).
    Returns an error string on any disagreement, else None."""
    shadow_x = enclosing_upper_bound(list(xs)) * scale
    shadow_y = enclosing_upper_bound(list(ys)) * scale
    real_x, real_y = real_upper_ends(ax, xs, ys, scale=scale)
    if float(shadow_x) != real_x or float(shadow_y) != real_y:
        return ("DISAGREEMENT\n  xs=%r\n  ys=%r\n  scale=%r\n"
                "  shadow=(%r, %r)\n  real=(%r, %r)"
                % (list(xs), list(ys), scale, shadow_x, shadow_y,
                   real_x, real_y))
    return None


# --- input generation ----------------------------------------------------------


def step_outline(nsteps, peakstep, ymax, xstep=20):
    """An integer step outline: x advances by `xstep` per step pair while y
    ramps up to `ymax` around `peakstep` and back down. With >= 64 steps the
    outline has >= 128 vertices — the long-outline regime where covering
    every vertex is load-bearing for the enclosing bound. Returns (xs, ys)."""
    xs, ys = [], []
    x = 0
    denom = max(peakstep, nsteps - peakstep)
    for k in range(nsteps):
        frac = 1 - abs(k - peakstep) / denom
        y = round(ymax * frac * frac)
        xs += [x, x]
        ys += [ys[-1] if ys else 0, y]
        x += xstep
    return xs, ys


def boundary_lists():
    return [
        [0],
        [7],
        [-3],
        [0, 0],
        [1, 2],
        [2, 1],
        [-5, -5, -5],
        [3, 1, 2],                       # extreme first
        [1, 2, 3],                       # extreme last
        [1, 3, 2],                       # extreme interior
        [-1000000, 1000000],             # large magnitude
        [0, -1, 0, -1],
        list(range(50)),
        list(range(50, 0, -1)),
    ]


def boundary_outlines():
    return [
        step_outline(70, 35, 42),        # symmetric ramp, interior peak
        step_outline(64, 10, 30),        # early peak
        step_outline(100, 90, 17),       # late peak
        step_outline(70, 35, -25),       # downward ramp (extreme is a trough)
    ]


def rand_list(rng):
    n = rng.randint(1, 12)
    if rng.random() < 0.1:
        lo, hi = -10 ** 6, 10 ** 6
    else:
        lo, hi = -1000, 1000
    return [rng.randint(lo, hi) for _ in range(n)]


def rand_outline(rng):
    nsteps = rng.randint(64, 120)
    peakstep = rng.randint(5, nsteps - 5)
    ymax = rng.choice([-1, 1]) * rng.randint(10, 60)
    return step_outline(nsteps, peakstep, ymax)


SCALE = 2.0 ** -7  # exact in float64; puts long outlines in the small regime


def main():
    ax = make_axes()

    checked = 0
    bl = boundary_lists()
    # pair each boundary list with every other (and itself) across the axes
    for i in range(len(bl)):
        for j in range(len(bl)):
            if len(bl[i]) != len(bl[j]):
                continue
            err = check_pair(ax, bl[i], bl[j])
            if err:
                print(err)
                return 1
            checked += 2
    # remaining boundary lists paired with a same-length constant column,
    # raw and in the scaled regime (exact power-of-two scale)
    for lst in bl:
        for scale in (1.0, SCALE):
            err = check_pair(ax, lst, [1] * len(lst), scale=scale)
            if err:
                print(err)
                return 1
            checked += 2
    # long step outlines, scaled: the regime where covering every vertex
    # decides the bound
    for xs, ys in boundary_outlines():
        err = check_pair(ax, xs, ys, scale=SCALE)
        if err:
            print(err)
            return 1
        checked += 2

    rng = random.Random(SEED)
    for k in range(N_FUZZ_CALLS):
        if k % 10 == 0:
            # scaled long step outline (small-geometry, full-coverage regime)
            xs, ys = rand_outline(rng)
            err = check_pair(ax, xs, ys, scale=SCALE)
        else:
            xs = rand_list(rng)
            ys = [rng.randint(-1000, 1000) for _ in range(len(xs))]
            err = check_pair(ax, xs, ys)
        if err:
            print(err)
            return 1
        checked += 2

    print("G-CONF OK: shadow impl == real data-limit upper end on %d inputs "
          "(boundary + %d fuzz lists, seed %d)."
          % (checked, 2 * N_FUZZ_CALLS, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
