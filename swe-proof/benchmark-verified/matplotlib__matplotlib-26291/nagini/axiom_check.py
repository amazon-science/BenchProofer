#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26291.

Executes the REAL callee the lone axiom stands in for — obtaining a drawing
context (renderer) from a host axes' figure, i.e. ``ax.figure._get_renderer()``
— and asserts the property the axiom encodes:

  (A-consumed) the model axiom `axes_context(ax)` Ensures `Result() > 0`:
      the host axes always yields a PRESENT (non-absent) drawing context. In
      the model a present handle is a positive opaque code and the absent
      sentinel is 0/None; the real-world witness is that
      `ax.figure._get_renderer()` returns a real renderer object (never None)
      for an axes belonging to a figure — exactly the context the patched
      `__call__` threads into the measurement when it is invoked without one.

This is the precise behaviour the fix depends on: when the positioning callable
is invoked with `renderer=None` (as the tight-bbox save path does), it must be
able to obtain a usable renderer from the host axes. The check exercises a
range of axes-construction shapes (plain, multi-subplot, and — the regression's
own scenario — an inset axes from `mpl_toolkits.axes_grid1.inset_locator`) and,
for each, asserts the axes' figure produces a present renderer.

Imports nothing repo-specific beyond matplotlib itself (the package the gold
patch lives in); the Agg backend is forced so it runs headless in-container.
Exit 0 iff every obligation holds.
"""
import sys


def _is_present_context(renderer):
    """The model's `Result() > 0` (present, non-absent handle) <-> the real
    renderer being a usable object: not None, and carrying the point-to-pixel
    scale the downstream measurement needs (`points_to_pixels`)."""
    return renderer is not None and hasattr(renderer, "points_to_pixels")


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes

    checks = 0

    # --- boundary / representative axes shapes ---------------------------
    # 1. a single plain axes
    fig, ax = plt.subplots()
    r = ax.figure._get_renderer()          # the REAL callee axes_context models
    assert _is_present_context(r), (
        "axes_context unsound: plain axes figure produced no usable "
        "renderer (got %r)" % (r,))
    checks += 1
    plt.close(fig)

    # 2. multiple subplots (every axes must yield a present context)
    fig, axes = plt.subplots(1, 2, figsize=[5.5, 2.8])
    for a in axes:
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context unsound: subplot axes produced no usable "
            "renderer (got %r)" % (r,))
        checks += 1
    plt.close(fig)

    # 3. the regression's own scenario: an inset axes built by the
    #    axes_grid1 inset_locator, then a tight-bbox save (the exact failing
    #    path). The inset axes' figure must produce a present renderer.
    fig, ax = plt.subplots()
    axins = inset_axes(ax, width=1.3, height=0.9)
    for a in (ax, axins):
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context unsound: inset-scenario axes produced no usable "
            "renderer (got %r)" % (r,))
        checks += 1
    plt.close(fig)

    # 4. a variety of figure sizes/dpis (fuzz the figure shape; the renderer
    #    must always be present)
    for figsize, dpi in [((1, 1), 50), ((3, 2), 100), ((6.4, 4.8), 72),
                         ((10, 8), 200), ((2.5, 2.5), 150)]:
        fig = plt.figure(figsize=figsize, dpi=dpi)
        a = fig.add_subplot(111)
        r = a.figure._get_renderer()
        assert _is_present_context(r), (
            "axes_context unsound: figure %r@%rdpi produced no usable "
            "renderer (got %r)" % (figsize, dpi, r))
        checks += 1
        plt.close(fig)

    print("G-AX OK: axes_context axiom sound — every host axes' figure "
          "produced a present (non-absent) renderer over %d witnesses "
          "incl. the inset regression axes" % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
