#!/usr/bin/env python3
"""G-CONF differential conformance check for mwaskom__seaborn-3069 (nagini).

SHADOW: the impl regions of model.py (`finalize_axis_range` and
`finalize_axis_grid`), copied VERBATIM below with only the contract calls
(Requires / Ensures) stripped. The model IS Python, so the bodies run
directly; there are no @Pure helpers and no PSeq in this bundle. The one
@ContractOnly callee, `slot_count()`, is delegated to the REAL repo-relied
routine the model maps it to per mapping.md section 3.1 — the count of major
tick objects the live matplotlib Axis reports (`len(axis.get_major_ticks())`)
— bound per trial through a module hook so the verbatim impl text is
unchanged.

ORACLE: the REAL patched repo function per mapping.md section 1 —
`seaborn._core.plot.Plotter._finalize_figure`, the per-axis finalization the
model abstracts. The gate applies patch.diff to /testbed and sets
PYTHONPATH=/testbed before this script runs, so the seaborn import resolves
to the patched module. Each trial builds a Plotter carrying one real
matplotlib Axes (a minimal `_subplots` entry, exactly the fields the
finalizer reads), installs per-axis scale objects (`Nominal` for a
categorical axis, `Continuous` or absent for an ordinary one), optionally
records caller limits on the `Plot` spec, configures the axis's incoming
range / tick slots / gridline visibility, runs the real `_finalize_figure`,
and reads back `get_xlim()` / `get_ylim()` and the gridline visibility
(`any(g.get_visible() for g in axis.get_gridlines())`). One trial exercises
BOTH axes, i.e. both truth values of `is_vertical`, so each trial contributes
two Requires-satisfying inputs to each modeled function.

TYPE BRIDGE (mapping.md section 2): `is_categorical` <-> the scale installed
for the axis being the categorical (Nominal) one; `has_explicit` <-> the axis
key being present in the spec's limits mapping; `is_vertical` <-> the y-axis
iteration; `user_lo` / `user_hi` <-> the caller pair when explicit, else the
axis's incoming (pre-finalization) range, both pairs of floats compared
exactly (0.5 is exactly representable); `pre_visible` <-> the gridline
visibility measured on the live axis immediately before finalization;
`slot_count()` <-> the live major-tick count. The bridgeable carrier domain
is finite, non-singular float pairs: a singular explicit pair is excluded by
the model precondition (unchanged range-sanitization machinery, mapping.md
section 2), and non-finite values cannot be stored as a matplotlib axis
range at all, so neither realizes as an incoming or recorded range.

INPUT PLAN (>= 1e5 Requires-satisfying inputs): exhaustive boolean boundary
grid (categorical x explicit x grid visibility, per axis, 64 combos) crossed
with slot counts 1..12 and several caller-range shapes (including pairs that
coincide with the categorical tuple, inverted pairs, half-integer edges),
plus 55000 random fuzz trials over mixed slot counts, range magnitudes and
booleans. Every trial checks both axes' range AND grid, so the input count
is >= 4x the trial count. Pinned fuzz seed: 3069.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + the repo under test (seaborn/matplotlib) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless

from matplotlib.figure import Figure
import matplotlib.ticker as mticker

SEED = 3069
N_FUZZ = 55_000


# --- @ContractOnly callee: the REAL repo-relied routine (mapping.md 3.1) -----
# Bound per trial to the live axis's major-tick count so the verbatim impl
# text below calls the real callee, not a stub.

_slot_count_real = None


def slot_count():
    return _slot_count_real()


# --- impl region of model.py `finalize_axis_range`, verbatim, contracts
# --- stripped -----------------------------------------------------------------

def finalize_axis_range(is_categorical, has_explicit, is_vertical,
                        user_lo, user_hi):
    lo = user_lo
    hi = user_hi
    if has_explicit:
        # Caller pinned the range explicitly: use it verbatim. The categorical
        # special-casing below is skipped.
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)


# --- impl region of model.py `finalize_axis_grid`, verbatim, contracts
# --- stripped -----------------------------------------------------------------

def finalize_axis_grid(is_categorical, pre_visible):
    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible


# --- oracle: the real patched repo finalizer ----------------------------------

def gridlines_visible(axis_obj):
    return any(g.get_visible() for g in axis_obj.get_gridlines())


class Harness(object):
    """One reusable figure/axes driven through the real finalizer per trial."""

    def __init__(self):
        from seaborn._core.plot import Plot, Plotter
        from seaborn._core.scales import Nominal, Continuous
        self.Plot = Plot
        self.Nominal = Nominal
        self.Continuous = Continuous
        self.fig = Figure()
        self.ax = self.fig.add_subplot()
        self.plotter = Plotter(pyplot=False, theme={})
        self.plotter._figure = self.fig
        self.plotter._subplots = [{"ax": self.ax, "x": "x", "y": "y"}]

    def run(self, spec):
        """Configure the axes per the trial spec, run the REAL
        _finalize_figure, and return per-axis observations.

        spec[axis] = dict(cat, expl, n, lim, pre, grid) with
          cat: categorical scale installed;  expl: caller limits recorded;
          n: slot count when cat;            lim: caller (lo, hi) when expl;
          pre: incoming axis range;          grid: incoming grid visibility.
        Returns {axis: (range, grid_visible, n_real, pre_visible)}.
        """
        ax = self.ax
        self.plotter._scales = {}
        p = self.Plot()
        state = {}
        for axis in "xy":
            s = spec[axis]
            axis_obj = getattr(ax, axis + "axis")
            if s["cat"]:
                self.plotter._scales[axis] = self.Nominal()
                axis_obj.set_ticks(list(range(s["n"])))
            else:
                # sometimes install the ordinary scale, sometimes leave the
                # axis key unmapped; both are non-categorical to the finalizer
                if s.get("scale", True):
                    self.plotter._scales[axis] = self.Continuous()
                axis_obj.set_major_locator(mticker.AutoLocator())
            if s["expl"]:
                p._limits[axis] = s["lim"]
            getattr(ax, "set_%slim" % axis)(*s["pre"])
            axis_obj.grid(s["grid"])
            # the bridge values, measured on the live axis
            pre_vis = gridlines_visible(axis_obj)
            n_real = (len(axis_obj.get_major_ticks()) if s["cat"] else None)
            state[axis] = (n_real, pre_vis)

        self.plotter._finalize_figure(p)

        out = {}
        for axis in "xy":
            axis_obj = getattr(ax, axis + "axis")
            rng = tuple(getattr(ax, "get_%slim" % axis)())
            out[axis] = (rng, gridlines_visible(axis_obj),
                         state[axis][0], state[axis][1])
        return out


def check(harness, spec):
    """Run shadow and oracle on one trial; return an error string on
    disagreement, else None. Each trial covers both axes (both is_vertical
    truth values) for both modeled functions."""
    global _slot_count_real
    real = harness.run(spec)
    for axis in "xy":
        s = spec[axis]
        real_range, real_grid, n_real, pre_vis = real[axis]
        is_vertical = (axis == "y")
        if s["expl"]:
            user_lo, user_hi = float(s["lim"][0]), float(s["lim"][1])
        else:
            user_lo, user_hi = float(s["pre"][0]), float(s["pre"][1])
        if s["cat"]:
            _slot_count_real = (lambda v=n_real: v)
        else:
            _slot_count_real = _no_slot_count
        shadow_range = finalize_axis_range(s["cat"], s["expl"], is_vertical,
                                           user_lo, user_hi)
        shadow_grid = finalize_axis_grid(s["cat"], pre_vis)
        shadow_range = (float(shadow_range[0]), float(shadow_range[1]))
        real_range = (float(real_range[0]), float(real_range[1]))
        if shadow_range != real_range:
            return ("DISAGREEMENT (range) on axis=%s spec=%r "
                    "(user_lo=%r user_hi=%r n=%r):\n"
                    "  shadow (impl region)          = %r\n"
                    "  real (patched repo finalizer) = %r"
                    % (axis, s, user_lo, user_hi, n_real,
                       shadow_range, real_range))
        if bool(shadow_grid) != bool(real_grid):
            return ("DISAGREEMENT (grid) on axis=%s spec=%r (pre_visible=%r):\n"
                    "  shadow (impl region)          = %r\n"
                    "  real (patched repo finalizer) = %r"
                    % (axis, s, pre_vis, shadow_grid, real_grid))
    return None


def _no_slot_count():
    raise AssertionError(
        "shadow called slot_count() on a non-categorical trial")


# --- input generation -----------------------------------------------------------

# caller-range shapes: increasing / inverted / negative / half-integer edges /
# pairs coinciding with the categorical tuple (rival-distinguishing) / large,
# tiny and mixed magnitudes. All finite and non-singular (the bridgeable
# carrier domain; the model precondition excludes singular explicit pairs).
LIM_SHAPES = [
    (-1.0, 2.1),
    (2.1, -1.0),
    (0.0, 10.0),
    (-5.0, 5.0),
    (-0.5, 2.5),          # equals the 3-slot categorical tuple
    (2.5, -0.5),          # its inversion
    (-0.5, 0.5),          # equals the 1-slot categorical tuple
    (0.25, 0.75),
    (-1e6, 1e-6),
    (1e-9, 1e9),
    (-273.15, 451.0),
    (1234.5, 1234.75),
]

PRE_SHAPES = [
    (0.3, 4.7),
    (4.7, 0.3),
    (-2.0, -1.0),
    (0.925, 3.075),        # an automatic-margin-looking range
    (-0.5, 2.5),           # incoming range equal to the categorical tuple
    (1e-6, 1e6),
    (-10.5, 10.5),
]


def boundary_specs():
    specs = []
    # exhaustive boolean grid per axis: (cat, expl, grid) for x crossed with
    # (cat, expl, grid) for y = 64 combos, at a fixed slot count / range shape
    for xcat in (False, True):
        for xexpl in (False, True):
            for xgrid in (False, True):
                for ycat in (False, True):
                    for yexpl in (False, True):
                        for ygrid in (False, True):
                            specs.append({
                                "x": {"cat": xcat, "expl": xexpl, "n": 3,
                                      "lim": (-1.0, 2.1), "pre": (0.3, 4.7),
                                      "grid": xgrid},
                                "y": {"cat": ycat, "expl": yexpl, "n": 5,
                                      "lim": (0.0, 7.0), "pre": (1.1, 9.9),
                                      "grid": ygrid},
                            })
    # slot-count sweep n = 1..12 on each axis, explicit and not
    for n in range(1, 13):
        for expl in (False, True):
            specs.append({
                "x": {"cat": True, "expl": expl, "n": n,
                      "lim": (-1.0, 2.1), "pre": (0.3, 4.7), "grid": True},
                "y": {"cat": True, "expl": expl, "n": n,
                      "lim": (0.0, 7.0), "pre": (1.1, 9.9), "grid": True},
            })
    # caller-range shape sweep on categorical and ordinary axes
    for lim in LIM_SHAPES:
        for cat in (False, True):
            specs.append({
                "x": {"cat": cat, "expl": True, "n": 4,
                      "lim": lim, "pre": (0.3, 4.7), "grid": True},
                "y": {"cat": cat, "expl": True, "n": 4,
                      "lim": lim, "pre": (1.1, 9.9), "grid": False},
            })
    # incoming-range shape sweep on ordinary axes (the identity sub-domain)
    for pre in PRE_SHAPES:
        for scale in (False, True):
            specs.append({
                "x": {"cat": False, "expl": False, "n": 0, "lim": (0.0, 1.0),
                      "pre": pre, "grid": True, "scale": scale},
                "y": {"cat": False, "expl": False, "n": 0, "lim": (0.0, 1.0),
                      "pre": pre, "grid": False, "scale": scale},
            })
    return specs


def fuzz_spec(rng):
    def one_axis():
        cat = rng.random() < 0.5
        expl = rng.random() < 0.4
        n = rng.choice([1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 10, 12, 17, 25])

        def pair(nonsingular):
            mag = rng.choice([1.0, 1.0, 10.0, 100.0, 1e4, 1e8, 1e-3])
            while True:
                a = round(rng.uniform(-mag, mag), 6)
                b = round(rng.uniform(-mag, mag), 6)
                if rng.random() < 0.15:
                    # snap onto half-integer edges near the categorical tuple
                    a = rng.choice([-0.5, 0.5, 1.5, 2.5, n - 0.5, -1.5])
                    b = rng.choice([-0.5, 0.5, 1.5, 2.5, n - 0.5, 3.5])
                if not nonsingular or a != b:
                    return (float(a), float(b))
        return {"cat": cat, "expl": expl, "n": n,
                "lim": pair(True), "pre": pair(True),
                "grid": rng.random() < 0.5,
                "scale": rng.random() < 0.5}
    return {"x": one_axis(), "y": one_axis()}


def main():
    harness = Harness()

    trials = 0
    boundary = boundary_specs()
    for spec in boundary:
        err = check(harness, spec)
        if err:
            print(err)
            return 1
        trials += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        spec = fuzz_spec(rng)
        err = check(harness, spec)
        if err:
            print(err)
            return 1
        trials += 1

    # each trial checks both axes' range and grid: 2 inputs per modeled
    # function per trial, 4 checks per trial overall
    inputs = trials * 4
    print("G-CONF OK: shadow impl == real patched finalizer on %d trials "
          "(%d boundary + %d fuzz, seed %d) = %d per-axis checks; "
          "0 disagreements." % (trials, len(boundary), N_FUZZ, SEED, inputs))
    print(json.dumps({"trials": trials, "checked_inputs": inputs,
                      "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl regions; "
                                "slot_count bound to the real live "
                                "major-tick count)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
