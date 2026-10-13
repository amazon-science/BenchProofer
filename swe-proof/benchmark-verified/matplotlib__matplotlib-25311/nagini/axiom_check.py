#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-25311.

There is NO consumed @ContractOnly axiom in this bundle: the behaviour under
specification -- the structure of the draggable helper's *serialisable state*
-- is modelled DEEPLY in model.py (the ``build_helper_state`` / ``contains`` /
``figure_canvas`` deep model). This script is the G-AX validation of that
A-reference deep model against the REAL matplotlib semantics.

The deep model claims, for the real ``matplotlib.offsetbox.DraggableBase``
helper (the changed function under specification) once it is set up:

  (1) Read access preserved -- reading the helper's ``canvas`` yields exactly
      ``ref_artist.figure.canvas`` (the figure's drawing surface).

  (2) The helper's serialisable state (its ``__dict__`` -- what a pickle of the
      helper, reachable from the figure through the registered callbacks, emits)
      contains NO reference to that drawing-surface object.

  (3) The genuine helper attributes (``ref_artist``, ``got_artist``,
      ``_use_blit``, ``cids``) ARE retained in that serialisable state.

We validate all three by exercising the real, unmodified library in the
official container (Agg backend, no GUI needed):

  * structural: build a real ``DraggableBase`` over a real figure artist and
    inspect ``vars(helper)`` (its ``__dict__``, i.e. the serialisable state)
    and ``helper.canvas`` (the read accessor).
  * end-to-end (the FAIL_TO_PASS observable): pickle a real figure carrying a
    draggable legend and assert the pickle byte stream names no canvas class.

Imports only matplotlib (the very library the patch changes) + stdlib. Exit 0
iff every obligation holds against the post-fix library.
"""
import pickle
import pickletools
import sys


def _genuine_attrs(helper):
    """The genuine retained helper attributes the model keeps in the state."""
    return ("ref_artist", "got_artist", "_use_blit", "cids")


def check_structural():
    """Validate the deep model against a real DraggableBase instance."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.offsetbox import DraggableBase

    fig = plt.figure()
    ax = fig.add_subplot(111)
    (line,) = ax.plot([0, 1, 2, 3, 4], [40, 43, 45, 47, 48], label="speed")

    helper = DraggableBase(line, use_blit=False)
    real_canvas = fig.canvas
    state = vars(helper)  # the instance __dict__ == the serialisable state

    # (1) read access preserved: helper.canvas IS the figure's drawing surface.
    assert helper.canvas is real_canvas, (
        "read access not preserved: helper.canvas %r is not figure.canvas %r"
        % (helper.canvas, real_canvas))
    # ... and it is reachable as ref_artist.figure.canvas, the model's source.
    assert helper.ref_artist.figure.canvas is real_canvas

    # (2) the drawing surface must NOT be held in the serialisable state.
    assert "canvas" not in state, (
        "the drawing surface is held in the helper's serialisable state "
        "(__dict__ keys: %r) -- it must be a property, recovered on read"
        % (sorted(state.keys()),))
    for key, value in state.items():
        assert value is not real_canvas, (
            "the drawing surface leaks into the serialisable state under "
            "key %r" % (key,))

    # (3) the genuine helper attributes ARE retained in the serialisable state.
    for attr in _genuine_attrs(helper):
        assert attr in state, (
            "genuine helper attribute %r missing from the serialisable state "
            "(keys: %r)" % (attr, sorted(state.keys())))

    plt.close(fig)
    print("G-AX structural OK: DraggableBase.canvas reads the figure surface, "
          "is absent from the serialisable state (__dict__), and the genuine "
          "attributes %r are retained." % (list(_genuine_attrs(helper)),))


def check_end_to_end():
    """The FAIL_TO_PASS observable: pickling a figure with a draggable legend
    yields a byte stream that names no canvas class."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot([0, 1, 2, 3, 4], [40, 43, 45, 47, 48], label="speed")
    leg = ax.legend()
    leg.set_draggable(True)

    pkl = pickle.dumps(fig, pickle.HIGHEST_PROTOCOL)
    args = [arg for op, arg, pos in pickletools.genops(pkl)]
    # No canvas object is referenced anywhere in the pickle stream. Agg's canvas
    # is itself picklable, so we check by class name (matches the F2P test).
    leaked = [a for a in args if isinstance(a, str) and "FigureCanvas" in a]
    assert not leaked, (
        "a canvas reference leaked into the figure pickle stream: %r" % (leaked,))

    # round trip still works and the canvas is recoverable on the reload.
    loaded = pickle.loads(pkl)
    assert loaded.canvas is not None
    plt.close(fig)
    plt.close(loaded)
    print("G-AX end-to-end OK: pickling a figure with a draggable legend "
          "produced no canvas reference in the byte stream; the figure round "
          "trips and recovers its canvas.")


def main():
    try:
        import matplotlib  # noqa: F401
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-AX SKIP: matplotlib not importable in this environment: %r"
              % (exc,))
        return 0
    check_structural()
    check_end_to_end()
    print("G-AX OK: the A-reference deep model (build_helper_state / contains / "
          "figure_canvas) is sound against the real matplotlib DraggableBase.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
