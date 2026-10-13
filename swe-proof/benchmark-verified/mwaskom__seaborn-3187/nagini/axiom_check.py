#!/usr/bin/env python3
"""G-AX executable soundness check for mwaskom__seaborn-3187.

Runs REAL `matplotlib` numeric tick formatters over tick sets spanning small to
very large magnitudes, attached to axes whose numeric RANGE is varied
INDEPENDENTLY of those tick sets, through BOTH of the formatter APIs the modeled
legend sites use, and asserts that every observation matches the deep models
declared in model.py's axioms region:

    rendered_labels(convention, ticks, residual, view_lo, view_hi)
                                                 -> label sequence
    reading(label)                               -> the number the text reads as

The obligations checked here, in the same order the model states them:

  (A-consumed 1)  one label per tick, for EVERY convention, mode and axis
      range:
        len(rendered_labels(c, ticks, r, lo, hi)) == len(ticks)

  (A-consumed 2)  the ONE reading property the proofs rely on:
        convention == the default one and not residual
            ==> reading(rendered_labels(c, ticks, False, lo, hi)[k]) == ticks[k]
      i.e. the default formatter with residual rendering disabled factors
      nothing out, so every label reads back to its tick's FULL value, at every
      magnitude AND for every axis range -- including ranges much wider than
      the ticks, and ranges that do not contain them at all.

  (A-nonvacuity) the `not residual` hypothesis is load-bearing: with residual
      rendering enabled the same formatter renders large ticks as small
      residuals, whose readings are NOT the ticks -- so the model's guarantee is
      unattainable in that mode rather than automatic.

  (A-reference 1) a label is its TEXT, not its reading: the same tick renders
      to texts that differ while reading back to the same number, so a model
      that saw only readings could not tell the two apart.  This is why the
      model's label carrier is an opaque code for the exact text.

  (A-reference 2) a label is not a function of its tick alone: the same tick
      renders differently depending on the whole tick SET it is rendered with,
      which is why `rendered_labels` takes the set and returns the sequence.

  (A-reference 3) a label sequence is not a function of the tick set alone
      either: holding the convention, the mode and the tick set fixed and
      moving only the axis RANGE changes what several conventions render.  This
      is why the range is an argument of the deep model, and why a
      refinement may not render against the tick set's own span instead: the
      measured range-dependent conventions are reported.

  (A-guard) the convention guard on the reading property withholds nothing that
      is available: for some conventions other than the default, the labels do
      NOT read back to the ticks even with every residual-rendering control
      disabled, so no reading guarantee exists there to be claimed.  How many
      non-default (convention, tick set, range) triples the controls do move is
      MEASURED and reported rather than asserted, because it is a property of
      the matplotlib version in use, not of the modeled behaviour.

      Conversely the DEFAULT convention is exactly the one those controls do
      move: on a large tick set its labels differ with them disabled vs left
      alone.  So convention 0 is pinned to the formatter the modeled guarantee
      is about, not chosen to make the guarantee easy.

  (A-domain) exactly which (convention, tick set, range) triples the real callee
      has no label sequence for -- the domain restriction model.py's
      `rendered_labels` docstring discloses.  Two-sided, so it cannot be met by
      a vague excuse: any convention with no rendering for an axis range of no
      WIDTH must be one that chooses its unit from that width; every convention
      that does render one renders exactly one label per tick; on a range of
      non-zero width every convention renders; and an empty tick set renders
      (as the empty sequence) even on a range of no width.  The measured set is
      reported and may be empty (whether the width-reading unit formatter
      raises depends on the matplotlib version), which is why the declared set
      is a bound and the exact restriction is measured.

Imports only the standard library plus `matplotlib` / `numpy`. Exit 0 iff every
obligation holds.
"""
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker as mticker
import numpy as np

# Model conventions (model.py `rendered_labels`): 0 writes a tick's own value
# into the label text -- the convention a numeric legend's formatter has when
# nothing else has been requested; anything else re-expresses ticks in a unit
# or precision of the formatter's own choosing.
VALUE_WRITING = 0

# The concrete formatter kinds each convention is realised by (refinement.md).
# `scalar` is the formatter a numeric legend gets when nothing else has been
# requested; it is the ONE kind whose rendering the residual-rendering controls
# actually move, which is what makes it the convention the reading property is
# stated for.  Every other kind re-expresses ticks its own way.
DEFAULT_KIND = ("scalar",)
OTHER_CONVENTION_KINDS = ("eng", "strmethod_3g", "strmethod_0f", "func_3g",
                          "logsci", "log")
ALL_KINDS = DEFAULT_KIND + OTHER_CONVENTION_KINDS


def _make(kind, view):
    """A real formatter of `kind`, attached to an axis whose numeric range is
    `view` -- the interval it consults when deciding how to write a tick.  The
    range is supplied by the caller, NEVER derived from the tick set: the two
    are independent inputs at both modeled sites, and collapsing them onto the
    diagonal is exactly the measurement error that would make a three-argument
    rendering model look sound."""
    span = (float(view[0]), float(view[1]))

    class _Axis:
        def get_view_interval(self):
            return span

    if kind == "scalar":
        fmt = mticker.ScalarFormatter()
    elif kind == "eng":
        fmt = mticker.EngFormatter("g")
    elif kind == "strmethod_3g":
        fmt = mticker.StrMethodFormatter("{x:.3g}")
    elif kind == "strmethod_0f":
        fmt = mticker.StrMethodFormatter("{x:.0f}")
    elif kind == "func_3g":
        fmt = mticker.FuncFormatter(lambda x, pos: "%.3g" % x)
    elif kind == "logsci":
        fmt = mticker.LogFormatterSciNotation(10)
    elif kind == "log":
        fmt = mticker.LogFormatter()
    else:
        raise AssertionError("unknown formatter kind %r" % kind)
    fmt.axis = _Axis()
    return fmt


def _disable_residual(fmt):
    """Put a formatter into the state the model calls `residual == False`: every
    control by which it could factor a magnitude common to the ticks out of
    them is switched off.  A formatter that has no such control is already in
    that state and is left untouched."""
    for setter in ("set_useOffset", "set_scientific"):
        if hasattr(fmt, setter):
            getattr(fmt, setter)(False)


def rendered_labels(kind, ticks, residual, view, via="format_ticks"):
    """The real formatter's label sequence for the whole tick set -- the deep
    model `rendered_labels(convention, ticks, residual, view_lo, view_hi)`.

    `via` selects the API each modeled legend site renders through:
      - "format_ticks": the whole tick set handed over at once;
      - "set_locs":     the tick set announced, then each tick rendered.
    """
    fmt = _make(kind, view)
    if not residual:
        _disable_residual(fmt)
    tick_list = [float(t) for t in ticks]
    if via == "format_ticks":
        return list(fmt.format_ticks(tick_list))
    fmt.set_locs(tick_list)
    return [fmt(t) for t in tick_list]


def reading(label):
    """The number a reader recovers from a label's text -- the deep model
    `reading(label)`.  Returns None when the text does not read back as a
    number at all (a rescaled unit carries a suffix)."""
    try:
        # a unicode minus is still a minus to a reader
        return float(label.replace("−", "-").strip())
    except ValueError:
        return None


APIS = ("format_ticks", "set_locs")


def diagonal(ticks):
    """The axis range a driver gets by mistaking the tick set for the range.
    Used only where a check needs SOME range; the checks that matter drive the
    range independently."""
    if not len(ticks):
        return (0.0, 1.0)
    return (float(np.min(ticks)), float(np.max(ticks)))


def check_one_label_per_tick(ticks, view):
    """(A-consumed 1) len(rendered_labels(c, ticks, r, lo, hi)) == len(ticks),
    for every convention, every mode, every axis range and both APIs."""
    for kind in ALL_KINDS:
        for residual in (False, True):
            for via in APIS:
                labels = rendered_labels(kind, ticks, residual, view, via=via)
                assert len(labels) == len(ticks), (
                    "[%s/%s/residual=%s/view=%r] label count %d != tick count "
                    "%d" % (kind, via, residual, view, len(labels),
                            len(ticks)))


def check_reading_axiom(ticks, view):
    """(A-consumed 2) the default convention + residual rendering disabled
    ==> every label reads back to its tick's full value, whatever the axis
    range is."""
    for kind in DEFAULT_KIND:
        for via in APIS:
            labels = rendered_labels(kind, ticks, False, view, via=via)
            for tick, label in zip(ticks, labels):
                got = reading(label)
                assert got == float(tick), (
                    "[%s/%s/view=%r] reading axiom unsound: with residual "
                    "rendering disabled, tick %r rendered to %r, which reads "
                    "back as %r (residual %r), not its full value"
                    % (kind, via, view, tick, label, got,
                       None if got is None else float(tick) - got))


def check_nonvacuity(ticks, view):
    """(A-nonvacuity) with residual rendering ENABLED the same default
    formatter renders these ticks to labels that do NOT read back to them."""
    lost = False
    for via in APIS:
        labels = rendered_labels("scalar", ticks, True, view, via=via)
        for tick, label in zip(ticks, labels):
            got = reading(label)
            if got != float(tick):
                lost = True
    return lost


def check_text_not_reading():
    """(A-reference 1) two different label texts for the same tick that read
    back to the same number: the text is strictly more information than the
    reading, so the model's label carrier must stand for the text."""
    ticks = [0.2, 0.22, 0.24, 0.26, 0.28]
    together = rendered_labels("scalar", ticks, False, diagonal(ticks))
    alone = rendered_labels("scalar", [0.2], False, diagonal([0.2]))
    assert together[0] != alone[0], (
        "expected the same tick to render to different TEXTS in different tick "
        "sets, got %r and %r" % (together[0], alone[0]))
    assert reading(together[0]) == reading(alone[0]), (
        "expected those two texts to read back to the same number, got %r "
        "and %r" % (reading(together[0]), reading(alone[0])))


def check_set_dependence():
    """(A-reference 2) at a FIXED axis range, the same tick renders to different
    labels depending on the whole tick set it is rendered with -- which is why
    `rendered_labels` takes the set and returns the sequence."""
    # non-integral, residual rendering disabled, one range for both calls
    view = (0.0, 1.0)
    together = rendered_labels("scalar", [0.2, 0.22, 0.24, 0.26, 0.28], False,
                               view)
    alone = rendered_labels("scalar", [0.2], False, view)
    assert together[0] != alone[0], (
        "expected set-dependent label text at a fixed axis range, got %r vs %r"
        % (together[0], alone[0]))
    # integral, residual rendering enabled, one range for both calls
    view = (0.0, 10.0 ** 9)
    small_set = rendered_labels("scalar", [100000000, 100000001], True, view)
    wide_set = rendered_labels("scalar", [0, 100000000, 100000001], True, view)
    assert small_set[0] != wide_set[1], (
        "expected tick 100000000 to render differently in {1e8, 1e8+1} than in "
        "{0, 1e8, 1e8+1} at a fixed axis range, got %r vs %r"
        % (small_set[0], wide_set[1]))


# Tick set / axis range pairs used to look for range dependence.  Every pair
# holds the tick set FIXED and moves only the range, and every range contains
# the tick set (which is the reachable region at both modeled sites, since both
# clip their ticks to the range).
RANGE_PROBES = [
    ([2, 3, 4], (2.0, 4.0), (1.0, 1000.0)),
    ([100, 200, 300], (100.0, 300.0), (0.0, 10.0 ** 6)),
    ([7], (7.0, 7.0), (0.0, 10.0 ** 9)),
    ([100000000, 100000001], (1e8, 1e8 + 1.0), (0.0, 10.0 ** 9)),
    ([1, 10, 100], (1.0, 100.0), (1.0, 10.0 ** 9)),
]


def check_range_dependence():
    """(A-reference 3) a label sequence is NOT a function of (convention, tick
    set, mode) alone: holding all three fixed and moving only the axis range
    changes what several conventions render.  Returns the measured set of
    range-dependent conventions; a refinement that rendered against the tick
    set's own span instead of the formatter's own range would differ from the
    real callee on exactly these."""
    dependent = set()
    for kind in ALL_KINDS:
        for ticks, view_a, view_b in RANGE_PROBES:
            for residual in (False, True):
                for via in APIS:
                    try:
                        a = rendered_labels(kind, ticks, residual, view_a,
                                            via=via)
                    except Exception as exc:
                        a = "raise:%s" % type(exc).__name__
                    try:
                        b = rendered_labels(kind, ticks, residual, view_b,
                                            via=via)
                    except Exception as exc:
                        b = "raise:%s" % type(exc).__name__
                    if a != b:
                        dependent.add(kind)
    assert dependent, (
        "no convention's rendering moved when only the axis range moved -- the "
        "deep model's range arguments would then be idle, and the probes above "
        "would not be exercising the input the real formatters read")
    return sorted(dependent)


def check_convention_guard(ticks, view):
    """(A-guard) the convention guard on the reading property withholds nothing
    that is available.

    Returns a pair:
      * whether some non-default convention's labels fail to read back to their
        ticks even with every residual-rendering control disabled -- i.e. the
        reading property is UNAVAILABLE there, not merely unclaimed;
      * how many non-default (convention, API) renderings the residual controls
        MOVE at this (tick set, range).  That count is reported, not asserted:
        which non-default formatters honour those controls is a property of the
        matplotlib version, and the model claims nothing about it.
    """
    unreadable = False
    moved = 0
    for kind in OTHER_CONVENTION_KINDS:
        for via in APIS:
            try:
                off = rendered_labels(kind, ticks, False, view, via=via)
            except Exception as exc:
                off = "raise:%s" % type(exc).__name__
            try:
                on = rendered_labels(kind, ticks, True, view, via=via)
            except Exception as exc:
                on = "raise:%s" % type(exc).__name__
            if off != on:
                moved += 1
            if isinstance(off, list) and any(
                    reading(lbl) != float(t) for t, lbl in zip(ticks, off)):
                unreadable = True
    return unreadable, moved


def check_default_convention_is_the_moved_one(ticks, view):
    """(A-guard, converse) the default convention IS moved by the controls: on
    a large tick set its labels differ with residual rendering disabled vs
    enabled.  Together with the check above this pins convention 0 to exactly
    the formatter the modeled guarantee is about."""
    for via in APIS:
        off = rendered_labels("scalar", ticks, False, view, via=via)
        on = rendered_labels("scalar", ticks, True, view, via=via)
        assert off != on, (
            "[scalar/%s/view=%r] expected the default convention's rendering to "
            "change when residual rendering is disabled, got %r both ways"
            % (via, view, off))


# The only conventions whose rendering is chosen from the WIDTH of the axis
# range, and so COULD be undefined when that range has no width.  This is the
# declared UPPER BOUND on the callee's domain restriction, and
# `check_callee_domain` below pins the actual restriction exactly: whatever
# kinds raise must lie inside this set, every kind that does not raise must
# render one label per tick even on a range of no width, on a range of non-zero
# width nothing may raise at all, and an empty tick set must render even on a
# range of no width.  The measured set is reported, and it may be EMPTY --
# whether the width-reading unit formatter raises or renders is a property of
# the matplotlib version in use, so a bound plus an exact measurement is the
# honest form of the claim.  A kind that raised outside the bound, or a
# non-raising kind that rendered the wrong number of labels, fails.
WIDTH_DEPENDENT_KINDS = ("eng",)


def check_callee_domain():
    """(A-domain) exactly which (convention, tick set, range) triples the real
    callee has no label sequence for -- the domain restriction model.py's
    `rendered_labels` docstring discloses.  Returns the measured set of
    restricted conventions, which is what gets reported; an empty set means this
    environment's callee is total on every input the model can reach."""
    tick_sets = [[7], [100000000], [0], [10 ** 8, 10 ** 8], [5, 5, 5],
                 [0, 1], [-3, -1, 1, 3]]
    zero_width = [(7.0, 7.0), (0.0, 0.0), (1e8, 1e8), (-3.0, -3.0)]
    positive_width = [(0.0, 1.0), (0.0, 10.0 ** 9), (-10.0 ** 9, 10.0 ** 9),
                      (1.0, 1000.0)]
    raised = set()
    for ticks in tick_sets:
        for view in zero_width:
            for kind in ALL_KINDS:
                for residual in (False, True):
                    for via in APIS:
                        try:
                            labels = rendered_labels(kind, ticks, residual,
                                                     view, via=via)
                        except Exception:
                            raised.add(kind)
                            continue
                        assert len(labels) == len(ticks), (
                            "[%s/%s/residual=%s/view=%r] %d labels for %d "
                            "ticks on a range of no width"
                            % (kind, via, residual, view, len(labels),
                               len(ticks)))
    assert raised <= set(WIDTH_DEPENDENT_KINDS), (
        "a convention with no rendering for an axis range of no width that is "
        "NOT one whose unit is chosen from that width: measured %r, declared "
        "bound %r" % (sorted(raised), sorted(WIDTH_DEPENDENT_KINDS)))
    # an empty tick set has no label to render, so nothing is undefined for it
    for view in zero_width:
        for kind in ALL_KINDS:
            for residual in (False, True):
                for via in APIS:
                    labels = rendered_labels(kind, [], residual, view, via=via)
                    assert len(labels) == 0, (
                        "[%s/%s/residual=%s/view=%r] %d labels for an empty "
                        "tick set" % (kind, via, residual, view, len(labels)))
    for ticks in tick_sets:
        for view in positive_width:
            for kind in ALL_KINDS:
                for residual in (False, True):
                    for via in APIS:
                        labels = rendered_labels(kind, ticks, residual, view,
                                                 via=via)
                        assert len(labels) == len(ticks), (
                            "[%s/%s/residual=%s/view=%r] %d labels for %d "
                            "ticks" % (kind, via, residual, view, len(labels),
                                       len(ticks)))
    return sorted(raised)


def main():
    rng = random.Random(3187)

    boundary = [
        [0, 1, 2, 3],
        [1, 2, 3, 4, 5],
        [-3, -1, 1, 3],
        [100, 200, 300],
        # large sets: the magnitudes where residual rendering bites
        [100000000, 100000001, 100000002, 100000003],
        [100000000, 500000000, 900000000],
        [1000000, 2000000, 3000000],
        [12340000, 12350000, 12360000],
        [999999999, 1000000000, 1000000001],
        [10000000, 20000000, 30000000],
    ]

    def views_for(ticks):
        """Axis ranges to drive this tick set against: the diagonal a careless
        driver would use, plus ranges that are wider, offset, or do not contain
        the ticks at all.  The range is an INPUT, not a function of the ticks."""
        lo, hi = float(min(ticks)), float(max(ticks))
        width = max(hi - lo, 1.0)
        return [(lo, hi),                       # the diagonal
                (lo - width, hi + width),       # twice as wide
                (lo - 1000.0 * width, hi + 1000.0 * width),
                (0.0, hi + width),              # anchored at zero
                (lo, hi + 1000.0 * width),      # widened upward only
                (0.0, 1.0),                     # unrelated, may exclude ticks
                (-(10.0 ** 9), 10.0 ** 9),
                (lo, lo)]                       # no width

    residual_loses_magnitude = False
    other_convention_unreadable = False
    guard_moves = 0
    renders = 0
    for ticks in boundary:
        for view in views_for(ticks):
            if view[0] == view[1]:
                # the one disclosed restriction lives here; check_callee_domain
                # pins it exactly, so the totality checks skip it
                continue
            check_one_label_per_tick(ticks, view)
            check_reading_axiom(ticks, view)
            unreadable, moved = check_convention_guard(ticks, view)
            other_convention_unreadable = other_convention_unreadable or \
                unreadable
            guard_moves += moved
            renders += 1
            # The converse-guard check is asserted on the ranges the modeled
            # sites can actually present -- ones that CONTAIN the tick set,
            # since both sites clip their ticks to the range. On a range that
            # excludes the ticks the default formatter has no common magnitude
            # to factor out and the controls are measurably inert, which is a
            # fact about the callee, not about the modeled behaviour.
            contains = view[0] <= min(ticks) and max(ticks) <= view[1]
            if min(ticks) >= 10000000 and contains:
                check_default_convention_is_the_moved_one(ticks, view)
                if check_nonvacuity(ticks, view):
                    residual_loses_magnitude = True

    assert residual_loses_magnitude, (
        "expected at least one large tick set whose labels stop reading back "
        "to their ticks once residual rendering is enabled -- otherwise the "
        "model's `not residual` hypothesis would be idle")
    assert other_convention_unreadable, (
        "expected a non-default convention whose labels do not read back to "
        "their ticks even with every residual-rendering control disabled -- "
        "otherwise the model's convention guard would be withholding a "
        "guarantee that is in fact available")

    check_text_not_reading()
    check_set_dependence()
    range_dependent = check_range_dependence()
    width_dependent = check_callee_domain()

    fuzz = 0
    for _ in range(4000):
        base = rng.choice([1, 10, 100, 1000, 10 ** 5, 10 ** 6, 10 ** 7,
                           10 ** 8, 10 ** 9])
        step = rng.choice([1, 2, 5, 10, 100, 1000])
        n = rng.randint(1, 8)
        start = rng.randint(0, base)
        ticks = [start + i * step for i in range(n)]
        # the axis range is drawn INDEPENDENTLY of the tick set: sometimes
        # containing it, sometimes not, sometimes far wider
        lo = rng.choice([0.0, -float(base), float(start),
                         float(start) - rng.randint(0, base),
                         float(min(ticks))])
        hi = rng.choice([float(base) * 10.0, float(max(ticks)),
                         float(start) + rng.randint(1, base * 10),
                         lo + 1.0, lo])
        if hi < lo:
            lo, hi = hi, lo
        if hi == lo:
            hi = lo + 1.0
        check_one_label_per_tick(ticks, (lo, hi))
        check_reading_axiom(ticks, (lo, hi))
        fuzz += 1

    print("G-AX OK: rendered_labels/reading deep models sound on %d boundary "
          "(tick set, axis range) pairs + %d fuzz pairs, both formatter APIs, "
          "with the axis range driven INDEPENDENTLY of the tick set -- one "
          "label per tick for every convention, mode and range; value-writing "
          "+ residual-disabled labels read back to full ticks at every range, "
          "including ranges that do not contain the ticks; residual-enabled "
          "labels demonstrably do not (hypothesis load-bearing); label text "
          "carries strictly more than its reading and depends on the whole "
          "tick set (carrier and signature justified); the label sequence "
          "moves when only the axis range moves for convention(s) %r, so the "
          "range arguments are load-bearing and rendering against the tick "
          "set's own span would differ; some non-default conventions are "
          "unreadable even with every residual-rendering control disabled "
          "(guard withholds nothing available) while the residual controls "
          "moved a non-default rendering in %d of the boundary pairs "
          "(measured, not claimed), and the default convention is exactly the "
          "one those controls move. Measured callee domain (declared bound "
          "%r): the convention(s) with no label sequence at all for an axis "
          "range of no width are %r; every other convention renders one label "
          "per tick on every range, of no width or not, an empty tick set "
          "renders everywhere, and on a range of non-zero width every "
          "convention renders."
          % (renders, fuzz, range_dependent, guard_moves,
             sorted(WIDTH_DEPENDENT_KINDS), width_dependent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
