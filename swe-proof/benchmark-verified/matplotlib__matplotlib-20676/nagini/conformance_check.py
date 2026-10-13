#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-20676
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (the two trailing Assert lines) stripped. The @Pure helper
`selected_bound` copies over as a plain function on a tuple-backed PSeq shim
and is used as a redundant internal cross-check. The only @ContractOnly
callee, `reported_positions`, models the report-back behaviour of the real
line-handle widget; the ORACLE path below exercises that real widget directly
(the oracle's observable IS the widget's reported positions), so the shadow
never needs a stand-in for it.

ORACLE: the REAL patched repo method the model models per mapping.md —
`matplotlib.widgets.SpanSelector._setup_edge_handle` — invoked on a live
selector whose axes carry the coordinate ranges under test; the observation
is `._edge_handles.positions` (the pair of coordinates the widget reports).
The gate applies patch.diff to /testbed before this script runs;
PYTHONPATH=/testbed makes the patched module importable. Headless Agg
backend.

Type bridge (mapping.md section 2): each coordinate is a repo `float`,
modelled as `int` under an injective encoding (the modelled behaviour is pure
value selection / pass-through — no arithmetic on magnitudes — so any
injective encoding preserves the pinned equalities). This script realises the
encoding explicitly per input: the finitely many float coordinates of one
input are mapped bijectively to small ints, the shadow runs on the ints, and
its output is decoded back to floats for the comparison. The orientation
string maps to the model's two-valued discriminant 0/1; the 2-tuples read
from the live axes (`get_xbound()`/`get_ybound()`) map endpoint-wise, and the
selector's own current shape extents supply the model's `other_coords`
parameter.

Input domain: Requires demands only a valid two-valued direction; the
coordinate parameters are unconstrained, but they are read from a live axes,
so fuzzing drives the axes to arbitrary finite limits (integer-valued,
fractional, negative, large-magnitude, inverted) and reads the resulting
bounds back as the shadow's inputs — exactly the binding mapping.md gives for
`x_bound`/`y_bound`.

>= 1e5 Requires-satisfying inputs: boundary cases (including full
fresh-construction end-to-end checks that also confirm the ranges are left
unchanged) + 100000 fuzz inputs split over both orientations.
Pinned fuzz seed: 20676.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + matplotlib (the repo under test) + numpy (its
dependency) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector

SEED = 20676
N_FUZZ = 100_000


HORIZONTAL = 0
VERTICAL = 1


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


# --- pure region of model.py, contracts stripped ------------------------------

def selected_bound(direction, x_lo, x_hi, y_lo, y_hi):
    if direction == HORIZONTAL:
        return PSeq(x_lo, x_hi)
    return PSeq(y_lo, y_hi)


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def selector_initial_coords(direction, x_bound, y_bound, other_coords):
    # Select the two endpoints of THIS orientation's current range as the
    # reported coordinate values.
    if direction == HORIZONTAL:
        result = [x_bound[0], x_bound[1]]  # type: List[int]
    else:
        result = [y_bound[0], y_bound[1]]
    # The selected values equal the orientation's range, which the
    # position-reporting component then returns unchanged.
    return result
    # (two Assert(...) contract calls stripped here)


# --- bridge: float coordinates <-> int model carrier ---------------------------

def run_shadow(direction_str, x_bound, y_bound, other_coords):
    """Encode one input's float coordinates injectively into ints, run the
    shadow on the int carrier, decode the result back to floats."""
    coords = sorted(set(list(x_bound) + list(y_bound) + list(other_coords)))
    enc = {v: i for i, v in enumerate(coords)}
    dec = {i: v for v, i in enc.items()}
    d = HORIZONTAL if direction_str == "horizontal" else VERTICAL
    xb = (enc[x_bound[0]], enc[x_bound[1]])
    yb = (enc[y_bound[0]], enc[y_bound[1]])
    oc = (enc[other_coords[0]], enc[other_coords[1]])
    out = selector_initial_coords(d, xb, yb, oc)
    # redundant cross-check against the pure-region helper
    sb = selected_bound(d, xb[0], xb[1], yb[0], yb[1])
    assert len(out) == len(sb) and all(out[i] == sb[i] for i in range(len(out)))
    return [dec[v] for v in out]


# --- oracle plumbing -----------------------------------------------------------

class Driver:
    """A live selector per orientation; each trial re-points the axes' ranges,
    re-invokes the real method under test, observes the widget's reported
    positions, then removes the created artists so the axes stay clean."""

    def __init__(self, direction_str):
        self.direction_str = direction_str
        self.fig, self.ax = plt.subplots()
        self.ax.set_xlim(0.0, 1.0)
        self.ax.set_ylim(0.0, 1.0)
        self.tool = SpanSelector(self.ax, lambda *a: None, direction_str,
                                 interactive=True)
        self.props = dict(color="r")
        # drop the handles the constructor made; trials make their own
        self._cleanup()
        self._base_artists = len(self.tool.artists)

    def _cleanup(self):
        try:
            self.tool._edge_handles.remove()
        except Exception:
            for a in self.tool._edge_handles.artists:
                try:
                    a.remove()
                except Exception:
                    pass

    def trial(self, xlim, ylim):
        """Set the axes ranges, run oracle + shadow, return an error string on
        disagreement, else None."""
        self.ax.set_xlim(*xlim)
        self.ax.set_ylim(*ylim)
        x_bound = self.ax.get_xbound()
        y_bound = self.ax.get_ybound()
        other_coords = tuple(self.tool.extents)

        self.tool._setup_edge_handle(self.props)   # REAL patched method
        observed = list(self.tool._edge_handles.positions)
        self._cleanup()
        del self.tool.artists[self._base_artists:]

        expected = run_shadow(self.direction_str, x_bound, y_bound,
                              other_coords)
        if observed != expected:
            return ("DISAGREEMENT\n  direction=%r xlim=%r ylim=%r\n"
                    "  x_bound=%r y_bound=%r other_coords=%r\n"
                    "  shadow=%r\n  real=%r"
                    % (self.direction_str, xlim, ylim, x_bound, y_bound,
                       other_coords, expected, observed))
        return None

    def close(self):
        plt.close(self.fig)


def end_to_end(direction_str, xlim, ylim):
    """Fresh full construction: the initially reported pair must equal the
    shadow's answer, and constructing the selector must leave both ranges
    unchanged (the modelled invariant that the reported values already lie
    inside the current range)."""
    fig, ax = plt.subplots()
    try:
        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)
        fig.canvas.draw()
        x_bound = ax.get_xbound()
        y_bound = ax.get_ybound()
        tool = SpanSelector(ax, lambda *a: None, direction_str,
                            interactive=True)
        observed = list(tool._edge_handles.positions)
        expected = run_shadow(direction_str, x_bound, y_bound,
                              tuple(tool.extents))
        if observed != expected:
            return ("DISAGREEMENT (fresh construction)\n"
                    "  direction=%r xlim=%r ylim=%r\n  shadow=%r\n  real=%r"
                    % (direction_str, xlim, ylim, expected, observed))
        fig.canvas.draw()
        if ax.get_xbound() != x_bound or ax.get_ybound() != y_bound:
            return ("DISAGREEMENT (range changed by construction)\n"
                    "  direction=%r xlim=%r ylim=%r\n"
                    "  before x=%r y=%r after x=%r y=%r"
                    % (direction_str, xlim, ylim, x_bound, y_bound,
                       ax.get_xbound(), ax.get_ybound()))
        return None
    finally:
        plt.close(fig)


BOUNDARY_LIMS = [
    ((10.0, 20.0), (10.0, 30.0)),      # the reported scenario's ranges
    ((0.0, 1.0), (0.0, 1.0)),
    ((-5.0, 5.0), (-1.0, 1.0)),
    ((-100.0, -50.0), (50.0, 100.0)),  # both ranges strictly one-signed
    ((0.25, 0.75), (-0.5, 2.5)),       # fractional endpoints
    ((1e6, 2e6), (-2e6, -1e6)),        # large magnitude
    ((20.0, 10.0), (30.0, 10.0)),      # inverted limits (bounds sort)
    ((0.0, 1e-9), (0.0, 1.0)),         # tiny extent
]


def rand_lim(rng):
    scale = rng.choice([1.0, 10.0, 1000.0, 1e6])
    a = rng.uniform(-scale, scale)
    b = rng.uniform(-scale, scale)
    if a == b:                          # avoid degenerate identical limits
        b = a + 1.0
    if rng.random() < 0.5:              # integer-valued endpoints half the time
        a, b = float(round(a)), float(round(b))
        if a == b:
            b = a + 1.0
    return (a, b)


def main():
    checked = 0

    # boundary: fresh end-to-end constructions (also checks range-unchanged)
    for direction_str in ("horizontal", "vertical"):
        for xlim, ylim in BOUNDARY_LIMS:
            err = end_to_end(direction_str, xlim, ylim)
            if err:
                print(err)
                return 1
            checked += 1

    # fuzz: 1e5 trials split over both orientations, in-place re-invocation
    rng = random.Random(SEED)
    n_boundary = checked
    for direction_str in ("horizontal", "vertical"):
        drv = Driver(direction_str)
        try:
            for _ in range(N_FUZZ // 2):
                err = drv.trial(rand_lim(rng), rand_lim(rng))
                if err:
                    print(err)
                    return 1
                checked += 1
        finally:
            drv.close()

    print("G-CONF OK: shadow impl == real patched method on %d inputs "
          "(%d boundary end-to-end + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
