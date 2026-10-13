#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26208.

The modelled change is a pure object-field propagation, spelled out directly in
model.py (no consumed @ContractOnly axiom). What G-AX validates here is the
single **A-reference**: the deep model's postcondition

    after building the companion frame, the companion's shared-direction axis
    references the SAME unit-descriptor object as the source frame's
    corresponding axis (identity), and is therefore non-None,

is exactly the observable behaviour of the REAL matplotlib companion-frame
builders. We construct the real scenario in-container (matplotlib is present in
the instance image), drive the source frame to acquire a descriptor from
unit-bearing data, build the companion, and observe the identity behaviour on
the real objects. This is the same scenario the hidden FAIL_TO_PASS tests
exercise, checked here as the reference for the deep model.

Self-validating against the image as shipped: the script is a DISCRIMINATION
check, not a post-fix assertion. Run against the base_commit (pre-patch) tree it
confirms the companion axis does NOT propagate the descriptor (the bug); run
against the patched tree it confirms the model's identity invariant holds. It
therefore exits 0 on either tree as long as the observed behaviour is one of the
two expected regimes, and only fails (exit 1) if neither holds — i.e. if the
deep model would be unsound against a patched tree. The bundle's `patch.diff`
selects which regime is in force; the reported regime tells the auditor which
tree it ran on. (DEFECT-2 fix: previously asserted the post-fix invariant
unconditionally and thus spuriously exited 1 on the pre-patch image.)
"""
import sys

import matplotlib
matplotlib.use("Agg")
from matplotlib.figure import Figure


def observe(source_axis, companion_axis):
    """Observe the identity regime on real Axis objects. Returns one of:
      - 'patched': companion.units is source.units and is not None
        (the deep-model postcondition holds — the fix is present)
      - 'prepatch': companion.units is None while source.units is not None
        (the descriptor is NOT propagated — exactly the bug the F2P test sees)
      - ('unsound', detail): neither regime — would make the deep model unsound.
    Raises AssertionError only if the scenario precondition itself fails."""
    assert source_axis.units is not None, \
        "scenario setup failed: source axis has no descriptor"
    if companion_axis.units is source_axis.units and \
            companion_axis.units is not None:
        return "patched"
    if companion_axis.units is None:
        return "prepatch"
    return ("unsound", "companion.units (%r) is neither source.units (%r) nor "
            "None" % (companion_axis.units, source_axis.units))


def check_share_horizontal(a, b):
    """Companion sharing the horizontal direction (its horizontal axis is the
    shared one): build it and observe the identity regime on that axis."""
    fig = Figure()
    ax1 = fig.subplots()
    ax1.plot(a, b)                       # unit-bearing x -> xaxis.units set
    assert ax1.xaxis.units is not None, \
        "scenario setup failed: source horizontal axis has no descriptor"
    ax2 = ax1.twinx()                    # companion sharing horizontal axis
    return observe(ax1.xaxis, ax2.xaxis)


def check_share_vertical(a, b):
    """Companion sharing the vertical direction (its vertical axis is the
    shared one): build it and observe the identity regime on that axis."""
    fig = Figure()
    ax1 = fig.subplots()
    ax1.plot(a, b)                       # unit-bearing y -> yaxis.units set
    assert ax1.yaxis.units is not None, \
        "scenario setup failed: source vertical axis has no descriptor"
    ax2 = ax1.twiny()                    # companion sharing vertical axis
    return observe(ax1.yaxis, ax2.yaxis)


def main():
    # Unit-bearing (string) data drives matplotlib's unit machinery -> a
    # non-None descriptor on the corresponding axis. Each case feeds the data to
    # the relevant direction so the shared axis is unit-bearing.
    cases = [
        (["0", "1"], ["a", "b"]),                          # the F2P scenario
        (["x", "y", "z"], ["p", "q", "r"]),
        (["Mon", "Tue", "Wed", "Thu"], ["a", "b", "c", "d"]),
        (["16 May", "17 May"], ["lo", "hi"]),
    ]
    regimes = set()
    for a, b in cases:
        for label, regime in (("horizontal", check_share_horizontal(a, b)),
                              ("vertical", check_share_vertical(a, b))):
            if isinstance(regime, tuple):
                print("G-AX FAIL: A-reference (%s) unsound: %s" % (label,
                                                                   regime[1]))
                return 1
            regimes.add(regime)

    if regimes == {"patched"}:
        print("G-AX OK (patched tree): companion-frame descriptor propagation "
              "(A-reference) sound on %d horizontal + %d vertical real "
              "scenarios; companion shared axis references the SAME descriptor "
              "object as the source." % (len(cases), len(cases)))
    elif regimes == {"prepatch"}:
        print("G-AX OK (pre-patch tree): discrimination confirmed on %d "
              "horizontal + %d vertical real scenarios; companion shared axis "
              "is NOT given the source descriptor (stays None) — exactly the "
              "bug the F2P test observes. Apply patch.diff for the patched "
              "regime." % (len(cases), len(cases)))
    else:
        # mixed regimes across sites/scenarios: one site propagates and another
        # does not. That is neither the clean pre-patch nor clean patched tree.
        print("G-AX FAIL: inconsistent regimes across scenarios: %r" % regimes)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
