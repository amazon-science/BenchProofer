#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-23314.

This bundle consumes NO `@ContractOnly` axiom: the only callee the changed code
invokes is the unchanged accessor `get_visible()`, modeled directly as a boolean
field read. What G-AX validates here are the two behavioral A-references the
refinement leans on, by executing the REAL matplotlib code in-container:

  (a) Accessor faithfulness — `Artist.get_visible()` returns exactly the stored
      visibility flag, so `set_visible(b)` => `get_visible() == b`. This is the
      boolean read `self.visible` the model uses (model.py / mapping.md §3a).

  (b) Guard semantics reference — a 3D axes (`Axes3D`) flagged not-visible
      delivers NO rendering work to the renderer, while a visible one delivers
      its full body; matching the sibling 2D path `_AxesBase.draw`, which has
      always carried `if not self.get_visible(): return`. This is the
      content==0 (invisible) vs content>0 (visible) discrimination of clauses
      (1)/(2) in model.py.

We count rendering work with a recording renderer (a RendererBase subclass that
tallies every draw_* call). An invisible axes must leave the tally at zero
(sink unchanged, clause 1); a visible axes with drawn content must raise it
(clause 2). The check runs on BOTH the post-gold source (where the invisible
case must draw nothing) and demonstrates the discrimination is real (a visible
axes draws). Exit 0 iff every obligation holds.

Imports only matplotlib (the package the gold patch lives in) and the stdlib.
"""
import sys


def _make_recording_renderer():
    """A RendererBase that tallies every drawing primitive it is asked for."""
    import matplotlib.backend_bases as backend_bases

    class RecordingRenderer(backend_bases.RendererBase):
        def __init__(self):
            super().__init__()
            self.draw_calls = 0

        # Count every primitive the artists push to the backend.
        def draw_path(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_markers(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_path_collection(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_image(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_text(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_gouraud_triangle(self, *args, **kwargs):
            self.draw_calls += 1

        def draw_gouraud_triangles(self, *args, **kwargs):
            self.draw_calls += 1

        # Width/height/dpi like the default Agg page.
        def get_canvas_width_height(self):
            return 100.0, 100.0

    return RecordingRenderer()


def _draw_calls_for(visible):
    """Build a 3D axes with some content, set its visibility, draw it onto a
    recording renderer, and return the number of draw primitives emitted."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registers '3d')

    fig = plt.figure()
    ax = fig.add_subplot(projection="3d")
    # Give the axes real drawable content (matches the issue's scatter repro).
    ax.scatter([1, 2, 3], [1, 2, 3], [1, 2, 3])

    ax.set_visible(visible)

    # (a) accessor faithfulness: get_visible() returns exactly what we set.
    assert ax.get_visible() is bool(visible), (
        "Artist.get_visible() did not return the stored flag: set %r, got %r"
        % (visible, ax.get_visible()))

    fig.canvas.draw()  # ensure transforms/limits are realized

    renderer = _make_recording_renderer()
    ax.draw(renderer)
    calls = renderer.draw_calls
    plt.close(fig)
    return calls


def main():
    # (b) the guard-semantics reference, executed on the REAL Axes3D.draw.
    invisible_calls = _draw_calls_for(False)
    visible_calls = _draw_calls_for(True)

    # Clause (1): an invisible 3D axes performs NO rendering work.
    assert invisible_calls == 0, (
        "invisible Axes3D still emitted %d draw primitives (expected 0): the "
        "visibility guard is not honoured" % invisible_calls)

    # Clause (2): a visible 3D axes with content performs work — so the
    # content==0 vs content>0 discrimination of the model is real and the
    # spec is not vacuously satisfiable.
    assert visible_calls > 0, (
        "visible Axes3D emitted no draw primitives (expected > 0): the "
        "recording renderer is not observing the render body")

    print("G-AX OK: Axes3D.draw honours get_visible() — invisible emits 0 draw "
          "primitives, visible emits %d; accessor faithfulness confirmed "
          "(set_visible(b) => get_visible()==b)." % visible_calls)
    return 0


if __name__ == "__main__":
    sys.exit(main())
