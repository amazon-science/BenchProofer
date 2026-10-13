#!/usr/bin/env python3
"""G-AX executable soundness check for matplotlib__matplotlib-26291.

Runs in-container (the prebuilt SWE-Bench instance image) against the UNCHANGED
repo at base_commit — G-AX does NOT apply patch.diff (that is G-CONF/G-RESOLVE's
job). Imports only the repo under test (matplotlib / mpl_toolkits) + the Python
standard library. Exit 0 iff every obligation holds.

The changed function is `AnchoredLocatorBase.__call__(self, ax, renderer)`
(lib/mpl_toolkits/axes_grid1/inset_locator.py:71). It CALLS, but does NOT change:

  (A-consumed, opaque) `hostContext` == `ax.figure._get_renderer()`
      (matplotlib.figure.FigureBase._get_renderer). The Lean axiom is fully
      OPAQUE (no `ensures`), so there is no contract strength to refute; the only
      obligation is that it is a total, deterministic `Host -> Ctx` op — every
      real host axes yields a drawing context. G-AX witnesses this on a real
      `inset_axes`-created locator's host figure.

  (A-consumed, opaque) `placeWith` == the unchanged measure -> offset ->
      transform pipeline of `__call__` given a CONCRETE context. Total and
      deterministic given a concrete context. Witnessed by feeding the unchanged
      `__call__` a concrete renderer and observing it returns a region, and that
      two calls with the same concrete context yield equal region extents.

  (A-reference) the deep context-substitution model encodes the CHECKED bug
      fact and the substitution, validated against the UNCHANGED callees:
        * the `none => hostContext host` fallback: an ABSENT context fed straight
          into the unchanged downstream (`__call__(ax, None)` /
          `get_window_extent(None)`) RAISES AttributeError on the figure-less
          locator artist — `self.figure` is None (the bug; why the substitution
          is load-bearing). G-AX asserts the unchanged path raises.
        * the substituted concrete context (`hostContext host`) fed into the
          UNCHANGED downstream returns a region — i.e.
          `placeWith (hostContext host) host` is well-defined and equals running
          `__call__` with the host figure's renderer. This witnesses that the
          modeled `none` fallback makes the downstream succeed, using only the
          unchanged callees (no patch). The end-to-end "patched __call__(ax,None)
          returns a region" is validated separately by G-CONF / G-RESOLVE, which
          DO apply patch.diff.
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1.inset_locator import inset_axes


def _bounds(bbox):
    """Observable extent of a region (mapping.md §2: region equality == extent)."""
    return (round(bbox.x0, 6), round(bbox.y0, 6),
            round(bbox.x1, 6), round(bbox.y1, 6))


def main():
    checks = 0

    # Build a real locator the way the issue + F2P test do.
    fig, ax = plt.subplots()
    inset = inset_axes(ax, width=1.3, height=0.9)
    locator = inset.get_axes_locator()       # AnchoredSizeLocator (AnchoredLocatorBase)
    host = inset                              # the `ax` arg threaded into __call__

    # A concrete drawing context (the host figure's renderer).
    fig.canvas.draw()

    # ---- (A-consumed, opaque) hostContext: total + deterministic Host->Ctx ----
    r1 = host.figure._get_renderer()
    r2 = host.figure._get_renderer()
    assert r1 is not None, "ax.figure._get_renderer() returned None (not total)"
    assert r2 is not None, "ax.figure._get_renderer() returned None (not total)"
    # type-stable retrieval (the value the substitution threads into the pipeline)
    assert type(r1) is type(r2), "host context retrieval not type-stable"
    checks += 1

    # the locator artist is genuinely figure-less — the precondition that makes
    # the absent-context path undefined on the UNCHANGED downstream (mapping.md §1).
    assert getattr(locator, "figure", None) is None, (
        "expected the locator artist to have no figure (self.figure is None); "
        "got %r" % getattr(locator, "figure", None))
    checks += 1

    # ---- (A-consumed, opaque) placeWith: total + deterministic given a context ----
    # The UNCHANGED __call__ given a CONCRETE renderer is the downstream pipeline.
    reg_a = locator(host, r1)
    reg_b = locator(host, r1)
    assert reg_a is not None and reg_b is not None, "placeWith returned None"
    assert _bounds(reg_a) == _bounds(reg_b), (
        "placeWith not deterministic given a concrete context: %r vs %r"
        % (_bounds(reg_a), _bounds(reg_b)))
    checks += 1

    # ---- (A-reference) the bug fact: absent context -> unchanged callee raises ----
    # The UNCHANGED __call__(ax, None) feeds None straight into get_window_extent,
    # which hits `self.figure._get_renderer()` with self.figure is None ->
    # AttributeError. This is why the impl's `none => hostContext host` fallback is load-bearing.
    raised = False
    try:
        locator(host, None)
    except AttributeError as e:
        raised = True
        assert "_get_renderer" in str(e) or "NoneType" in str(e), (
            "unexpected AttributeError text: %r" % (str(e),))
    assert raised, (
        "expected the unchanged __call__(ax, None) to raise AttributeError on "
        "the figure-less locator (the bug witness) — it did not")
    checks += 1

    # also directly through get_window_extent(None) (the exact raising frame)
    raised_gwe = False
    try:
        locator.get_window_extent(None)
    except AttributeError as e:
        raised_gwe = True
        assert "_get_renderer" in str(e) or "NoneType" in str(e), (
            "unexpected AttributeError text from get_window_extent: %r" % (str(e),))
    assert raised_gwe, (
        "expected the unchanged get_window_extent(None) to raise AttributeError "
        "on the figure-less locator — it did not")
    checks += 1

    # ---- (A-reference) the substitution makes the UNCHANGED downstream succeed --
    # The model's `none` branch substitutes hostContext host, then computes
    # placeWith (hostContext host) host. Validate it against the UNCHANGED
    # callees: feeding the substituted CONCRETE context into the unchanged
    # __call__ returns a region equal to running with the host figure's renderer.
    # (No patch needed — the substitution is modeled deeply; the patched
    #  end-to-end is G-CONF/G-RESOLVE's job.)
    reg_sub = locator(host, host.figure._get_renderer())   # placeWith (hostContext host) host
    assert reg_sub is not None, (
        "placeWith (hostContext host) host is undefined — the modeled substitution "
        "does not yield a region")
    assert _bounds(reg_sub) == _bounds(reg_a), (
        "substituted-context placement != host-context placement: %r vs %r — the "
        "modeled fallback none => hostContext host is not exactly the "
        "host figure's context fed to the downstream"
        % (_bounds(reg_sub), _bounds(reg_a)))
    checks += 1

    # ---- present context passes through unchanged (the some-branch passes the arg) ----
    reg_some = locator(host, r1)
    assert _bounds(reg_some) == _bounds(reg_a), (
        "present-context placement not stable")
    checks += 1

    plt.close(fig)
    print("G-AX OK: hostContext (ax.figure._get_renderer) total+deterministic; "
          "placeWith deterministic given a concrete context; the UNCHANGED "
          "__call__(ax, None) / get_window_extent(None) raises AttributeError on "
          "the figure-less locator (bug witness); the modeled substitution "
          "placeWith (hostContext host) host returns the host-context region "
          "against the unchanged downstream (fix model). %d obligations." % checks)
    return 0


if __name__ == "__main__":
    sys.exit(main())
