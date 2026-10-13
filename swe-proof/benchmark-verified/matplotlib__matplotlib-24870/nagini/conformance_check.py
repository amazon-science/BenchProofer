#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-24870
(nagini).

SHADOW: the impl region of model.py `choose_default_levels`, copied verbatim
below with the contract calls (Requires/Ensures) stripped. The one
@ContractOnly callee (`auto_levels`) delegates to the REAL repo function it is
bound to per mapping.md section 3.1: the default-count branch of the level
selection, `ContourSet._autolev(7)`, run on a default-configured receiver
(locator None, linear scale, extend 'neither' -- the configuration the
modeled default path always runs under).

ORACLE: the REAL patched repo method per mapping.md section 1 --
`matplotlib.contour.ContourSet._process_contour_level_args`, invoked unbound
on a receiver carrying exactly the state the mapping binds (levels=None so
the default-selection block is taken, filled, zmin, zmax) with an empty
explicit-args tuple (the `not has_explicit` branch fixed by the model's
precondition) and the field's dtype. The gate applies patch.diff to /testbed
before this script runs and sets PYTHONPATH so the import resolves to the
patched module. The method's result is read back from `self.levels` AFTER its
own post-processing (line-contour interior filter, filled minimum-count and
monotonicity checks), so any post-selection rewriting would surface as a
disagreement. A small end-to-end tier additionally drives the four public
plotting entry points (contour/contourf/tricontour/tricontourf) on real
arrays and compares `cs.levels`, exercising the dtype-threading plumbing
hunks as well.

Type bridge (mapping.md section 2):
  * `two_valued`  <-> the dtype predicate `np.issubdtype(z_dtype, bool)`;
    the oracle receives np.dtype(bool) vs np.dtype(np.float64). A bool field
    can only attain the two values 0/1, so on the reachable repo domain a
    two-valued input always carries extents zmin=0.0, zmax=1.0 (and midpoint
    0.5) -- two-valued inputs are generated on exactly that bridge image.
  * `filled`      <-> `self.filled` (identity), `has_explicit` <-> non-empty
    explicit args (the driver fixes the False branch per the precondition).
  * `zmin`/`zmax`/`mid` are interpreted reals; `mid` enters pinned by the
    subtraction-only equation mid - zmin == zmax - mid (mapping.md 2.1). The
    float driver enforces that equation exactly in float64 (inputs are
    redrawn/adjusted until it holds), so every generated input satisfies the
    Requires under the bridge.
  * the resulting level list <-> List[float]; the oracle's `self.levels`
    (ndarray/list) lifts via float() per element, exact equality.

Input domain (the Requires): no explicit levels, zmin < zmax, and the
well-resolved-range guard (span >= 1e-6, span >= 1e-9*zmax,
span >= 1e-9*(0-zmin)); the driver replicates the guard and only submits
guard-satisfying ranges. Continuous fuzz spans ordinary, large-magnitude,
tiny-magnitude and near-guard-floor regimes; two-valued fuzz varies `filled`
on the bridge image (0, 1, 0.5).

>= 1e5 Requires-satisfying inputs: boundary + end-to-end + 100000 fuzz.
Pinned fuzz seed: 24870.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + numpy + matplotlib (the repo under test) only.
"""
import json
import random
import sys

SEED = 24870
N_FUZZ = 100000

import numpy as np                        # noqa: E402
import matplotlib                         # noqa: E402
matplotlib.use("Agg")
from matplotlib.contour import ContourSet  # noqa: E402


# --- the Requires (model.py pre-conditions), replicated for input filtering ---

def well_resolved(zmin, zmax):
    span = zmax - zmin
    if not (zmin < zmax):
        return False
    if not (span >= 1e-6):
        return False
    if not (span >= 1e-9 * zmax):
        return False
    if not (span >= 1e-9 * (0.0 - zmin)):
        return False
    return True


def mid_pinned(zmin, zmax, mid):
    # the subtraction-only defining equation of the midpoint (mapping.md 2.1)
    return (mid - zmin) == (zmax - mid)


# --- oracle receiver: exactly the state mapping.md binds ----------------------

class Receiver(object):
    """Minimal receiver for the real (unbound) repo methods: levels=None so
    the default-selection block runs; default locator/scale/extend, i.e. the
    configuration of the modeled default path."""
    _autolev = ContourSet._autolev

    def __init__(self, filled, zmin, zmax):
        self.levels = None
        self.filled = filled
        self.zmin = zmin
        self.zmax = zmax
        self.locator = None
        self.logscale = False
        self.extend = 'neither'


# --- @ContractOnly callee: the REAL repo delegate (mapping.md section 3.1) ----

def auto_levels(zmin, zmax):
    """The axiomatized ordinary multi-level selection, delegated to the REAL
    repo function: the default-count branch `self._autolev(7)`."""
    r = Receiver(filled=False, zmin=zmin, zmax=zmax)
    return [float(v) for v in ContourSet._autolev(r, 7)]


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def choose_default_levels(has_explicit, two_valued, filled, zmin, zmax, mid):
    result = []  # type: List[float]
    if two_valued:
        # `mid` is equidistant from the two distinct values, so it lies strictly
        # between them: zmin < mid < zmax.
        if filled:
            result = [zmin, mid, zmax]
        else:
            result = [mid]
    else:
        result = list(auto_levels(zmin, zmax))
    return result


# --- oracle: the real patched repo function -----------------------------------

def real_process_level_args(receiver, args, z_dtype):
    """The real (patched) selection routine, unbound-called on the receiver.
    Isolated in one function so a local smoke harness can substitute it."""
    return ContourSet._process_contour_level_args(receiver, args, z_dtype)


def real_default_levels(two_valued, filled, zmin, zmax):
    r = Receiver(filled=filled, zmin=zmin, zmax=zmax)
    z_dtype = np.dtype(bool) if two_valued else np.dtype(np.float64)
    real_process_level_args(r, (), z_dtype)
    return [float(v) for v in np.asarray(r.levels)]


# --- differential driver -------------------------------------------------------

def check(two_valued, filled, zmin, zmax, mid):
    """Run shadow and oracle on one Requires-satisfying input; return an error
    string on disagreement, else None."""
    shadow = [float(v) for v in
              choose_default_levels(False, two_valued, filled,
                                    zmin, zmax, mid)]
    real = real_default_levels(two_valued, filled, zmin, zmax)
    if shadow != real:
        return ("DISAGREEMENT on input two_valued=%r filled=%r "
                "zmin=%r zmax=%r mid=%r:\n"
                "  shadow (impl region)           = %r\n"
                "  real (patched level selection) = %r"
                % (two_valued, filled, zmin, zmax, mid, shadow, real))
    return None


def pin_mid(zmin, zmax):
    """Float-exact midpoint pinning: return (zmin, zmax, mid) satisfying the
    Requires (guard + defining equation) or None if this range cannot be
    pinned exactly in float64."""
    mid = zmin + (zmax - zmin) / 2.0
    if not mid_pinned(zmin, zmax, mid):
        # re-anchor the upper extent on the pinned midpoint
        zmax = mid + (mid - zmin)
        if not mid_pinned(zmin, zmax, mid):
            return None
    if not well_resolved(zmin, zmax):
        return None
    if not (zmin < mid < zmax):
        return None
    return (zmin, zmax, mid)


def boundary_cases():
    """Guard-satisfying boundary ranges (continuous regime) plus the
    two-valued bridge image; every case is pinned float-exactly."""
    cases = []
    # two-valued bridge image: extents 0/1, midpoint 0.5; both fill modes
    for filled in (False, True):
        cases.append((True, filled, 0.0, 1.0, 0.5))
    ranges = [
        (0.0, 1.0),            # the same extents a two-valued field yields
        (-1.0, 1.0),
        (0.0, 100.0),
        (-50.0, -10.0),
        (1.0, 1.0001),         # narrow but well-resolved
        (0.0, 1e-6),           # span exactly at the absolute guard floor
        (-1e-6, 0.0),
        (1e12, 2e12),          # large magnitude
        (-2e12, -1e12),
        (-0.5, 0.5),
        (1000.0, 1000.002),    # tiny relative span, clears the guard
        (-273.15, 5778.0),
        (0.0, 7.0),
        (-7.0, 0.0),
    ]
    for zmin, zmax in ranges:
        pinned = pin_mid(zmin, zmax)
        if pinned is None:
            continue
        for filled in (False, True):
            cases.append((False, filled) + pinned)
    return cases


def end_to_end_cases():
    """Drive the four public entry points on real arrays and compare
    `cs.levels` with the shadow: exercises the plumbing that threads the
    field's dtype through to the selection."""
    import matplotlib.pyplot as plt
    errs = []
    checked = 0

    z_bool_patterns = [
        np.array([[False, True], [True, False]]),
        np.array([[True, True, False], [False, True, True]]),
        np.tri(6, 6, dtype=bool),
        np.eye(5, dtype=bool),
    ]
    tri_x = np.array([0.0, 1.0, 0.0, 1.0, 0.5])
    tri_y = np.array([0.0, 0.0, 1.0, 1.0, 0.5])
    z_bool_tri = [
        np.array([False, True, True, False, True]),
        np.array([True, False, False, True, False]),
    ]

    def compare(levels, two_valued, filled, zmin, zmax, mid, label):
        got = [float(v) for v in np.asarray(levels)]
        want = [float(v) for v in
                choose_default_levels(False, two_valued, filled,
                                      zmin, zmax, mid)]
        if got != want:
            return ("END-TO-END DISAGREEMENT (%s, two_valued=%r filled=%r "
                    "zmin=%r zmax=%r):\n  shadow = %r\n  real   = %r"
                    % (label, two_valued, filled, zmin, zmax, want, got))
        return None

    fig, ax = plt.subplots()
    try:
        # rectangular-grid entry points, two-valued fields
        for z in z_bool_patterns:
            for filled, fn in ((False, ax.contour), (True, ax.contourf)):
                cs = fn(z)
                e = compare(cs.levels, True, filled, 0.0, 1.0, 0.5,
                            fn.__name__)
                if e:
                    errs.append(e)
                checked += 1
        # triangulated entry points, two-valued fields
        for z in z_bool_tri:
            for filled, fn in ((False, ax.tricontour), (True, ax.tricontourf)):
                cs = fn(tri_x, tri_y, z)
                e = compare(cs.levels, True, filled, 0.0, 1.0, 0.5,
                            fn.__name__)
                if e:
                    errs.append(e)
                checked += 1
        # continuous fields across all four entry points
        cont_ranges = [(0.0, 1.0), (-1.0, 1.0), (0.0, 100.0), (-50.0, -10.0),
                       (2.5, 3.5)]
        for zmin, zmax in cont_ranges:
            pinned = pin_mid(zmin, zmax)
            if pinned is None:
                continue
            zmin, zmax, mid = pinned
            z2 = np.array([[zmin, zmax], [zmin, zmax]], dtype=np.float64)
            for filled, fn in ((False, ax.contour), (True, ax.contourf)):
                cs = fn(z2)
                e = compare(cs.levels, False, filled, zmin, zmax, mid,
                            fn.__name__)
                if e:
                    errs.append(e)
                checked += 1
            zt = np.array([zmin, zmax, zmin, zmax, zmin], dtype=np.float64)
            for filled, fn in ((False, ax.tricontour), (True, ax.tricontourf)):
                cs = fn(tri_x, tri_y, zt)
                e = compare(cs.levels, False, filled, zmin, zmax, mid,
                            fn.__name__)
                if e:
                    errs.append(e)
                checked += 1
    finally:
        plt.close(fig)
    return errs, checked


def draw_range(rng):
    """One candidate continuous range, spanning ordinary / large / tiny
    magnitudes and near-guard-floor spans."""
    r = rng.random()
    if r < 0.35:
        zmin = rng.uniform(-100.0, 100.0)
        span = rng.uniform(1e-6, 250.0)
    elif r < 0.55:
        e = rng.randint(-5, 12)
        zmin = rng.uniform(-1.0, 1.0) * (10.0 ** e)
        span = rng.uniform(0.05, 5.0) * (10.0 ** e)
    elif r < 0.75:
        zmin = rng.uniform(-1000.0, 1000.0)
        floor = max(1e-6, 1.001e-9 * abs(zmin))
        span = floor * rng.uniform(1.0, 50.0)
    elif r < 0.9:
        zmin = rng.uniform(-1.0, 1.0)
        span = rng.uniform(1e-6, 2.0)
    else:
        zmin = -rng.uniform(0.0, 1e6)
        span = rng.uniform(1e-3, 2e6)
    return zmin, zmin + span


def main():
    checked = 0

    boundary = boundary_cases()
    for args in boundary:
        err = check(*args)
        if err:
            print(err)
            return 1
        checked += 1

    e2e_errs, e2e_checked = end_to_end_cases()
    if e2e_errs:
        print(e2e_errs[0])
        return 1
    checked += e2e_checked

    # randomized fuzz (pinned seed): 10% two-valued on the bridge image with
    # `filled` varying, 90% continuous over guard-satisfying pinned ranges
    rng = random.Random(SEED)
    fuzz = 0
    while fuzz < N_FUZZ:
        if rng.random() < 0.10:
            args = (True, rng.random() < 0.5, 0.0, 1.0, 0.5)
        else:
            zmin, zmax = draw_range(rng)
            pinned = pin_mid(zmin, zmax)
            if pinned is None:
                continue
            args = (False, rng.random() < 0.5) + pinned
        err = check(*args)
        if err:
            print(err)
            return 1
        fuzz += 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched default level selection on "
          "%d inputs (%d boundary + %d end-to-end + %d fuzz, seed %d); "
          "0 disagreements."
          % (checked, len(boundary), e2e_checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
