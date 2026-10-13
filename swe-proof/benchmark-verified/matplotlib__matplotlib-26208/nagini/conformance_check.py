#!/usr/bin/env python3
"""G-CONF differential conformance check for matplotlib__matplotlib-26208
(nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures) stripped. The model IS Python: the two contracted
builder functions `build_companion_sharing_horizontal` /
`build_companion_sharing_vertical` and the two minimal carrier classes
(`UnitDescriptor`, `CoordinateAxis`) run directly once the Ensures lines are
removed. There are no @Pure helpers with bodies beyond the constructors, no
PSeq, and no @ContractOnly callees (mapping.md section 3.1: the axioms region
is empty), so nothing calls back into the repo from the shadow itself.

ORACLE: the REAL patched repo methods the model models per mapping.md --
`matplotlib.axes._base._AxesBase.twinx` (the companion builder sharing the
horizontal direction) and `.twiny` (sharing the vertical direction). The gate
applies patch.diff to /testbed before this script runs; PYTHONPATH=/testbed
makes the patched package importable. Headless Agg backend. Each trial puts a
non-None descriptor object on the source frame's shared-direction axis
(`Axis.units`), builds the companion via the real builder, and reads the
companion's shared-direction axis descriptor (`ax2.xaxis.units` for the
horizontal share, `ax2.yaxis.units` for the vertical share).

Type bridge (mapping.md section 2): `matplotlib.axis.Axis` maps to
`CoordinateAxis` carrying the single touched field (`units` maps to
`descriptor`); the descriptor value is identity-only, so the model-side input
carrier holds THE VERY SAME Python object the real axis carries and the diff
is pure `is`-identity: the shadow's returned `descriptor` must be the same
object as the real companion axis' `units` (and their None-ness must agree).
The read-only source is checked too: after the real build the source axis
must still carry its original descriptor object (the model's fractional
read-only permission plus the source postconditions).

Input domain: the Requires demand a non-None descriptor on the source's
shared-direction axis; every trial satisfies this by construction. The
descriptor pool spans what the real unit machinery can leave on an axis plus
arbitrary opaque objects (identity is the only observable): real categorical
unit-data objects harvested from string-data plots (the hidden-test scenario
family), fresh instances of the model's own opaque descriptor carrier, plain
`object()` instances, and a handful of long-lived shared objects (so repeated
and cross-axis sharing of one descriptor is exercised). Boundary cases: the
four categorical scenarios from axiom_check.py on both sites, same-object on
both axes, back-to-back rebuilds with an unchanged descriptor, and a
descriptor harvested from one figure installed on another.

>= 1e5 Requires-satisfying site-inputs: 16 boundary builds + 50,000 fuzz
iterations x 2 sites each = 100,016 real builder invocations, each diffed
against the shadow. Pinned fuzz seed: 26208.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib + matplotlib (the repo under test) only.
"""
import json
import random
import sys

import matplotlib
matplotlib.use("Agg")  # headless
from matplotlib.figure import Figure

SEED = 26208
N_FUZZ = 50_000


# --- model.py carriers, verbatim, contract lines stripped -----------------------

class UnitDescriptor:
    """An opaque descriptor object. Only its object identity is observable."""

    def __init__(self) -> None:
        self.present = True  # type: bool


class CoordinateAxis:
    """A coordinate axis carrying only the touched field: its descriptor
    reference. A freshly constructed axis has no descriptor (None)."""

    def __init__(self) -> None:
        self.descriptor = None  # type: Optional[UnitDescriptor]


# --- the impl regions of model.py, verbatim, contract calls stripped ------------

def build_companion_sharing_horizontal(source_horizontal):
    companion_horizontal = CoordinateAxis()
    companion_horizontal.descriptor = source_horizontal.descriptor
    return companion_horizontal


def build_companion_sharing_vertical(source_vertical):
    companion_vertical = CoordinateAxis()
    companion_vertical.descriptor = source_vertical.descriptor
    return companion_vertical


# --- the diff: one real build vs one shadow run ----------------------------------

def check_site(ax1, site, descriptor):
    """Install `descriptor` on the source frame's shared-direction axis, build
    the companion via the REAL builder, run the shadow on a model carrier
    holding the same object, and diff by identity. Returns an error string on
    disagreement, else None. Cleans up the companion so the figure stays
    small across many trials."""
    if site == "horizontal":
        source_axis = ax1.xaxis
        source_axis.units = descriptor
        ax2 = ax1.twinx()                    # REAL builder under test
        real_out = ax2.xaxis.units           # companion's shared axis
        shadow_fn = build_companion_sharing_horizontal
    else:
        source_axis = ax1.yaxis
        source_axis.units = descriptor
        ax2 = ax1.twiny()                    # REAL builder under test
        real_out = ax2.yaxis.units           # companion's shared axis
        shadow_fn = build_companion_sharing_vertical

    # model-side input: a CoordinateAxis carrying the very same object
    src = CoordinateAxis()
    src.descriptor = descriptor
    shadow_out = shadow_fn(src).descriptor

    err = None
    if (shadow_out is None) != (real_out is None) or shadow_out is not real_out:
        err = ("DISAGREEMENT site=%s descriptor=%r\n"
               "  shadow companion descriptor: %r\n"
               "  real companion axis descriptor: %r"
               % (site, descriptor, shadow_out, real_out))
    elif source_axis.units is not descriptor:
        err = ("DISAGREEMENT site=%s descriptor=%r\n"
               "  real builder replaced the source axis descriptor with %r "
               "(model treats the source as read-only)"
               % (site, descriptor, source_axis.units))
    elif src.descriptor is not descriptor:
        err = ("SHADOW SELF-CHECK site=%s: shadow mutated its source carrier"
               % site)
    ax2.remove()
    return err


def harvest_real_descriptors():
    """Plot string data so the real unit machinery installs genuine
    categorical unit-data objects on both axes; harvest them as fuzz-pool
    descriptors. Same scenario family as axiom_check.py / the hidden tests."""
    cases = [
        (["0", "1"], ["a", "b"]),
        (["x", "y", "z"], ["p", "q", "r"]),
        (["Mon", "Tue", "Wed", "Thu"], ["a", "b", "c", "d"]),
        (["16 May", "17 May"], ["lo", "hi"]),
    ]
    harvested = []
    for a, b in cases:
        fig = Figure()
        ax = fig.subplots()
        ax.plot(a, b)
        assert ax.xaxis.units is not None and ax.yaxis.units is not None, \
            "scenario setup failed: string data left an axis without units"
        harvested.append((ax, ax.xaxis.units, ax.yaxis.units))
    return harvested


def main():
    checked = 0

    # --- boundary -------------------------------------------------------------
    harvested = harvest_real_descriptors()
    real_pool = []
    for ax, ux, uy in harvested:
        # 1) the categorical scenarios themselves, on their own figures, with
        #    the genuine machinery-installed descriptors, both sites
        for site, d in (("horizontal", ux), ("vertical", uy)):
            err = check_site(ax, site, d)
            if err:
                print(err)
                return 1
            checked += 1
        real_pool += [ux, uy]

    fig = Figure()
    ax1 = fig.subplots()
    shared = object()
    boundary = [
        # same object installed on both axes of one figure, then each site
        ("horizontal", shared), ("vertical", shared),
        # back-to-back rebuild with the descriptor left unchanged
        ("horizontal", shared), ("vertical", shared),
        # a genuine unit-data object harvested from ANOTHER figure
        ("horizontal", real_pool[0]), ("vertical", real_pool[1]),
        # the model's own opaque carrier as the descriptor object
        ("horizontal", UnitDescriptor()), ("vertical", UnitDescriptor()),
    ]
    for site, d in boundary:
        err = check_site(ax1, site, d)
        if err:
            print(err)
            return 1
        checked += 1
    n_boundary = checked

    # --- fuzz -------------------------------------------------------------------
    rng = random.Random(SEED)
    long_lived = [object() for _ in range(8)] + \
                 [UnitDescriptor() for _ in range(8)]

    def rand_descriptor():
        kind = rng.randrange(4)
        if kind == 0:
            return rng.choice(real_pool)       # genuine unit-data object
        if kind == 1:
            return rng.choice(long_lived)      # repeatedly-shared object
        if kind == 2:
            return UnitDescriptor()            # fresh model-carrier instance
        return object()                        # fresh opaque object

    for i in range(N_FUZZ):
        # both sites each iteration, in a random order, with independently
        # drawn descriptors (sometimes the same object lands on both axes)
        d1, d2 = rand_descriptor(), rand_descriptor()
        sites = [("horizontal", d1), ("vertical", d2)]
        if rng.random() < 0.5:
            sites.reverse()
        for site, d in sites:
            err = check_site(ax1, site, d)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched companion-builder "
          "descriptor propagation on %d site-inputs (%d boundary + %d fuzz "
          "iterations x 2 sites, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "no axiomatized callees)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
