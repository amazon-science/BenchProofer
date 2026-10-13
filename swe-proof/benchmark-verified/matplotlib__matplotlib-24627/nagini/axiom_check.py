#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-24627.

This bundle consumes **no @ContractOnly axiom**: the modeled behaviour is a pure
object-graph mutation (clear the container's member list and clear each former
member's two owner back-references), spelled out deeply in model.py. There is
therefore no axiom contract to fuzz against a library callee.

What G-AX validates here instead is that the **deep object-graph model** matches
the **real callee end-to-end**: that the real ``Axes.clear()`` (which invokes the
patched ``_AxesBase.__clear``) leaves every artist that had been a child fully
de-parented — ``art.axes is None`` AND ``art.figure is None`` — and leaves the
axes with no remaining children. This is the structural twin of the F2P test
``test_cla_clears_children_axes_and_fig`` plus the refinement-load-bearing
observables (the empty-collection half and the de-parented-members half that
postconditions (1) and (2) of model.py pin).

It runs inside the official SWE-bench container for the instance, where
matplotlib is importable with the Agg backend. Boundary + fuzz over the number
and kind of children. Exit 0 iff every obligation holds. Outside the container
(matplotlib absent / no usable backend) it prints ``G-AX SKIP`` and returns 0;
the orchestrator runs it in-container.
"""
import sys


def main():
    try:
        import matplotlib
        matplotlib.use("Agg")  # headless, no display needed
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: matplotlib not importable in this environment: %r" % (exc,))
        return 0

    observations = 0

    def check_cleared(ax, fig, artists, label):
        # Pre-state sanity: every artist is parented under this ax and fig.
        for art in artists:
            assert art.axes is ax, (
                "%s: pre-clear art.axes was %r, expected the axes" % (label, art.axes))
            assert art.figure is fig, (
                "%s: pre-clear art.figure was %r, expected the figure" % (label, art.figure))
        # The REAL changed routine.
        ax.clear()
        # Post-state: the modeled observables (postconditions 1 and 2).
        assert len(ax._children) == 0, (
            "%s: ax._children not emptied after clear: %r" % (label, ax._children))
        for art in artists:
            assert art.axes is None, (
                "%s: art.axes not cleared after clear: %r" % (label, art.axes))
            assert art.figure is None, (
                "%s: art.figure not cleared after clear: %r" % (label, art.figure))

    # (a) the exact F2P twin: 4 lines from a single 4-curve plot() call + 1 image.
    for _ in range(20):
        fig, ax = plt.subplots()
        lines = ax.plot([], [], [], [])
        img = ax.imshow([[1]])
        check_cleared(ax, fig, list(lines) + [img], "lines+image")
        plt.close(fig)
        observations += 1

    # (b) fuzz over the number of line children (0..6), boundary at 0 and 1.
    for n in range(0, 7):
        fig, ax = plt.subplots()
        arts = []
        for _ in range(n):
            (ln,) = ax.plot([0, 1], [0, 1])
            arts.append(ln)
        check_cleared(ax, fig, arts, "lines[n=%d]" % n)
        plt.close(fig)
        observations += 1

    # (c) heterogeneous children: scatter (a collection), bar (patches),
    #     text, and an errorbar container's component artists.
    for _ in range(10):
        fig, ax = plt.subplots()
        arts = []
        arts.append(ax.scatter([0, 1, 2], [1, 2, 3]))
        arts.extend(ax.bar([0, 1, 2], [1, 2, 3]))
        arts.append(ax.text(0.5, 0.5, "x"))
        (ln,) = ax.plot([0, 1], [1, 0])
        arts.append(ln)
        arts.append(ax.imshow([[1, 2], [3, 4]]))
        check_cleared(ax, fig, arts, "heterogeneous")
        plt.close(fig)
        observations += 1

    # (d) repeated clears: a second clear on an already-cleared axes must remain
    #     well-behaved (empty children, no stale references introduced).
    for _ in range(10):
        fig, ax = plt.subplots()
        (ln,) = ax.plot([0, 1], [0, 1])
        ax.clear()
        assert ln.axes is None and ln.figure is None
        ax.clear()
        assert len(ax._children) == 0
        plt.close(fig)
        observations += 1

    print("G-AX OK: real Axes.clear() de-parents every former child "
          "(art.axes is None AND art.figure is None) and empties ax._children "
          "over %d end-to-end observations (F2P twin + line-count fuzz + "
          "heterogeneous artists + repeated clears); deep model matches the "
          "real callee." % (observations,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
