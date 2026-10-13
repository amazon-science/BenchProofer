#!/usr/bin/env python3
"""G-AX executable soundness check for mwaskom__seaborn-3069.

model.py carries one consumed @ContractOnly axiom and two deep-model references.

  (A-consumed) `slot_count() -> int` abstracts the unchanged tick-querying
      routine the finalizer queries for a categorical axis:
        len(axis_obj.get_major_ticks())
      The axiom's Ensures is the weakest fact the proof needs:
        a categorical axis has at least one category slot, slot_count() >= 1.
      This is a property of matplotlib's tick API (unchanged by the patch); we
      run the real categorical axis and assert the major-tick count is >= 1 and
      equals the number of categories (so the n-0.5 upper edge is grounded in
      the real count).

  (A-reference) the deep model `finalize_axis_range(is_categorical, has_explicit,
      is_vertical, user_lo, user_hi)` == the REAL finalized axis range. For a
      categorical axis with no explicit caller range the real range is exactly
      (-0.5, n-0.5) on x and (n-0.5, -0.5) on y (inverted); an explicit caller
      range is used verbatim; an ORDINARY (non-categorical) axis without an
      explicit caller range is left at its pre-existing automatic-margin range
      — the finalizer never touches it (the categorical special-casing is
      gated on isinstance(..., Nominal)), so in particular the categorical
      (-0.5, n-0.5) tuple is NEVER imposed on it. We run the real seaborn Plot
      and read get_xlim() / get_ylim() and assert they equal the model's
      prediction.

  (A-reference) the deep model `finalize_axis_grid(is_categorical,
      pre_visible)` == the REAL gridline visibility: a categorical axis draws
      no visible gridlines whatever visibility it carried into finalization
      (checked under both a grid-drawing and a grid-suppressing rc theme),
      while an ORDINARY axis keeps exactly the visibility it had immediately
      before the finalizer ran — the finalizer never touches it (checked by
      capturing the pre-finalization gridline visibility and comparing, under
      both themes).

These mirror the F2P assertions exactly:
  Plot(x=["a","b","c"], y=[1,2,3]) -> xlim == (-.5, 2.5), no visible x gridlines
  Plot(x=[1,2,3], y=["a","b","c"]) -> ylim == (2.5, -.5), no visible y gridlines
  .limit(x=(-1, 2.1)) -> xlim == (-1, 2.1)   (explicit range used verbatim)
and the P2P behaviour the identity clause protects (the sub-domain a rival
that drops the is_categorical gate would clobber — the recorded G-EQ attack):
  a continuous axis finalizes with its range untouched (== the range captured
  immediately before _finalize_figure ran, never the categorical (-0.5, n-0.5)
  tuple), including a log-scaled axis, whose log transform stays intact
  (mirrors test_faceted_log_scale / test_paired_single_log_scale).

Imports nothing repo-specific beyond seaborn itself (the package the gold patch
lives in) + matplotlib. Exit 0 iff every obligation holds.
"""
import sys


# --- model.py reference encodings (kept in lock-step with the spec) ----------

def model_axis_range(is_categorical, has_explicit, is_vertical,
                     user_lo, user_hi, n):
    """Reference implementation of model.py's deep model `finalize_axis_range`,
    with slot_count() instantiated to the measured category count n."""
    lo, hi = user_lo, user_hi
    if has_explicit:
        lo, hi = user_lo, user_hi
    elif is_categorical:
        lo, hi = -0.5, n - 0.5
        if is_vertical:
            lo, hi = hi, lo
    return (lo, hi)


def model_grid_visible(is_categorical, pre_visible):
    """Reference implementation of model.py's deep model `finalize_axis_grid`."""
    if is_categorical:
        return False
    return pre_visible


# --- driving the REAL seaborn Plot -------------------------------------------

def real_plot_axis(xvals, yvals, limit_kw=None, theme_rc=None):
    """Build and finalize a real seaborn Plot; return the finalized Axes."""
    import matplotlib
    matplotlib.use("Agg")
    from seaborn._core.plot import Plot

    p = Plot(x=xvals, y=yvals)
    if limit_kw is not None:
        p = p.limit(**limit_kw)
    if theme_rc is not None:
        p = p.theme(theme_rc)
    fig = p.plot()._figure
    return fig.axes[0]


def gridlines_visible(axis_obj):
    return any(g.get_visible() for g in axis_obj.get_gridlines())


def check_nominal_x(cats, ydata, theme_rc=None):
    """Categorical x axis, no explicit range: range == (-0.5, n-0.5), no grid;
    also validate the slot_count() >= 1 axiom against the real major-tick count."""
    n = len(cats)
    ax = real_plot_axis(cats, ydata, theme_rc=theme_rc)

    # A-consumed: slot_count() axiom — major-tick count is >= 1 and equals n.
    nticks = len(ax.xaxis.get_major_ticks())
    assert nticks >= 1, (
        "slot_count axiom UNSOUND: categorical x axis reported %d major ticks "
        "(< 1) for categories %r" % (nticks, cats))
    assert nticks == n, (
        "slot_count grounding broken: categorical x axis reported %d major "
        "ticks but there are %d categories %r" % (nticks, n, cats))

    # A-reference: the real finalized range == the model prediction.
    expected = model_axis_range(True, False, False, None, None, nticks)
    observed = tuple(ax.get_xlim())
    assert observed == expected, (
        "range deep-model UNSOUND on categorical x (cats=%r): real get_xlim()=%r,"
        " model gives %r" % (cats, observed, expected))

    # A-reference: gridlines off (model_grid_visible(True, anything) is False,
    # whatever visibility the active theme would have given the axis).
    assert gridlines_visible(ax.xaxis) == model_grid_visible(True, True) == \
        model_grid_visible(True, False), (
        "grid deep-model UNSOUND: categorical x axis has visible gridlines "
        "(model predicts none) for cats=%r theme=%r" % (cats, theme_rc))


def check_nominal_y(cats, xdata, theme_rc=None):
    """Categorical y axis, no explicit range: range == (n-0.5, -0.5) inverted,
    no grid."""
    n = len(cats)
    ax = real_plot_axis(xdata, cats, theme_rc=theme_rc)

    nticks = len(ax.yaxis.get_major_ticks())
    assert nticks >= 1, (
        "slot_count axiom UNSOUND: categorical y axis reported %d major ticks "
        "(< 1) for categories %r" % (nticks, cats))
    assert nticks == n, (
        "slot_count grounding broken: categorical y axis reported %d major "
        "ticks but there are %d categories %r" % (nticks, n, cats))

    expected = model_axis_range(True, False, True, None, None, nticks)
    observed = tuple(ax.get_ylim())
    assert observed == expected, (
        "range deep-model UNSOUND on categorical y (cats=%r): real get_ylim()=%r,"
        " model gives %r" % (cats, observed, expected))

    assert gridlines_visible(ax.yaxis) == model_grid_visible(True, True) == \
        model_grid_visible(True, False), (
        "grid deep-model UNSOUND: categorical y axis has visible gridlines "
        "(model predicts none) for cats=%r theme=%r" % (cats, theme_rc))


def check_explicit_x(cats, ydata, lim):
    """Categorical x axis WITH an explicit caller range: range used verbatim."""
    ax = real_plot_axis(cats, ydata, limit_kw={"x": lim})
    expected = model_axis_range(True, True, False, lim[0], lim[1], len(cats))
    observed = tuple(ax.get_xlim())
    assert observed == expected, (
        "explicit-range deep-model UNSOUND on categorical x (cats=%r, lim=%r): "
        "real get_xlim()=%r, model gives %r" % (cats, lim, observed, expected))


def check_explicit_y(cats, xdata, lim):
    ax = real_plot_axis(xdata, cats, limit_kw={"y": lim})
    expected = model_axis_range(True, True, True, lim[0], lim[1], len(cats))
    observed = tuple(ax.get_ylim())
    assert observed == expected, (
        "explicit-range deep-model UNSOUND on categorical y (cats=%r, lim=%r): "
        "real get_ylim()=%r, model gives %r" % (cats, lim, observed, expected))


def check_continuous_untouched(xdata, ydata, theme_rc=None):
    """Ordinary (non-categorical) axis, no explicit range: the finalizer leaves
    the pre-existing range alone (the identity clause, !is_categorical &
    !has_explicit -> Result == (user_lo, user_hi)) AND the pre-existing grid
    visibility alone (the grid identity clause, !is_categorical -> Result ==
    pre_visible). Ground both directly: capture the real range and gridline
    visibility IMMEDIATELY BEFORE Plotter._finalize_figure runs (those are
    user_lo/user_hi and pre_visible) and assert the finalized values equal
    them — the finalizer touched nothing. A gate-dropping rival (the recorded
    G-EQ attack) would instead impose the categorical (-0.5, n-0.5) tuple
    here; a grid-forcing rival would flip the gridline visibility. Run under
    the caller's theme_rc so pre_visible takes BOTH truth values across the
    main() sweep."""
    import matplotlib
    matplotlib.use("Agg")
    from seaborn._core.plot import Plot, Plotter

    captured = {}
    orig = Plotter._finalize_figure

    def capture_then_finalize(self, p):
        for ax_ in self._figure.axes:
            captured[id(ax_)] = (tuple(ax_.get_xlim()), tuple(ax_.get_ylim()),
                                 gridlines_visible(ax_.xaxis),
                                 gridlines_visible(ax_.yaxis))
        return orig(self, p)

    Plotter._finalize_figure = capture_then_finalize
    try:
        p = Plot(x=xdata, y=ydata)
        if theme_rc is not None:
            p = p.theme(theme_rc)
        fig = p.plot()._figure
    finally:
        Plotter._finalize_figure = orig
    ax = fig.axes[0]
    pre_x, pre_y, pre_gx, pre_gy = captured[id(ax)]
    observed_x = tuple(ax.get_xlim())
    observed_y = tuple(ax.get_ylim())

    assert observed_x == model_axis_range(False, False, False,
                                          pre_x[0], pre_x[1], None), (
        "identity clause UNSOUND on continuous x (x=%r): finalized get_xlim()="
        "%r, pre-finalization range was %r — the finalizer must leave a "
        "non-categorical, non-explicit axis alone" % (xdata, observed_x, pre_x))
    assert observed_y == model_axis_range(False, False, True,
                                          pre_y[0], pre_y[1], None), (
        "identity clause UNSOUND on continuous y (y=%r): finalized get_ylim()="
        "%r, pre-finalization range was %r" % (ydata, observed_y, pre_y))

    # grid identity: the finalized gridline visibility equals the model's
    # prediction from the captured pre-finalization visibility.
    obs_gx = gridlines_visible(ax.xaxis)
    obs_gy = gridlines_visible(ax.yaxis)
    assert obs_gx == model_grid_visible(False, pre_gx), (
        "grid identity clause UNSOUND on continuous x (x=%r, theme=%r): "
        "finalized gridline visibility %r, pre-finalization was %r — the "
        "finalizer must leave an ordinary axis's grid alone"
        % (xdata, theme_rc, obs_gx, pre_gx))
    assert obs_gy == model_grid_visible(False, pre_gy), (
        "grid identity clause UNSOUND on continuous y (y=%r, theme=%r): "
        "finalized gridline visibility %r, pre-finalization was %r"
        % (ydata, theme_rc, obs_gy, pre_gy))
    return pre_gx, pre_gy


def check_log_scale_untouched():
    """The P2P behaviour the recorded G-EQ attack broke (mirrors
    test_faceted_log_scale / test_paired_single_log_scale): finalizing a
    figure with a log-scaled continuous axis must complete (the gate-dropping
    rival crashed inside get_major_ticks with vmin=inf when it forced the
    categorical range onto the log axis), keep the log transform intact
    (transform([1,10,100]) == [0,1,2] — the tests' exact assertion), and leave
    the finalized range identical to the pre-finalization range (the identity
    clause)."""
    import matplotlib
    matplotlib.use("Agg")
    from seaborn._core.plot import Plot, Plotter

    captured = {}
    orig = Plotter._finalize_figure

    def capture_then_finalize(self, p):
        for ax_ in self._figure.axes:
            captured[id(ax_)] = tuple(ax_.get_ylim())
        return orig(self, p)

    Plotter._finalize_figure = capture_then_finalize
    try:
        fig = Plot(y=[1, 10, 100]).scale(y="log").plot()._figure
    finally:
        Plotter._finalize_figure = orig
    ax = fig.axes[0]

    pre_y = captured[id(ax)]
    observed_y = tuple(ax.get_ylim())
    assert observed_y == model_axis_range(False, False, True,
                                          pre_y[0], pre_y[1], None), (
        "identity clause UNSOUND: log-scaled continuous y axis finalized to "
        "%r but the pre-finalization range was %r — the finalizer must leave "
        "a non-categorical, non-explicit axis alone" % (observed_y, pre_y))
    xfm = ax.yaxis.get_transform().transform
    got = [float(v) for v in xfm([1, 10, 100])]
    assert got == [0.0, 1.0, 2.0], (
        "identity clause UNSOUND: log transform broken on continuous y axis "
        "(transform([1,10,100]) == %r, expected [0,1,2])" % (got,))


def main():
    # --- exact F2P witnesses -------------------------------------------------
    check_nominal_x(["a", "b", "c"], [1, 2, 3])          # xlim == (-.5, 2.5)
    check_nominal_y(["a", "b", "c"], [1, 2, 3])          # ylim == (2.5, -.5)
    check_explicit_x(["a", "b", "c"], [1, 2, 3], (-1, 2.1))
    check_explicit_y(["a", "b", "c"], [1, 2, 3], (-1, 2.1))

    # categorical grid-off must hold under BOTH a grid-drawing and a
    # grid-suppressing rc theme (model_grid_visible(True, *) is False for
    # either pre-visibility).
    check_nominal_x(["a", "b", "c"], [1, 2, 3], theme_rc={"axes.grid": True})
    check_nominal_x(["a", "b", "c"], [1, 2, 3], theme_rc={"axes.grid": False})
    check_nominal_y(["a", "b", "c"], [1, 2, 3], theme_rc={"axes.grid": True})
    check_nominal_y(["a", "b", "c"], [1, 2, 3], theme_rc={"axes.grid": False})

    # --- identity clauses: ordinary axes left untouched (P2P protection) -----
    # Both the range and the grid visibility must survive finalization
    # unchanged; sweep themes so pre_visible takes both truth values.
    seen_pre_vis = set()
    for rc in (None, {"axes.grid": True}, {"axes.grid": False}):
        gx, gy = check_continuous_untouched([1, 2, 3], [1, 2, 3], theme_rc=rc)
        seen_pre_vis.update((gx, gy))
        check_continuous_untouched([0.5, 1.5, 2.5, 3.5], [10, 20, 5, 40],
                                   theme_rc=rc)
    assert seen_pre_vis == {True, False}, (
        "grid identity coverage incomplete: pre-finalization visibility only "
        "took values %r across the theme sweep — both truth values of "
        "pre_visible must be exercised" % (seen_pre_vis,))
    check_log_scale_untouched()

    # --- boundary + fuzz over category count and content ---------------------
    import string
    n_checked = 0
    for n in range(1, 13):
        cats = list(string.ascii_lowercase[:n])
        ydata = list(range(n))
        check_nominal_x(cats, ydata)                     # (-0.5, n-0.5)
        check_nominal_y(cats, ydata)                     # (n-0.5, -0.5)
        n_checked += 2
        # explicit caller ranges of several shapes are used verbatim
        for lim in [(-1.0, 2.1), (0.0, 10.0), (-5.0, 5.0)]:
            check_explicit_x(cats, ydata, lim)
            check_explicit_y(cats, ydata, lim)
            n_checked += 2

    print("G-AX OK: slot_count axiom (>=1 major ticks, == #categories) sound; "
          "range deep-model == real get_xlim/get_ylim and grid deep-model == "
          "real gridline visibility on the 4 F2P witnesses + %d categorical "
          "axes (n=1..12, x & y) + verbatim explicit ranges + both grid rc "
          "themes; identity clauses grounded (continuous axes finalize with "
          "their pre-finalization range AND gridline visibility untouched, "
          "across both pre_visible truth values, incl. log-scaled with intact "
          "transform). 0 violations." % (n_checked,))
    return 0


if __name__ == "__main__":
    sys.exit(main())
