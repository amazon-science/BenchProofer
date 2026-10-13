#!/usr/bin/env python3
"""G-AX executable soundness probe for mwaskom__seaborn-3187 (lean bundle).

Runs INSIDE the instance image at the BASE commit and drives the REAL callee the
Solution.lean `axioms` region abstracts — a matplotlib numeric tick formatter
together with the axis view interval it reads — asserting that every observation
satisfies each consumed axiom. Imports only stdlib + matplotlib/numpy (present in
the image). Exits 0 iff every obligation holds; a single JSON line is the last
thing printed either way.

===========================================================================
THE AXIOMS UNDER TEST (Solution.lean, `axioms` region)
===========================================================================

    axiom render : TickRenderer -> List Int -> List String
    axiom labelValue : String -> Int

    axiom render_length : forall r ticks,
        (render r ticks).length = ticks.length

    structure TickRenderer where
      compactionCapable : Bool
      compacting : Bool
      numeralStyle : Bool
      convention : Nat

    axiom render_uncompacted_faithful : forall r ticks,
        r.compactionCapable = true -> r.compacting = false ->
        r.numeralStyle = true ->
        (forall t in ticks, t.natAbs <= 9007199254740992) ->
        forall i, i < ticks.length ->
          labelValue ((render r ticks)[i]!) = ticks[i]!

===========================================================================
THE PYTHON BINDING (measured; see mapping.md)
===========================================================================

A `TickRenderer` is a matplotlib tick formatter plus the axis view interval it
reads, i.e. exactly the state a legend builder meets at both call sites
(`ContinuousBase._setup` in seaborn/_core/scales.py, and
`locator_to_legend_entries` in seaborn/utils.py).

  * `compactionCapable` == `hasattr(formatter, "set_useOffset")`. MEASURED to
    agree with `hasattr(formatter, "set_scientific")` for every formatter class
    reachable at these sites: `ScalarFormatter` exposes both, `LogFormatter` and
    `LogFormatterSciNotation` expose neither. The capability is therefore an
    intrinsic property of the formatter class, not something a builder sets --
    which is exactly what the structure field claims.

  * `compacting` == whether the two compaction behaviours are enabled. A capable
    renderer is built with `set_useOffset(v); set_scientific(v)`. Not settable on
    a non-capable formatter, which never hoists a common magnitude out of its
    labels; such a renderer is recorded with `compacting = False` and used as it
    stands.

  * `numeralStyle` == whether the renderer spells a label as a BARE NUMERAL, i.e.
    `not (formatter._useMathText or formatter._useLocale or formatter._usetex)`
    for a capable formatter, and False for a non-capable one (which writes by its
    own convention -- `LogFormatterSciNotation` writes `$\mathdefault{10^{2}}$`).
    MEASURED, each of those three settings makes the renderer write text that
    denotes its quantity by a typesetting or regional convention rather than by
    being read as a number: with all compaction OFF, ticks
    [0, 200000, ..., 1000000] render as ['$\mathdefault{0}$', ...] under
    useMathText and as ['0', '200,000', ...] under useLocale, and neither parses
    back. Each is settled from a constructor argument or an rcParam BEFORE the
    renderer reaches either call site -- reachable through the public API as
    `Continuous().label(formatter=ScalarFormatter(useMathText=True))` and as
    `mpl.rcParams['axes.formatter.use_mathtext'] = True` (which the utils.py
    site's bare `ScalarFormatter()` picks up on construction) -- and NO legend
    builder can undo any of them, since neither `set_useOffset` nor
    `set_scientific` touches them. That is why the faithfulness axiom is guarded
    by it rather than claiming a plain reading of every capable renderer: the
    claim would be false of the real renderer at a state it really reaches.
    Obligation 7 MEASURES both directions of this guard.

  * `convention` == the remainder of what governs the text: the formatter CLASS
    plus the axis view interval. Encoded here as an index into `CONVENTIONS`.
    This component is real rather than decorative: MEASURED, the label text
    genuinely varies with the view interval alone (see `iv_sensitive_witnesses`
    in the report -- e.g. a `LogFormatter` over ticks [0, 1, 2] writes
    ['0', '1', ''] under view interval (0.0, 1.0) and ['0', '1', '2'] under
    (9e15, 9.1e15)), so an abstraction leaving it out would claim more
    determinacy than the real renderer has.

  * `render r ticks` == attach a dummy axis returning that view interval, then
    `formatter.set_locs([float(t) for t in ticks])` followed by
    `[formatter(float(t)) for t in ticks]`. MEASURED equivalent to
    `formatter.format_ticks(locs)` -- the call the scales.py site uses -- with 0
    mismatches over 16000 draws; the equivalence is re-measured here
    (`format_ticks_agreements`).

  * `labelValue s` == read the label text back on its own: strip it, map
    matplotlib's Unicode minus U+2212 to ASCII '-', then `float(...)`. A label
    that does not parse is reported as a FAILURE of the faithfulness axiom
    wherever that axiom's guard applies, never silently skipped.

===========================================================================
WHAT IS CHECKED (each numbered obligation is counted in the JSON report)
===========================================================================

  1. `check_length` -- one label per tick, for CAPABLE and NON-CAPABLE
     formatters, in every mode, over every tick set including the empty list.

  2. `check_faithful` -- for a CAPABLE renderer with compaction OFF that spells
     its labels as BARE NUMERALS, and every tick within the guard (|t| <= 2^53),
     each label reads back to its tick EXACTLY. Only capable, bare-numeral
     renderers are checked: the axiom deliberately claims
     nothing about the label values of a renderer offering no compaction
     control, so no such assertion is made for `LogFormatter` /
     `LogFormatterSciNotation` -- what they write is recorded instead
     (`noncapable_samples`).

  3. NON-VACUITY (`witness_default_breaks`) -- the guarded axiom is not trivially
     true: with a CAPABLE renderer in the COMPACTING mode there exist tick sets,
     well inside the guard, whose labels do NOT read back to their ticks. E.g.
     ticks [1e8 .. 1e8+4] under view interval (1e8-1, 1e8+5) render as
     '0'..'4' while compacting. If no such observation were found the axiom
     would be vacuous and the specification would pin nothing, so that is a
     probe FAILURE.

  4. GUARD TIGHTNESS just above 2^53 -- the `|t| <= 2^53` restriction is a real
     property of the renderer, not a convenience. At ticks 2^53+1, 2^53+3,
     2*2^53+1, 2^60+1 (and their negations) the round trip genuinely does NOT
     hold, because the renderer receives tick positions through an IEEE-754
     double channel that stops distinguishing consecutive integers past 2^53:
     MEASURED, 2^53+1 renders as '9007199254740992'. Every such observation is
     recorded. Should the round trip hold there, the guard would be needlessly
     narrow -- that is reported and treated as a probe FAILURE, so the axiom
     cannot quietly over-restrict its domain.

  5. Boundary tick sets: 0, +-1, +-2, +-10, the powers of ten up to 1e15, the
     1e8-shaped run from the issue, 2^53-2, 2^53-1, 2^53, and the empty list.
     Plus a seeded fuzz (seed 3187, meta.json `verifier_pins.conf_seed`) of at
     least 40000 draws across formatter kinds, modes and view intervals, of
     which several thousand hug the 2^53 guard from below.

  7. numeralStyle GUARD TIGHTNESS (`check_dressed_breaks`) -- the numeralStyle
     restriction is a real property of the renderer, not a convenience. At a
     renderer that offers the compaction control, has that mode fully OFF (the
     gold fix's own two calls are applied and asserted effective, offset == 0 and
     orderOfMagnitude == 0), and has every tick well inside the 2^53 guard, the
     round trip genuinely does NOT hold once the renderer dresses its labels up --
     under any one of useMathText, useLocale or usetex. Every such observation is
     recorded. If no such observation were found the guard would have no measured
     justification, and if the round trip HELD for a dressed renderer the guard
     would be needlessly narrow; either is a probe FAILURE, so the axiom can
     neither claim more than the renderer delivers nor quietly over-restrict.

  6. Every formatter kind reachable at the two real call sites is covered:
     `ScalarFormatter` (capable, both modes) plus `LogFormatter` and
     `LogFormatterSciNotation` (both non-capable, length only).
"""
import json
import random
import sys
import warnings

import numpy as np  # noqa: F401  (imported for errstate around log formatters)

import matplotlib

matplotlib.use("Agg")

import matplotlib.ticker as mticker  # noqa: E402

INSTANCE = "mwaskom__seaborn-3187"
SEED = 3187                     # meta.json verifier_pins.conf_seed
FLOAT_EXACT = 2 ** 53           # 9007199254740992 -- the axiom's domain guard

# fuzz budget: FUZZ_TICKSETS tick sets x len(RENDERERS_PER_SET) renderer states
FUZZ_TICKSETS = 12_000
FUZZ_BOUNDARY_TICKSETS = 3_000
MIN_FUZZ_DRAWS = 40_000
MIN_COMPACTING_BREAKS = 8       # obligation 3: a healthy number, not just one

UNICODE_MINUS = "−"


# --------------------------------------------------------------------------
# The renderer: a matplotlib tick formatter plus its axis view interval.
# --------------------------------------------------------------------------

class _DummyAxis:
    """The whole of the axis a tick formatter reads: a view interval. This is
    the same minimal stand-in seaborn supplies at both call sites (its own
    `dummy_axis()` in utils.py, and the `PseudoAxis` set up with
    `set_view_interval` in _core/scales.py)."""

    def __init__(self, view_interval):
        self._iv = (float(view_interval[0]), float(view_interval[1]))

    def get_view_interval(self):
        return self._iv


# `convention` == the formatter CLASS plus the view interval: everything other
# than the compacting mode that governs the text. Enumerated as Nat indices.
FORMATTER_KINDS = (
    ("ScalarFormatter", mticker.ScalarFormatter),
    ("LogFormatter", mticker.LogFormatter),
    ("LogFormatterSciNotation", mticker.LogFormatterSciNotation),
)

VIEW_INTERVALS = (
    (0.0, 1.0),
    (-1.0, 1.0),
    (0.0, 1e15),
    (-1e15, 1e15),
    (9e15, 9.1e15),
    (0.0, 1e-9),
    (3.0, 2.0),           # reversed
    (0.5, 0.5),           # degenerate
    (1e8 - 1.0, 1e8 + 5.0),   # the issue-shaped range around the 1e8 tick run
)

# The view interval a legend describing the issue's quantity actually presents,
# used for the named non-vacuity witness below.
F2P_VIEW_INTERVAL = (1e8 - 1.0, 1e8 + 5.0)
F2P_TICKS = [10 ** 8 + i for i in range(5)]

CONVENTIONS = [(kind_name, kind_cls, iv)
               for (kind_name, kind_cls) in FORMATTER_KINDS
               for iv in VIEW_INTERVALS]
CONVENTION_INDEX = {(k, iv): i
                    for i, (k, _c, iv) in enumerate(CONVENTIONS)}

# convention indices whose formatter class exposes the compaction controls
CAPABLE_CONVENTIONS = [i for i, (k, _c, _iv) in enumerate(CONVENTIONS)
                       if k == "ScalarFormatter"]
NONCAPABLE_CONVENTIONS = [i for i, (k, _c, _iv) in enumerate(CONVENTIONS)
                          if k != "ScalarFormatter"]


class TickRenderer:
    """A `TickRenderer` value: (compactionCapable, compacting, numeralStyle,
    convention).

    `numeralStyle` is the binding for whether the renderer spells a label as a
    BARE NUMERAL. MEASURED: a `ScalarFormatter` writes plain decimal numerals only
    when none of its three text-dressing settings is on -- `_useMathText` (the
    label is typeset, `$\\mathdefault{200000}$`), `_useLocale` (the label is
    punctuated by the regional convention, `200,000`) and `_usetex`. Each is
    settled from a constructor argument or an rcParam BEFORE the renderer reaches
    either call site, and no legend builder can undo any of them: neither
    `set_useOffset` nor `set_scientific` touches them. A renderer offering no
    compaction control at all writes by its own convention, which is likewise not
    a bare numeral in general (`LogFormatterSciNotation` writes
    `$\\mathdefault{10^{2}}$`), so it is recorded with numeralStyle False.
    """

    def __init__(self, convention, compacting=False):
        kind_name, kind_cls, iv = CONVENTIONS[convention]
        self.convention = convention
        self.kind = kind_name
        self._cls = kind_cls
        self._iv = iv
        probe = kind_cls()
        # MEASURED: the two capability probes always agree per formatter class.
        cap_offset = hasattr(probe, "set_useOffset")
        cap_scale = hasattr(probe, "set_scientific")
        if cap_offset != cap_scale:
            raise AssertionError(
                "binding assumption unmet: %s exposes set_useOffset=%s but "
                "set_scientific=%s -- compactionCapable is not a single "
                "intrinsic property of this formatter class"
                % (kind_name, cap_offset, cap_scale))
        self.compactionCapable = cap_offset
        # A renderer offering no control never hoists anything out; it is used
        # as it stands, so its mode is recorded as not compacting.
        self.compacting = bool(compacting) if self.compactionCapable else False
        if compacting and not self.compactionCapable:
            raise AssertionError(
                "binding misuse: the compacting mode is not settable on %s"
                % kind_name)
        # numeralStyle: measured off the constructed formatter, never assumed.
        if self.compactionCapable:
            self.numeralStyle = not (getattr(probe, "_useMathText", False)
                                     or getattr(probe, "_useLocale", False)
                                     or getattr(probe, "_usetex", False))
        else:
            self.numeralStyle = False

    def _build(self):
        f = self._cls()
        f.axis = _DummyAxis(self._iv)
        if self.compactionCapable:
            f.set_useOffset(self.compacting)
            f.set_scientific(self.compacting)
        return f

    # --- axiom `render` -------------------------------------------------
    def render(self, ticks):
        f = self._build()
        locs = [float(t) for t in ticks]
        f.set_locs(locs)
        return [f(x) for x in locs]

    # the call the scales.py site actually makes; MEASURED equivalent
    def render_via_format_ticks(self, ticks):
        f = self._build()
        return list(f.format_ticks([float(t) for t in ticks]))

    def describe(self):
        return {"kind": self.kind, "view_interval": list(self._iv),
                "compactionCapable": self.compactionCapable,
                "compacting": self.compacting,
                "numeralStyle": self.numeralStyle,
                "convention": self.convention}


def label_value(label):
    """axiom `labelValue`: the quantity a reader recovers from one label read
    back on its own. Raises ValueError when the text denotes no quantity."""
    return float(label.strip().replace(UNICODE_MINUS, "-"))


def _silence():
    """Log formatters evaluate log10 on nonpositive ticks; the resulting numpy
    warnings are noise, not observations."""
    return warnings.catch_warnings()


# --------------------------------------------------------------------------
# Obligation 1 -- render_length
# --------------------------------------------------------------------------

def check_length(state, renderers, ticks):
    """`render_length`: exactly one label per tick, in every mode, for capable
    and non-capable renderers alike."""
    for r in renderers:
        labels = r.render(ticks)
        state["n_length"] += 1
        if len(labels) != len(ticks):
            state["disagreements"].append({
                "axiom": "render_length",
                "renderer": r.describe(),
                "ticks": [str(t) for t in ticks[:8]],
                "n_ticks": len(ticks),
                "n_labels": len(labels),
            })


# --------------------------------------------------------------------------
# Obligation 2 -- render_uncompacted_faithful (capable, compaction off)
# --------------------------------------------------------------------------

def check_faithful(state, renderers, ticks):
    """`render_uncompacted_faithful`: capable renderer, compaction off, every
    tick inside the guard => every label reads back to its tick exactly."""
    for t in ticks:
        if abs(t) > FLOAT_EXACT:
            raise AssertionError(
                "probe error: check_faithful called outside the axiom's "
                "guarded domain (tick %s)" % t)
    for r in renderers:
        if not (r.compactionCapable and not r.compacting and r.numeralStyle):
            raise AssertionError(
                "probe error: check_faithful called on a renderer outside the "
                "axiom's hypotheses: %r" % (r.describe(),))
        labels = r.render(ticks)
        state["n_faithful"] += 1
        if len(labels) != len(ticks):
            state["disagreements"].append({
                "axiom": "render_uncompacted_faithful/length",
                "renderer": r.describe(), "n_ticks": len(ticks),
                "n_labels": len(labels)})
            continue
        for i, (t, lab) in enumerate(zip(ticks, labels)):
            state["n_faithful_labels"] += 1
            try:
                got = label_value(lab)
            except ValueError:
                state["disagreements"].append({
                    "axiom": "render_uncompacted_faithful",
                    "reason": "label denotes no quantity",
                    "renderer": r.describe(), "index": i,
                    "tick": str(t), "label": lab,
                    "ticks": [str(x) for x in ticks[:8]]})
                continue
            if got != t:
                state["disagreements"].append({
                    "axiom": "render_uncompacted_faithful",
                    "reason": "label reads back to another quantity",
                    "renderer": r.describe(), "index": i,
                    "tick": str(t), "label": lab, "read_back": repr(got),
                    "ticks": [str(x) for x in ticks[:8]]})


# --------------------------------------------------------------------------
# Obligation 3 -- non-vacuity: the compacting mode genuinely loses the value
# --------------------------------------------------------------------------

def witness_default_breaks(state, renderer, ticks):
    """Count observations where a CAPABLE renderer standing in the COMPACTING
    mode writes a label that does not read back to its tick. Nothing is
    asserted about these labels -- the axiom claims nothing there; they are what
    shows the guarded claim is not trivially true."""
    if not (renderer.compactionCapable and renderer.compacting):
        raise AssertionError("probe error: non-vacuity witness needs a capable "
                             "renderer in the compacting mode")
    labels = renderer.render(ticks)
    state["n_compacting_probes"] += 1
    broke = False
    for t, lab in zip(ticks, labels):
        try:
            if label_value(lab) != t:
                broke = True
        except ValueError:
            broke = True
        if broke:
            break
    if broke:
        state["n_compacting_breaks"] += 1
        if len(state["compacting_break_witnesses"]) < 5:
            state["compacting_break_witnesses"].append({
                "renderer": renderer.describe(),
                "ticks": [str(t) for t in ticks[:8]],
                "labels": labels[:8]})
    return broke


# --------------------------------------------------------------------------
# Obligation 4 -- guard tightness just above 2^53
# --------------------------------------------------------------------------

ABOVE_GUARD_TICKS = (
    FLOAT_EXACT + 1,
    FLOAT_EXACT + 3,
    2 * FLOAT_EXACT + 1,
    2 ** 60 + 1,
    -(FLOAT_EXACT + 1),
    -(FLOAT_EXACT + 3),
    -(2 * FLOAT_EXACT + 1),
    -(2 ** 60 + 1),
)


def check_guard_tightness(state):
    """Above the guard the round trip genuinely does not hold: a tick reaches
    the renderer through a double-precision channel that no longer distinguishes
    it from a neighbour, so it is snapped before any text is written. Each
    observation where the round trip DOES hold above the guard would mean the
    axiom's domain restriction is needlessly narrow, and is recorded as such."""
    for conv in CAPABLE_CONVENTIONS:
        r = TickRenderer(conv, compacting=False)
        for t in ABOVE_GUARD_TICKS:
            for ticks in ([t], [t, t + 2]):
                labels = r.render(ticks)
                state["n_above_guard_probes"] += 1
                held = True
                for tk, lab in zip(ticks, labels):
                    try:
                        if label_value(lab) != tk:
                            held = False
                    except ValueError:
                        held = False
                    if not held:
                        break
                if held:
                    state["n_above_guard_roundtrip_held"] += 1
                    if len(state["guard_narrow_witnesses"]) < 5:
                        state["guard_narrow_witnesses"].append({
                            "renderer": r.describe(),
                            "ticks": [str(x) for x in ticks],
                            "labels": labels})
                else:
                    state["n_above_guard_breaks"] += 1
                    if len(state["guard_tight_witnesses"]) < 5:
                        state["guard_tight_witnesses"].append({
                            "renderer": r.describe(),
                            "ticks": [str(x) for x in ticks],
                            "labels": labels})


# --------------------------------------------------------------------------
# numeralStyle NON-VACUITY / TIGHTNESS -- the guard is load-bearing
# --------------------------------------------------------------------------

# The three text-dressing settings of a real ScalarFormatter, each reachable at
# both call sites before a legend builder ever sees the renderer: as a constructor
# argument (`Continuous().label(formatter=ScalarFormatter(useMathText=True))` at
# the scales.py site) or as an rcParam (`axes.formatter.use_mathtext`,
# `axes.formatter.use_locale`, `text.usetex`), which the utils.py site's bare
# `ScalarFormatter()` picks up on construction. None is touched by
# `set_useOffset` / `set_scientific`, so a legend builder that disables compaction
# leaves every one of them exactly as it found it.
DRESSED_MODES = (
    ("useMathText", "_useMathText"),
    ("useLocale", "_useLocale"),
    ("usetex", "_usetex"),
)

# `useLocale` routes the label through `locale.format_string(..., grouping=True)`,
# so what it writes depends on the process's numeric locale. Under the "C" locale
# there is no grouping separator and the text coincides with the bare numeral --
# so probing that mode under "C" would measure nothing. The reachable condition is
# a locale that DOES group, which is what a real deployment of the reporting code
# in the issue runs under, so the probe selects one for that arm and reports which
# it got. If no grouping locale is available in the image the arm is recorded as
# unmeasured rather than counted as agreement.
GROUPING_LOCALES = ("en_US.UTF-8", "en_US.utf8", "C.UTF-8", "")


def _select_grouping_locale():
    """Return (locale_name, thousands_sep) for the first available locale whose
    numeric convention groups thousands, or (None, None) if none does."""
    import locale as _loc
    saved = _loc.setlocale(_loc.LC_NUMERIC)
    for name in GROUPING_LOCALES:
        try:
            _loc.setlocale(_loc.LC_NUMERIC, name)
        except _loc.Error:
            continue
        sep = _loc.localeconv().get("thousands_sep") or ""
        grouping = _loc.localeconv().get("grouping") or []
        if sep and any(g > 0 for g in grouping):
            return (name or "<user default>", sep)
    _loc.setlocale(_loc.LC_NUMERIC, saved)
    return (None, None)


def check_dressed_breaks(state):
    """`numeralStyle` is a real restriction on `render_uncompacted_faithful`, not a
    convenience: at a renderer that offers the compaction control, HAS that mode
    off, and has every tick well inside the 2^53 guard, the round trip genuinely
    FAILS as soon as the renderer dresses its labels up. Each such observation is
    recorded. Were the round trip to hold for every dressed renderer, the
    numeralStyle guard would be needlessly narrow -- that is a probe FAILURE, so
    the axiom cannot quietly over-restrict its domain."""
    ticksets = [[0, 200000, 400000, 600000, 800000, 1000000],
                F2P_TICKS, [1, 10, 100, 1000], [-5, 0, 5], [7]]
    import locale as _loc
    for mode_name, attr in DRESSED_MODES:
        if mode_name == "useLocale":
            loc_name, loc_sep = _select_grouping_locale()
            state["dressed_locale"] = loc_name
            state["dressed_locale_sep"] = loc_sep
            if loc_name is None:
                # No grouping locale in this image: the arm cannot be measured,
                # and is NOT counted as the round trip holding.
                state["dressed_modes_unmeasured"].append(mode_name)
                continue
            _loc.setlocale(_loc.LC_NUMERIC, "" if loc_name == "<user default>"
                           else loc_name)
        else:
            _loc.setlocale(_loc.LC_NUMERIC, "C")
        for conv in CAPABLE_CONVENTIONS:
            _k, kind_cls, iv = CONVENTIONS[conv]
            for ticks in ticksets:
                f = kind_cls()
                setattr(f, attr, True)
                f.axis = _DummyAxis(iv)
                # the gold fix's own two calls: compaction genuinely off
                f.set_useOffset(False)
                f.set_scientific(False)
                if getattr(f, "_useMathText", False) or getattr(f, "_usetex", False):
                    pass
                locs = [float(x) for x in ticks]
                f.set_locs(locs)
                labels = [f(x) for x in locs]
                state["n_dressed_probes"] += 1
                state["dressed_by_mode"].setdefault(
                    mode_name, {"probes": 0, "breaks": 0, "held": 0})
                state["dressed_by_mode"][mode_name]["probes"] += 1
                # domain membership: capable, not compacting, inside the guard
                if f.offset != 0 or f.orderOfMagnitude != 0:
                    raise AssertionError(
                        "probe error: the gold calls left residual compaction "
                        "(offset=%r oom=%r)" % (f.offset, f.orderOfMagnitude))
                held = True
                for tk, lab in zip(ticks, labels):
                    try:
                        if label_value(lab) != tk:
                            held = False
                    except ValueError:
                        held = False
                    if not held:
                        break
                if held:
                    state["n_dressed_roundtrip_held"] += 1
                    state["dressed_by_mode"][mode_name]["held"] += 1
                    if len(state["dressed_narrow_witnesses"]) < 5:
                        state["dressed_narrow_witnesses"].append({
                            "mode": mode_name, "view_interval": list(iv),
                            "ticks": [str(x) for x in ticks[:6]],
                            "labels": labels[:6]})
                else:
                    state["n_dressed_breaks"] += 1
                    state["dressed_by_mode"][mode_name]["breaks"] += 1
                    if len(state["dressed_break_witnesses"]) < 6:
                        state["dressed_break_witnesses"].append({
                            "mode": mode_name, "view_interval": list(iv),
                            "ticks": [str(x) for x in ticks[:6]],
                            "labels": labels[:6]})
    _loc.setlocale(_loc.LC_NUMERIC, "C")


# --------------------------------------------------------------------------
# Renderer-state cohorts
# --------------------------------------------------------------------------

def all_renderers():
    """Every renderer state the two call sites can meet: the capable formatter
    in both modes, and each non-capable formatter as it stands, over every
    convention."""
    out = []
    for conv in CAPABLE_CONVENTIONS:
        out.append(TickRenderer(conv, compacting=False))
        out.append(TickRenderer(conv, compacting=True))
    for conv in NONCAPABLE_CONVENTIONS:
        out.append(TickRenderer(conv, compacting=False))
    return out


def capable_uncompacted(renderers):
    """The cohort clause (R) and `render_uncompacted_faithful` speak about: the
    control is offered, the compacting mode is off, AND the renderer spells its
    labels as bare numerals. A renderer that dresses its labels up is excluded
    because the round trip genuinely does not hold of it (see
    `check_dressed_breaks`, which MEASURES that and would fail if it did hold)."""
    return [r for r in renderers
            if r.compactionCapable and not r.compacting and r.numeralStyle]


def capable_compacting(renderers):
    return [r for r in renderers if r.compactionCapable and r.compacting]


def noncapable(renderers):
    return [r for r in renderers if not r.compactionCapable]


# --------------------------------------------------------------------------
# Boundary tick sets (obligation 5)
# --------------------------------------------------------------------------

def boundary_ticksets():
    powers = [10 ** k for k in range(16)]          # 1 .. 1e15
    return [
        [],                                        # the empty tick set
        [0],
        [1], [-1], [2], [-2], [10], [-10],
        [0, 1], [-1, 0, 1], [-2, -1, 0, 1, 2],
        [0, 1, 2, 3],
        powers,
        [-p for p in powers],
        [10 ** 8 + i for i in range(5)],           # the 1e8-shaped run
        [10 ** 8 + 2 * i for i in range(5)],
        [-(10 ** 8) + i for i in range(5)],
        [10 ** 9 + 5 * i for i in range(4)],
        [10 ** 12 + 10 ** 6 * i for i in range(4)],
        [FLOAT_EXACT - 2, FLOAT_EXACT - 1, FLOAT_EXACT],
        [FLOAT_EXACT],
        [-FLOAT_EXACT],
        [-FLOAT_EXACT, 0, FLOAT_EXACT],
        [FLOAT_EXACT - 10 ** 6, FLOAT_EXACT - 1, FLOAT_EXACT],
        [FLOAT_EXACT // 2, FLOAT_EXACT - 1],
    ]


# --------------------------------------------------------------------------
# Cross-check: set_locs + __call__ vs format_ticks (the scales.py call)
# --------------------------------------------------------------------------

def check_format_ticks_equivalence(state, renderers, ticks):
    for r in renderers:
        state["n_format_ticks_probes"] += 1
        if r.render(ticks) == r.render_via_format_ticks(ticks):
            state["format_ticks_agreements"] += 1
        else:
            state["disagreements"].append({
                "axiom": "binding/render",
                "reason": "set_locs+__call__ and format_ticks disagree",
                "renderer": r.describe(),
                "ticks": [str(t) for t in ticks[:8]],
                "via_call": r.render(ticks),
                "via_format_ticks": r.render_via_format_ticks(ticks)})


# --------------------------------------------------------------------------
# Convention non-triviality: the label text varies with the view interval
# --------------------------------------------------------------------------

def measure_iv_sensitivity(state):
    """The `convention` component carries the view interval because the text
    genuinely depends on it. Recorded as observations, not asserted: a renderer
    settling on one text regardless would simply make the component redundant,
    not any axiom unsound."""
    probes = [[0, 1, 2], [10 ** 8 + i for i in range(5)], [1, 10, 100],
              [-5, 0, 5], [FLOAT_EXACT - 1, FLOAT_EXACT]]
    for kind_name, _cls in FORMATTER_KINDS:
        modes = (False, True) if kind_name == "ScalarFormatter" else (False,)
        for mode in modes:
            for ticks in probes:
                texts = set()
                for iv in VIEW_INTERVALS:
                    r = TickRenderer(CONVENTION_INDEX[(kind_name, iv)],
                                     compacting=mode)
                    texts.add(tuple(r.render(ticks)))
                state["n_iv_sensitivity_probes"] += 1
                if len(texts) > 1:
                    state["n_iv_sensitive"] += 1
                    if len(state["iv_sensitive_witnesses"]) < 4:
                        variants = sorted(texts)
                        state["iv_sensitive_witnesses"].append({
                            "kind": kind_name, "compacting": mode,
                            "ticks": [str(t) for t in ticks[:8]],
                            "n_distinct_texts": len(texts),
                            "variants": [list(v[:6]) for v in variants[:2]]})


# --------------------------------------------------------------------------
# Recording what a non-capable renderer writes (obligation 6)
# --------------------------------------------------------------------------

def record_noncapable(state, renderers, ticks):
    """The axiom claims nothing about the label VALUES of a renderer offering no
    compaction control, so nothing is asserted here beyond `render_length`
    (checked separately). What such a renderer writes is recorded, including
    whether its labels happen to read back."""
    for r in renderers:
        labels = r.render(ticks)
        state["n_noncapable_observations"] += 1
        readable = 0
        for t, lab in zip(ticks, labels):
            try:
                if label_value(lab) == t:
                    readable += 1
            except ValueError:
                pass
        state["n_noncapable_labels"] += len(labels)
        state["n_noncapable_labels_reading_back"] += readable
        if len(state["noncapable_samples"]) < 6 and ticks:
            state["noncapable_samples"].append({
                "renderer": r.describe(),
                "ticks": [str(t) for t in ticks[:6]],
                "labels": labels[:6],
                "labels_reading_back": readable})


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    rng = random.Random(SEED)
    state = {
        "n_length": 0,
        "n_faithful": 0,
        "n_faithful_labels": 0,
        "n_compacting_probes": 0,
        "n_compacting_breaks": 0,
        "n_above_guard_probes": 0,
        "n_above_guard_breaks": 0,
        "n_above_guard_roundtrip_held": 0,
        "n_format_ticks_probes": 0,
        "format_ticks_agreements": 0,
        "n_iv_sensitivity_probes": 0,
        "n_iv_sensitive": 0,
        "n_noncapable_observations": 0,
        "n_noncapable_labels": 0,
        "n_noncapable_labels_reading_back": 0,
        "n_fuzz_draws": 0,
        "n_boundary_ticksets": 0,
        "f2p_named_witness_breaks": False,
        "f2p_labels_compacting": [],
        "f2p_labels_uncompacted": [],
        "disagreements": [],
        "compacting_break_witnesses": [],
        "guard_tight_witnesses": [],
        "guard_narrow_witnesses": [],
        "iv_sensitive_witnesses": [],
        "noncapable_samples": [],
        "n_dressed_probes": 0,
        "n_dressed_breaks": 0,
        "n_dressed_roundtrip_held": 0,
        "dressed_break_witnesses": [],
        "dressed_narrow_witnesses": [],
        "dressed_modes_unmeasured": [],
        "dressed_by_mode": {},
        "dressed_locale": None,
        "dressed_locale_sep": None,
    }

    renderers = all_renderers()
    cap_off = capable_uncompacted(renderers)
    cap_on = capable_compacting(renderers)
    noncap = noncapable(renderers)

    # Every formatter kind reachable at the two call sites must be present, and
    # the capability split must be the measured one.
    kinds_capable = sorted({r.kind for r in renderers if r.compactionCapable})
    kinds_noncapable = sorted({r.kind for r in renderers
                               if not r.compactionCapable})
    if kinds_capable != ["ScalarFormatter"] or kinds_noncapable != [
            "LogFormatter", "LogFormatterSciNotation"]:
        raise AssertionError(
            "coverage/capability binding unmet: capable=%r non-capable=%r"
            % (kinds_capable, kinds_noncapable))

    with _silence():
        warnings.simplefilter("ignore")
        with np.errstate(all="ignore"):

            # ---- obligation 5: boundary tick sets ------------------------
            bset = boundary_ticksets()
            state["n_boundary_ticksets"] = len(bset)
            for ticks in bset:
                check_length(state, renderers, ticks)            # obligation 1
                check_faithful(state, cap_off, ticks)            # obligation 2
                check_format_ticks_equivalence(state, renderers, ticks)
                record_noncapable(state, noncap, ticks)          # obligation 6
                for r in cap_on:                                 # obligation 3
                    witness_default_breaks(state, r, ticks)

            # ---- obligation 3, named witness: the 1e8-shaped tick run ----
            # The renderer state a legend describing the issue's quantity meets:
            # a capable renderer standing in the compacting mode, over the view
            # interval that quantity's range presents. MEASURED to write
            # '0'..'4' there, so its labels do not read back to their ticks --
            # the guarded faithfulness axiom is claiming something.
            f2p_conv = CONVENTION_INDEX[("ScalarFormatter", F2P_VIEW_INTERVAL)]
            f2p_on = TickRenderer(f2p_conv, compacting=True)
            f2p_off = TickRenderer(f2p_conv, compacting=False)
            state["f2p_labels_compacting"] = f2p_on.render(F2P_TICKS)
            state["f2p_labels_uncompacted"] = f2p_off.render(F2P_TICKS)
            state["f2p_named_witness_breaks"] = bool(
                witness_default_breaks(state, f2p_on, F2P_TICKS))
            check_length(state, [f2p_on, f2p_off], F2P_TICKS)
            check_faithful(state, [f2p_off], F2P_TICKS)

            # ---- obligation 4: guard tightness just above 2^53 -----------
            check_guard_tightness(state)

            # ---- numeralStyle guard tightness: a dressed renderer really
            # ---- does not read back, even with compaction fully off -------
            check_dressed_breaks(state)

            # ---- convention non-triviality (view interval is load-bearing)
            measure_iv_sensitivity(state)

            # ---- obligation 5: seeded fuzz across kinds/modes/intervals ---
            magnitudes = [1, 2, 10, 100, 10 ** 3, 10 ** 6, 10 ** 8, 10 ** 9,
                          10 ** 12, 10 ** 15, FLOAT_EXACT]
            for _ in range(FUZZ_TICKSETS):
                n = rng.randint(0, 7)
                mag = rng.choice(magnitudes)
                ticks = [rng.randint(-mag, mag) for _ in range(n)]
                conv_cap = rng.choice(CAPABLE_CONVENTIONS)
                conv_non = rng.choice(NONCAPABLE_CONVENTIONS)
                r_off = TickRenderer(conv_cap, compacting=False)
                r_on = TickRenderer(conv_cap, compacting=True)
                r_non = TickRenderer(conv_non, compacting=False)
                cohort = [r_off, r_on, r_non]
                check_length(state, cohort, ticks)               # obligation 1
                check_faithful(state, [r_off], ticks)            # obligation 2
                witness_default_breaks(state, r_on, ticks)       # obligation 3
                record_noncapable(state, [r_non], ticks)         # obligation 6
                state["n_fuzz_draws"] += len(cohort)

            # ---- obligation 5: draws hugging the 2^53 guard from below ----
            for _ in range(FUZZ_BOUNDARY_TICKSETS):
                n = rng.randint(1, 5)
                sign = rng.choice([1, -1])
                ticks = [sign * (FLOAT_EXACT - rng.randint(0, 10 ** 6))
                         for _ in range(n)]
                conv_cap = rng.choice(CAPABLE_CONVENTIONS)
                conv_non = rng.choice(NONCAPABLE_CONVENTIONS)
                r_off = TickRenderer(conv_cap, compacting=False)
                r_non = TickRenderer(conv_non, compacting=False)
                cohort = [r_off, r_non]
                check_length(state, cohort, ticks)
                check_faithful(state, [r_off], ticks)
                record_noncapable(state, [r_non], ticks)
                state["n_fuzz_draws"] += len(cohort)

    # ---- verdict -----------------------------------------------------------
    failures = []
    if state["disagreements"]:
        failures.append("axiom disagreement(s) observed: %d"
                        % len(state["disagreements"]))
    if state["n_compacting_breaks"] < MIN_COMPACTING_BREAKS:
        failures.append(
            "non-vacuity unmet: only %d/%d compacting-mode observations failed "
            "to read back (need >= %d); the guarded faithfulness axiom would be "
            "vacuous" % (state["n_compacting_breaks"],
                         state["n_compacting_probes"], MIN_COMPACTING_BREAKS))
    if not state["f2p_named_witness_breaks"]:
        failures.append(
            "non-vacuity unmet at the named witness: the compacting renderer's "
            "labels for the 1e8-shaped tick run (%r) all read back to their "
            "ticks" % (state["f2p_labels_compacting"],))
    if state["n_above_guard_breaks"] == 0:
        failures.append(
            "guard-tightness unmet: the round trip was never observed to stop "
            "holding above 2^53, so the axiom's domain restriction has no "
            "measured justification")
    if state["n_above_guard_roundtrip_held"] > 0:
        failures.append(
            "guard is needlessly narrow: the round trip HELD in %d/%d "
            "observations above 2^53 (witnesses recorded), so the axiom "
            "restricts its domain further than the renderer requires"
            % (state["n_above_guard_roundtrip_held"],
               state["n_above_guard_probes"]))
    # The faithfulness axiom is universally quantified over TICK SETS at a given
    # renderer state, so what justifies excluding a dressed renderer is that SOME
    # tick set at that state fails the round trip -- one such tick set already
    # makes the unguarded axiom false there. A dressed renderer that happens to
    # write a particular tick set plainly (a locale-grouped renderer over
    # single-digit ticks needs no separator) is therefore not evidence that the
    # guard is too narrow. So tightness is required PER MODE, existentially: every
    # dressed mode that was measured must break somewhere.
    for mode_name, _attr in DRESSED_MODES:
        if mode_name in state["dressed_modes_unmeasured"]:
            continue
        seen = state["dressed_by_mode"].get(mode_name)
        if not seen or seen["probes"] == 0:
            failures.append(
                "numeralStyle-guard coverage unmet: dressed mode %s was never "
                "probed" % mode_name)
        elif seen["breaks"] == 0:
            failures.append(
                "numeralStyle-guard tightness unmet for %s: the round trip held "
                "at every one of %d observations, so excluding this mode from the "
                "faithfulness axiom has no measured justification"
                % (mode_name, seen["probes"]))
    if state["n_dressed_breaks"] == 0:
        failures.append(
            "numeralStyle-guard tightness unmet: the round trip was never "
            "observed to stop holding for a renderer that dresses its labels up, "
            "so that restriction on the faithfulness axiom has no measured "
            "justification")
    if state["format_ticks_agreements"] != state["n_format_ticks_probes"]:
        failures.append("binding unmet: set_locs+__call__ and format_ticks "
                        "disagreed")
    if state["n_fuzz_draws"] < MIN_FUZZ_DRAWS:
        failures.append("fuzz budget unmet: %d draws < %d"
                        % (state["n_fuzz_draws"], MIN_FUZZ_DRAWS))
    if state["n_faithful_labels"] == 0 or state["n_length"] == 0:
        failures.append("probe made no observations")

    checked = (state["n_length"] + state["n_faithful"]
               + state["n_compacting_probes"] + state["n_above_guard_probes"]
               + state["n_format_ticks_probes"]
               + state["n_noncapable_observations"]
               + state["n_iv_sensitivity_probes"]
               + state["n_dressed_probes"])

    report = {
        "status": "pass" if not failures else "fail",
        "instance": INSTANCE,
        "checked": checked,
        "seed": SEED,
        "matplotlib": matplotlib.__version__,
        "guard": FLOAT_EXACT,
        "conventions": len(CONVENTIONS),
        "formatter_kinds_capable": kinds_capable,
        "formatter_kinds_noncapable": kinds_noncapable,
        # obligation 1
        "render_length_checks": state["n_length"],
        # obligation 2
        "faithful_checks": state["n_faithful"],
        "faithful_label_comparisons": state["n_faithful_labels"],
        # obligation 3
        "compacting_probes": state["n_compacting_probes"],
        "compacting_readback_breaks": state["n_compacting_breaks"],
        "compacting_break_witnesses": state["compacting_break_witnesses"],
        "f2p_named_witness_breaks": state["f2p_named_witness_breaks"],
        "f2p_labels_compacting": state["f2p_labels_compacting"],
        "f2p_labels_uncompacted": state["f2p_labels_uncompacted"],
        # obligation 4
        "above_guard_probes": state["n_above_guard_probes"],
        "above_guard_breaks": state["n_above_guard_breaks"],
        "above_guard_roundtrip_held": state["n_above_guard_roundtrip_held"],
        "guard_tight_witnesses": state["guard_tight_witnesses"],
        "guard_narrow_witnesses": state["guard_narrow_witnesses"],
        # numeralStyle guard tightness
        "dressed_probes": state["n_dressed_probes"],
        "dressed_readback_breaks": state["n_dressed_breaks"],
        "dressed_roundtrip_held": state["n_dressed_roundtrip_held"],
        "dressed_break_witnesses": state["dressed_break_witnesses"],
        "dressed_narrow_witnesses": state["dressed_narrow_witnesses"],
        "dressed_modes_unmeasured": state["dressed_modes_unmeasured"],
        "dressed_by_mode": state["dressed_by_mode"],
        "dressed_locale": state["dressed_locale"],
        "dressed_locale_sep": state["dressed_locale_sep"],
        # obligation 5
        "boundary_ticksets": state["n_boundary_ticksets"],
        "fuzz_draws": state["n_fuzz_draws"],
        "fuzz_ticksets": FUZZ_TICKSETS,
        "fuzz_boundary_ticksets": FUZZ_BOUNDARY_TICKSETS,
        # obligation 6
        "noncapable_observations": state["n_noncapable_observations"],
        "noncapable_labels": state["n_noncapable_labels"],
        "noncapable_labels_reading_back":
            state["n_noncapable_labels_reading_back"],
        "noncapable_samples": state["noncapable_samples"],
        # binding cross-checks
        "format_ticks_probes": state["n_format_ticks_probes"],
        "format_ticks_agreements": state["format_ticks_agreements"],
        "iv_sensitivity_probes": state["n_iv_sensitivity_probes"],
        "iv_sensitive": state["n_iv_sensitive"],
        "iv_sensitive_witnesses": state["iv_sensitive_witnesses"],
        "disagreements": state["disagreements"][:5],
        "failures": failures,
    }
    print(json.dumps(report))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
