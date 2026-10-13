#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-20676.

Executes the REAL Matplotlib callee (`matplotlib.widgets.ToolLineHandles`) and
the end-to-end interactive `SpanSelector` construction, asserting that every
observation matches the model in model.py.

Two kinds of check:

  (A-reference) the deep model `reported_positions` (model.py axioms region) is
      the IDENTITY on the supplied coordinates. We build the real
      `ToolLineHandles(ax, positions, direction)` for both directions and
      assert `.positions == list(positions)` — i.e. the widget reports the
      coordinates it was constructed with, unchanged.

  (discriminator) the model's pinned cause — initial marker positions equal the
      orientation's CURRENT axis bound — is exactly the tested effect. Building
      the interactive SpanSelector leaves `ax.get_xbound()`/`get_ybound()`
      unchanged and yields `_edge_handles.positions == list(bound)`. We also
      reproduce the pre-patch behaviour (positions = (0, 0)) and confirm it DOES
      expand the bound, so the model's discriminating postcondition is the real
      discriminator.

Imports only `matplotlib` (the very module the gold patch changes) + numpy
(its dependency). Uses the headless Agg backend. Exit 0 iff every obligation
holds.
"""
import sys
import random

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector, ToolLineHandles


def check_handle_positions_identity(positions, direction):
    """A-reference: the real ToolLineHandles reports supplied positions back
    unchanged (model.py `reported_positions` is the identity)."""
    fig, ax = plt.subplots(1, 1)
    try:
        handles = ToolLineHandles(ax, positions, direction)
        observed = handles.positions
        expected = list(positions)
        assert observed == expected, (
            "handle_positions identity unsound: ToolLineHandles(%r, %r).positions"
            " gave %r, model identity requires %r"
            % (direction, positions, observed, expected))
    finally:
        plt.close(fig)


def check_end_to_end(direction):
    """The pinned cause == the tested effect: building the interactive selector
    leaves the bound unchanged and the markers sit on the orientation's bound."""
    fig, ax = plt.subplots(1, 1)
    try:
        ax.plot([10, 20], [10, 30])
        ax.figure.canvas.draw()
        x_bound = ax.get_xbound()
        y_bound = ax.get_ybound()

        tool = SpanSelector(ax, print, direction, interactive=True)

        # constructing the interactive selector must not move the bounds
        assert ax.get_xbound() == x_bound, (
            "x bound changed by construction: %r -> %r"
            % (x_bound, ax.get_xbound()))
        assert ax.get_ybound() == y_bound, (
            "y bound changed by construction: %r -> %r"
            % (y_bound, ax.get_ybound()))

        # markers sit on the orientation's current bound (model A3/A4)
        bound = x_bound if direction == "horizontal" else y_bound
        assert tool._edge_handles.positions == list(bound), (
            "edge handle positions %r != orientation bound %r"
            % (tool._edge_handles.positions, list(bound)))
    finally:
        plt.close(fig)


def check_prepatch_does_expand(direction):
    """Confirm the model's discriminator is real: supplying the pre-patch
    (0, 0) extents to the marker widget DOES expand the bound (so the spec's
    pinned cause genuinely distinguishes fixed from buggy)."""
    fig, ax = plt.subplots(1, 1)
    try:
        ax.plot([10, 20], [10, 30])
        ax.figure.canvas.draw()
        bound_attr = "get_xbound" if direction == "horizontal" else "get_ybound"
        before = getattr(ax, bound_attr)()
        # pre-patch: positions came from the degenerate extents (0, 0)
        ToolLineHandles(ax, (0, 0), direction)
        ax.figure.canvas.draw()
        after = getattr(ax, bound_attr)()
        assert after != before, (
            "expected pre-patch (0,0) handles to expand %s, but %r == %r "
            "(discriminator not real)" % (direction, before, after))
        assert after[0] <= 0, (
            "expected pre-patch (0,0) handles to drag the lower %s bound down "
            "to include 0, got %r" % (direction, after))
    finally:
        plt.close(fig)


def main():
    # --- A-reference: ToolLineHandles position pass-through identity ---------
    boundary = [
        (10, 20), (0, 0), (-5, 5), (10, 10), (20, 10),
        (10.5, 11.5), (-1.25, 3.75), (1000000, 1000001),
    ]
    for direction in ("horizontal", "vertical"):
        for positions in boundary:
            check_handle_positions_identity(positions, direction)

    rng = random.Random(20676)
    for _ in range(2000):
        lo = rng.uniform(-1000, 1000)
        hi = rng.uniform(-1000, 1000)
        positions = (lo, hi)
        for direction in ("horizontal", "vertical"):
            check_handle_positions_identity(positions, direction)

    # --- discriminator: end-to-end + pre-patch contrast ----------------------
    for direction in ("horizontal", "vertical"):
        check_end_to_end(direction)
        check_prepatch_does_expand(direction)

    print("G-AX OK: ToolLineHandles position pass-through identity sound on "
          "%d boundary + 2000 fuzz position pairs (x2 directions); interactive "
          "SpanSelector leaves bounds unchanged with markers on the orientation "
          "bound, while pre-patch (0,0) handles do expand the bound."
          % len(boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
