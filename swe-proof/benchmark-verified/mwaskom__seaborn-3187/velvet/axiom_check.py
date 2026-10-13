#!/usr/bin/env python3
"""G-AX executable soundness check for mwaskom__seaborn-3187.

Executes the REAL callees the bundle axiomatizes — matplotlib's tick renderers —
and asserts every observation meets the axiom's `ensures`. Imports only
matplotlib (the library whose renderers the change configures) + stdlib; exit 0
iff every obligation holds.

The modeled site hands a renderer a list of tick positions and shows what comes
back as legend text. A renderer is free to ABBREVIATE those labels by hoisting
something shared out of them — a common additive term, or a common power of ten
— and to report the hoisted term SEPARATELY (matplotlib draws it beside the
axis: `Formatter.get_offset()`). A legend has nowhere to draw a separately
reported term, so whatever is hoisted out of the labels is simply lost.

These renderers are PARTIAL. For some installations and tick lists they return
no labels at all: they fail outright, and the failure escapes the modeled region
(measured here at both sites), so no legend exists there for any clause to
describe. The model says so rather than assuming otherwise, with two opaque
domain predicates that this file makes OPERATIONAL — `renders(cfg, om, sm,
ticks)` holds exactly when the numeric renderer RETURNS for those arguments, and
`rendersLog(cfg, ticks)` likewise for the log renderer — and every fact below is
asserted only INSIDE the relevant domain. Four obligations come with a modeled
domain, and all four are checked (`check_domain_*`):

    * it is DETERMINISTIC — the same arguments return twice or raise twice, so
      "returns" is a property of (handle, switches, ticks) and not of the run;
    * it is NON-EMPTY (`renders_nonvacuous`) — some installation and non-empty
      tick list are in BOTH domains at once;
    * it is NOT IDLE — some installation and tick list are OUTSIDE it, with the
      boundary pinned by a measured pair, and it genuinely depends on all of its
      arguments (there is an installation and tick list the numeric renderer
      refuses with the switches off and accepts with the multiplicative switch
      on, and one the log renderer accepts where the numeric one refuses); and,
      most important,
    * it does not duck any input the modeled sites can actually produce — every
      (installation, tick list) either SITE produces on the grids below is in the
      domain, and where the domain fails the site produces no legend at all
      rather than a wrong one, which is what makes the restriction a statement
      about the model's scope rather than an escape hatch.

Axioms validated (Solution.lean `axioms` region; mapping.md §3, §3.4):

  RendererConfig
      An opaque handle for the renderer AS INSTALLED: its own presentation
      settings plus the axis interval it is attached to, everything EXCEPT the
      two shared-term switches. Modeled here by `_Cfg`, which can build the same
      renderer state repeatedly. Two obligations come with calling it a handle:
      the labels must be a FUNCTION of (handle, switches, ticks) — checked by
      building each configuration twice and comparing byte-for-byte
      (`check_handle_is_a_function`) — and residual settings on the handle must
      not be able to defeat the switches, so the configurations below include
      ones that arrive with a shared term already hoisted (a numeric
      `set_useOffset(3.0)`, `set_scientific(True)`, non-default power limits).

  renderTicks (cfg, offsetMode, scaleMode, ticks) -> labels
      `ScalarFormatter.format_ticks(ticks)` on that renderer after the two
      switches are set:
        offsetMode == useOffset      (set_useOffset)   — additive common term
        scaleMode  == scientific     (set_scientific)  — multiplicative 10^k
    (renderTicks_length)  len(labels) == len(ticks) — every cfg, every switch
        setting, every tick list IN `renders cfg om sm ticks`.

  sharedTerm (cfg, offsetMode, scaleMode, ticks) -> str
      The term the renderer reports separately instead of putting it in any
      label: `Formatter.get_offset()` after that same rendering. Empty exactly
      when nothing was hoisted out.
    (sharedTerm_none)     with BOTH switches off, `get_offset() == ""` — for
        every renderer configuration and every tick list the renderer RETURNS
        labels for with both switches off. This is the axiom the
        specification's discriminating clause rests on, and unlike a claim about
        the numeric text of a label it is true of every configuration: a renderer
        may legitimately be set up to print typeset labels that no numeric
        reading parses at all (`useMathText`, `text.usetex`) yet still hoist
        nothing.
    (sharedTerm_hoists)   NON-VACUITY: some configuration and tick list are in
        the domain with both switches ON and DO hoist a term out there (the axiom
        states both halves as one conjunction, so the witness must satisfy both),
        so `sharedTerm ... = ""` is a real
        obligation rather than an idle one. Witnessed on the very data the
        instance's tests use (positions ~1e8), where the default configuration
        reports `+1e8` separately and prints labels of `0`, `20`, `40`, ...

  renderLog (cfg, ticks) -> labels        (the log-spaced renderer)
      The log renderer of that SAME installation, driven the way the site drives
      it (`set_locs(ticks)`, then one call per tick).
    (renderLog_length)    len(labels) == len(ticks), on `rendersLog cfg ticks`.
      Label text unconstrained.
      Why it takes the handle rather than the ticks alone: this renderer consults
      the interval it is attached to — at the modeled site, the span of the DATA
      the legend describes, which is NOT the span of the ticks — and abbreviates
      a label to a power-of-ten form once that interval is wide enough. Two
      obligations therefore come with it, and they are the two halves of the
      claim that `renderLog` is the site's own function:
        (h) the handle argument is NOT idle — the same tick list prints two
            DIFFERENT label lists on two installations differing only in that
            interval (`check_log_handle_matters`), so a ticks-only model could
            not be a function of the observable at all; and
        (i) `renderLog(cfg, ticks)` reproduces the real site's log-path labels
            byte-for-byte over every (interval, tick list) pair the site itself
            produces on a grid of data limits, while a ticks-only model
            disagrees on some of them (`check_log_site_faithful`).

Modelling facts about the OTHER renderers a continuous scale can install
(mapping.md §1.1, §3.3) — these are what make `legendLabels`'s `modesAvailable`
/ `ownLabels` inputs a faithful model of the site rather than a convenience:

  (a) modesAvailable is ONE boolean, faithfully. The site asks two separate
      questions (`hasattr(fmt, "set_useOffset")`, `hasattr(fmt, "set_scientific")`).
      For every renderer a continuous scale can install the two answers AGREE, so
      a single Bool models the pair without losing a case — checked exhaustively
      over every `Formatter` subclass matplotlib exposes in the two modules those
      renderers come from, so no reachable subclass is left unexamined.
  (b) modesAvailable == False is REAL, not empty: of every such subclass only
      `ScalarFormatter` answers yes, so every other one reaches the site with the
      two questions answered no.
  (c) ownLabels has one entry per tick. `Formatter.format_ticks` is
      `[self(value, i) for i, value in enumerate(values)]` after `set_locs`, i.e.
      one label per tick for every subclass — which is what `require
      ownLabels.length = ticks.length` states.
  (d) on a modesAvailable == False renderer the site is INERT: because both
      questions answer no, neither setter runs, so the labels are exactly the
      renderer's own (`ensures modesAvailable = false -> labels = ownLabels`).
      Checked by running the site's own guarded sequence and comparing.
  (e) those renderers hoist nothing to begin with (`get_offset() == ""`), which
      is why the `modesAvailable = false` arm needs no shared-term clause of its
      own.

And the link from the verified clause to the instance's own test assertion
(refinement.md §D), which the specification deliberately does NOT state as an
obligation because it is not true of every renderer configuration:

  (f) on the configurations the tests actually exercise (default rcParams: plain
      decimal labels), `sharedTerm == ""` labels read back with `float()` to
      their own tick and so exceed the `1e7` the assertion checks, while EVERY
      hoisting configuration produces labels that do not; and
  (g) the exception is explicit and measured: with `useMathText` / `usetex`
      labels are typeset (`$\\mathdefault{100000000}$`) and `float()` cannot read
      them back AT ALL, even though nothing is hoisted. A read-back obligation
      would therefore be UNSOUND as a specification clause for those
      configurations, while `sharedTerm == ""` holds for all of them.
"""
import random
import sys

import matplotlib as mpl
mpl.use("Agg")
import matplotlib.dates as mdates      # noqa: E402
import matplotlib.ticker as mticker    # noqa: E402


class _DummyAxis:
    """The minimal axis the formatters read: just a view interval, exactly as
    seaborn supplies via its own `dummy_axis` / `set_view_interval`."""

    def __init__(self, lo, hi):
        self._lo, self._hi = lo, hi

    def get_view_interval(self):
        return (self._lo, self._hi)


class _Cfg:
    """A RendererConfig handle: everything about the installed renderer EXCEPT
    the two shared-term switches, in a form that can be rebuilt on demand.

    `rc` covers the public rcParams a user can set without touching seaborn at
    all (`axes.formatter.use_mathtext`, `.use_locale`, `.useoffset`, `.limits`,
    `.offset_threshold`, `text.usetex`); `kwargs` covers
    `Continuous().label(formatter=ScalarFormatter(...))`; `pre` covers residual
    state a caller may have configured on the instance before it reaches the
    site; `view` covers the axis interval the renderer reads.
    """

    def __init__(self, name, rc=None, kwargs=None, pre=(), view=None):
        self.name, self.rc, self.kwargs = name, dict(rc or {}), dict(kwargs or {})
        self.pre, self.view = tuple(pre), view

    def build(self, locs):
        with mpl.rc_context(self.rc):
            f = mticker.ScalarFormatter(**self.kwargs)
        lo, hi = self.view or ((min(locs), max(locs)) if locs else (0.0, 1.0))
        f.axis = _DummyAxis(lo, hi)
        for meth, arg in self.pre:
            getattr(f, meth)(arg)
        return f

    def build_log(self, locs):
        """The LOG renderer of this same installation: a different renderer kind
        on the same axis interval, which is exactly how the modeled site's two
        arms relate (one handle, two renderers)."""
        lo, hi = self.view or ((min(locs), max(locs)) if locs else (1.0, 10.0))
        f = mticker.LogFormatter()
        f.axis = _DummyAxis(lo, hi)
        return f


CFGS = [
    _Cfg("plain"),
    # reachable with no caller-supplied formatter at all, via public rcParams:
    _Cfg("rc_mathtext", rc={"axes.formatter.use_mathtext": True}),
    _Cfg("rc_locale", rc={"axes.formatter.use_locale": True}),
    _Cfg("rc_useoffset_off", rc={"axes.formatter.useoffset": False}),
    _Cfg("rc_limits_tight", rc={"axes.formatter.limits": (-1, 1)}),
    _Cfg("rc_offset_threshold_1", rc={"axes.formatter.offset_threshold": 1}),
    _Cfg("rc_usetex", rc={"text.usetex": False}),
    # ... and via label(formatter=ScalarFormatter(...)):
    _Cfg("kw_mathtext", kwargs={"useMathText": True}),
    _Cfg("kw_locale", kwargs={"useLocale": True}),
    _Cfg("kw_useoffset_true", kwargs={"useOffset": True}),
    _Cfg("kw_useoffset_numeric", kwargs={"useOffset": 3.0}),
    # residual state already hoisting a shared term when the site is reached:
    _Cfg("pre_useoffset_numeric", pre=[("set_useOffset", 12345.0)]),
    _Cfg("pre_scientific_on", pre=[("set_scientific", True)]),
    _Cfg("pre_powerlimits", pre=[("set_powerlimits", (-1, 1))]),
    _Cfg("pre_both", pre=[("set_useOffset", 7.0), ("set_scientific", True),
                          ("set_powerlimits", (-2, 2))]),
    # an axis interval WIDER than the ticks (what a real axis usually has):
    _Cfg("wide_view", view=(-1e9, 1e9)),
]

# The tick lists the site really produces, plus boundary shapes. These are
# FLOATS, including non-integral spacings: the levels a locator emits for the
# instance's own test data are half-integral (`1e8, 1e8+2.5, 1e8+5, ...`).
BOUNDARY_TICKS = [
    [0.0],
    [0.0, 1.0, 2.0, 3.0],
    [-2.0, -1.0, 0.0, 1.0, 2.0],
    [1e8, 1e8 + 20.0, 1e8 + 40.0, 1e8 + 60.0, 1e8 + 80.0],          # F2P, site A
    [1e8, 1e8 + 2.5, 1e8 + 5.0, 1e8 + 7.5, 1e8 + 10.0, 1e8 + 12.5],  # F2P, site B
    [0.21, 0.225, 0.24, 0.255, 0.27],                                # P2P levels
    [0.2, 0.22, 0.24, 0.26, 0.28],                                   # P2P levels
    [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0],
    [1e6 * k for k in (3, 4, 5, 6)],
    [1e9 + 5.0 * k for k in range(4)],
    [-1e8 + 5.0 * k for k in range(5)],
    [1e12 + 1e6 * k for k in range(4)],
    [1e-7, 2e-7, 3e-7],
    [1.0 / 3.0, 2.0 / 3.0, 1.0],
    [-0.878368, -0.740369, 0.315822],
    [float(2 ** 53), float(2 ** 53) - 2.0, float(2 ** 53) - 4.0],
    [1e8, 1e8],                                                      # repeated
    [],
]

LOG_TICKS = [[10.0 ** (2 * k) for k in range(1, 5)], [1.0, 10.0, 100.0], []]

# Installations for the LOG renderer. The interval is given EXPLICITLY and is
# deliberately not the span of the ticks: at the modeled site the interval is the
# span of the DATA the legend describes, and the ticks are what a locator chose
# inside it, so the two coincide only by accident. A configuration list that
# derived the interval from the ticks would be unable to see the interval's
# effect at all — which is the whole reason `renderLog` takes the handle.
LOG_CFGS = [
    _Cfg("log_view_1_1e5", view=(1.0, 1e5)),
    _Cfg("log_view_1_1p5e5", view=(1.0, 1.5e5)),
    _Cfg("log_view_1_1e6", view=(1.0, 1e6)),
    _Cfg("log_view_half_2e5", view=(0.5, 2e5)),
    _Cfg("log_view_1em3_1e3", view=(1e-3, 1e3)),
    _Cfg("log_view_1_1e8", view=(1.0, 1e8)),
    _Cfg("log_view_1e2_1e7", view=(1e2, 1e7)),
]

# The far end of the double range, which is where these renderers stop being
# total. `_MAXF` is the largest finite double; an installation whose interval
# spans MORE than that has an infinite span, and the numeric renderer takes the
# base-ten magnitude of that span whenever it has fewer than two tick positions
# of its own to measure. The grid straddles the boundary deliberately, so the
# checks below see BOTH sides of it rather than only the comfortable side.
_MAXF = 1.7976931348623157e308
_INF = float("inf")
_NAN = float("nan")

EXTREME_CFGS = [
    _Cfg("x_view_full", view=(-_MAXF, _MAXF)),
    _Cfg("x_view_9e307", view=(-9e307, 9e307)),
    _Cfg("x_view_8e307", view=(-8e307, 8e307)),
    _Cfg("x_view_1e308", view=(-1e308, 1e308)),
    _Cfg("x_view_half_max", view=(-_MAXF / 2, _MAXF / 2)),
    _Cfg("x_view_zero_max", view=(0.0, _MAXF)),
    _Cfg("x_view_1e300", view=(-1e300, 1e300)),
    _Cfg("x_view_1e300_pos", view=(1e300, 1.5e300)),
    _Cfg("x_view_mathtext_full", rc={"axes.formatter.use_mathtext": True},
         view=(-_MAXF, _MAXF)),
]

EXTREME_TICKS = [
    [0.0],
    [1e300],
    [-_MAXF, _MAXF],
    [_MAXF],
    [1e300, 2e300],
    [-1e308, 1e308],
    [0.0, 1.0],
    [1e300, 1e300 + 1e290, 1e300 + 2e290],
    [],
]

# Non-finite positions: `List Float` in Lean includes them, so a model that
# claimed totality would be claiming something about these too.
NONFINITE_TICKS = [
    [_INF],
    [-_INF],
    [_NAN],
    [0.0, _INF],
    [1.0, _NAN, 2.0],
    [-_INF, _INF],
]


# --- the axiomatized callees --------------------------------------------------

def render_ticks(cfg, offset_mode, scale_mode, ticks):
    """REAL renderer == axiom `renderTicks`; returns (labels, shared_term)."""
    locs = [float(t) for t in ticks]
    f = cfg.build(locs)
    f.set_useOffset(offset_mode)
    f.set_scientific(scale_mode)
    labels = list(f.format_ticks(locs))
    return labels, f.get_offset()


def shared_term(cfg, offset_mode, scale_mode, ticks):
    """REAL separately-reported term == axiom `sharedTerm`."""
    return render_ticks(cfg, offset_mode, scale_mode, ticks)[1]


def render_log(cfg, ticks):
    """REAL log renderer == axiom `renderLog`: the log renderer of installation
    `cfg`, driven by the site's own call sequence (`set_locs`, then one call per
    tick — `Formatter.format_ticks` is that sequence)."""
    locs = [float(t) for t in ticks]
    f = cfg.build_log(locs)
    f.set_locs(locs)
    return [f(x) for x in locs]


def render_log_ticks_only(ticks):
    """A model of the log renderer that reads ONLY the ticks, taking the interval
    to be their own span. Kept solely as the NEGATIVE control for the handle
    argument: `check_log_site_faithful` measures where it and the real site part
    company, so the widening is justified by a divergence rather than by
    caution."""
    locs = [float(t) for t in ticks]
    f = mticker.LogFormatter()
    f.axis = _DummyAxis(*((min(locs), max(locs)) if locs else (1.0, 10.0)))
    f.set_locs(locs)
    return [f(x) for x in locs]


def renders(cfg, offset_mode, scale_mode, ticks):
    """The axiom's domain predicate `renders`, made OPERATIONAL: it holds exactly
    when the real numeric renderer RETURNS a label list for these arguments.
    Returns (in_domain, detail) so the caller can report what the failure was."""
    try:
        render_ticks(cfg, offset_mode, scale_mode, ticks)
        return True, ""
    except Exception as exc:                                    # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, exc)


def renders_log(cfg, ticks):
    """The axiom's domain predicate `rendersLog`, made operational the same way."""
    try:
        render_log(cfg, ticks)
        return True, ""
    except Exception as exc:                                    # noqa: BLE001
        return False, "%s: %s" % (type(exc).__name__, exc)


def _reads_back(label):
    """`float(text)` the way the instance's own assertion reads a legend label,
    normalizing matplotlib's Unicode minus (U+2212). None if it cannot be read."""
    try:
        return float(label.replace("−", "-"))
    except ValueError:
        return None


# --- axiom obligations -------------------------------------------------------

def check_length_and_none(cfg, ticks, tally=None):
    """renderTicks_length for all four switch settings + sharedTerm_none, each ON
    THE DOMAIN `renders cfg om sm ticks` — which is what the axioms now say.

    Outside the domain there is nothing to check and nothing is claimed, but the
    fact is not simply skipped: the refusal is required to be DETERMINISTIC (the
    same arguments refuse twice, with the same exception type), because otherwise
    "returns" would not be a property of (handle, switches, ticks) and the domain
    predicate could not be a function of them either. `tally` counts in-domain and
    out-of-domain observations so the caller can prove the guard is not idle."""
    for om in (False, True):
        for sm in (False, True):
            ok, why = renders(cfg, om, sm, ticks)
            if not ok:
                ok2, why2 = renders(cfg, om, sm, ticks)
                assert not ok2 and why2.split(":")[0] == why.split(":")[0], (
                    "the domain is not deterministic: cfg=%s ticks=%r om=%s "
                    "sm=%s refused with %r then gave %r"
                    % (cfg.name, ticks, om, sm, why, (ok2, why2)))
                if tally is not None:
                    tally["out"] += 1
                    tally.setdefault("examples", [])
                    if len(tally["examples"]) < 4:
                        tally["examples"].append(
                            (cfg.name, list(ticks), om, sm, why))
                continue
            if tally is not None:
                tally["in"] += 1
            labels, off = render_ticks(cfg, om, sm, ticks)
            assert len(labels) == len(ticks), (
                "renderTicks_length unsound: cfg=%s ticks=%r om=%s sm=%s -> %d "
                "labels" % (cfg.name, ticks, om, sm, len(labels)))
            if not om and not sm:
                assert off == "", (
                    "sharedTerm_none unsound: cfg=%s ticks=%r reported %r "
                    "separately with both switches off"
                    % (cfg.name, ticks, off))


def check_handle_is_a_function(cfg, ticks):
    """`renderTicks`/`sharedTerm` are FUNCTIONS of (handle, switches, ticks):
    rebuilding the same configuration reproduces the same labels and the same
    separately-reported term, so nothing outside the handle is being observed."""
    for om, sm in ((False, False), (True, True)):
        if not renders(cfg, om, sm, ticks)[0]:
            continue                      # outside the domain; nothing is claimed
        a = render_ticks(cfg, om, sm, ticks)
        b = render_ticks(cfg, om, sm, ticks)
        assert a == b, (
            "RendererConfig is not a faithful handle: cfg=%s ticks=%r om=%s "
            "sm=%s gave %r then %r" % (cfg.name, ticks, om, sm, a, b))


def check_log_length(cfg, ticks, tally=None):
    """renderLog_length ON `rendersLog cfg ticks`, with the same determinism
    obligation on the refusals as the numeric renderer's."""
    ok, why = renders_log(cfg, ticks)
    if not ok:
        ok2, why2 = renders_log(cfg, ticks)
        assert not ok2 and why2.split(":")[0] == why.split(":")[0], (
            "the log domain is not deterministic: cfg=%s ticks=%r refused with "
            "%r then gave %r" % (cfg.name, ticks, why, (ok2, why2)))
        if tally is not None:
            tally["out"] += 1
            tally.setdefault("examples", [])
            if len(tally["examples"]) < 4:
                tally["examples"].append((cfg.name, list(ticks), why))
        return
    if tally is not None:
        tally["in"] += 1
    labels = render_log(cfg, ticks)
    assert len(labels) == len(ticks), (
        "renderLog_length unsound: cfg=%s ticks=%r -> %d labels"
        % (cfg.name, ticks, len(labels)))


def check_log_handle_is_a_function(cfg, ticks):
    """`renderLog` is a FUNCTION of (handle, ticks): the same installation
    rebuilt prints the same labels, so nothing outside the handle is observed."""
    if not renders_log(cfg, ticks)[0]:
        return                            # outside the domain; nothing is claimed
    a, b = render_log(cfg, ticks), render_log(cfg, ticks)
    assert a == b, (
        "renderLog is not a function of (handle, ticks): cfg=%s ticks=%r gave "
        "%r then %r" % (cfg.name, ticks, a, b))


def check_log_handle_matters():
    """Obligation (h): the handle argument of `renderLog` is NOT idle. Some tick
    list prints DIFFERENT labels on two installations that differ only in the
    interval the renderer is attached to — so the observable is not a function of
    the ticks alone and `renderLog : ticks -> labels` could not model this site.
    Returns the witnesses (ticks, cfg_a, labels_a, cfg_b, labels_b)."""
    wit = []
    for ticks in LOG_TICKS:
        if not ticks:
            continue
        seen = {}
        for cfg in LOG_CFGS:
            seen[cfg.name] = tuple(render_log(cfg, ticks))
        names = sorted(seen)
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                if seen[a] != seen[b]:
                    wit.append((list(ticks), a, list(seen[a]), b, list(seen[b])))
    assert wit, (
        "renderLog's handle argument is unwitnessed: every installation printed "
        "the same labels for every tick list, so the widened signature would be "
        "unmotivated by measurement")
    return wit


# --- the modeled DOMAIN itself (mapping.md §3.4) ------------------------------

def check_domain_nonvacuous():
    """`renders_nonvacuous`: SOME installation and NON-EMPTY tick list are in both
    domains at once — `ticks ≠ [] ∧ renders cfg false false ticks ∧ rendersLog cfg
    ticks`. Without this the two guards could be empty and every guarded fact
    (and every obligation that consumes one) would be vacuous.

    Returns the witness (cfg name, ticks, numeric labels, log labels)."""
    for cfg in LOG_CFGS + CFGS:
        for ticks in ([1.0, 100.0, 10000.0], [1.0, 10.0, 100.0],
                      BOUNDARY_TICKS[3], [1.0]):
            if not ticks:
                continue
            if renders(cfg, False, False, ticks)[0] and renders_log(cfg, ticks)[0]:
                return (cfg.name, list(ticks),
                        render_ticks(cfg, False, False, ticks)[0],
                        render_log(cfg, ticks))
    raise AssertionError(
        "renders_nonvacuous unwitnessed: no installation and non-empty tick list "
        "lay in both domains, so both guards would be empty and every guarded "
        "fact vacuous")


def check_domain_not_idle():
    """The domain is a REAL restriction, not decoration. Four measurements:

      (1) something is OUTSIDE it: an installation whose interval spans more than
          the largest finite double, with a single tick position and both switches
          off, produces no labels at all;
      (2) the boundary is pinned by a PAIR that differs only in that span, so the
          exclusion is attributable to the span rather than to the shape of the
          configuration;
      (3) it depends on the SWITCHES, not just on (cfg, ticks) — the same
          installation and tick list are outside the domain with both switches off
          and inside it with the multiplicative switch on. This is why `renders`
          takes the switches, and why a guard stated only at `false false` would be
          a claim about a different set of calls; and
      (4) the two renderers' domains DIFFER — the log renderer returns labels for
          a tick list at an installation where the numeric one with both switches
          off does not, which is why there are two predicates rather than one.

    Returns (n_out, boundary_pair, switch_witness, log_wider_witness)."""
    n_out = 0
    for cfg in EXTREME_CFGS:
        for ticks in EXTREME_TICKS:
            for om in (False, True):
                for sm in (False, True):
                    if not renders(cfg, om, sm, ticks)[0]:
                        n_out += 1
    for cfg in CFGS:
        for ticks in NONFINITE_TICKS:
            for om in (False, True):
                for sm in (False, True):
                    if not renders(cfg, om, sm, ticks)[0]:
                        n_out += 1
    assert n_out > 0, (
        "the modeled domain excludes nothing on a grid reaching the end of the "
        "double range and including non-finite positions, so a guarded fact would "
        "be indistinguishable from an unguarded one and the guard could not be "
        "load-bearing")

    # (2) the boundary pair: same shape, spans either side of the largest double.
    wide = _Cfg("boundary_9e307", view=(-9e307, 9e307))
    narrow = _Cfg("boundary_8e307", view=(-8e307, 8e307))
    ok_w, why_w = renders(wide, False, False, [0.0])
    ok_n, _ = renders(narrow, False, False, [0.0])
    assert (not ok_w) and ok_n, (
        "the domain boundary is not where it was measured: (-9e307, 9e307) with "
        "ticks [0.0] and both switches off gave in_domain=%s and "
        "(-8e307, 8e307) gave in_domain=%s" % (ok_w, ok_n))
    boundary = (why_w, render_ticks(narrow, False, False, [0.0]))

    # (3) switch dependence at one and the same installation and tick list.
    sw = None
    for cfg in EXTREME_CFGS:
        for ticks in EXTREME_TICKS:
            if not ticks:
                continue
            if (not renders(cfg, False, False, ticks)[0]
                    and renders(cfg, False, True, ticks)[0]):
                sw = (cfg.name, list(ticks),
                      render_ticks(cfg, False, True, ticks))
                break
        if sw:
            break
    assert sw, (
        "the domain never depended on the switches on this grid, so `renders` "
        "taking them would be unmotivated and a guard stated at one setting could "
        "be silently reused at another")

    # (4) the two domains are genuinely different sets.
    wider = None
    for cfg in EXTREME_CFGS:
        for ticks in ([1.0, 100.0, 10000.0], [1e300], [1.0]):
            if (not renders(cfg, False, False, ticks)[0]
                    and renders_log(cfg, ticks)[0]):
                wider = (cfg.name, list(ticks), render_log(cfg, ticks))
                break
        if wider:
            break
    assert wider, (
        "the log renderer's domain never exceeded the numeric renderer's on this "
        "grid, so modelling them as two predicates would be unmotivated")
    return n_out, boundary, sw, wider


def check_domain_covers_the_ordinary_region():
    """The guard costs the specification nothing where the instance lives: the
    ORDINARY region — every renderer configuration the site can install, crossed
    with every tick list it really produces (the F2P and P2P levels among them),
    at all four switch settings — lies entirely INSIDE the domain, with no
    exclusions at all. Asserted rather than counted, so a future matplotlib that
    narrowed the domain into this region would fail G-AX here."""
    n = 0
    for cfg in CFGS:
        for ticks in BOUNDARY_TICKS:
            for om in (False, True):
                for sm in (False, True):
                    ok, why = renders(cfg, om, sm, ticks)
                    assert ok, (
                        "the domain excludes an ORDINARY input: cfg=%s ticks=%r "
                        "om=%s sm=%s -> %s" % (cfg.name, ticks, om, sm, why))
                    n += 1
    for cfg in LOG_CFGS:
        for ticks in LOG_TICKS:
            ok, why = renders_log(cfg, ticks)
            assert ok, (
                "the log domain excludes an ORDINARY input: cfg=%s ticks=%r -> %s"
                % (cfg.name, ticks, why))
            n += 1
    return n


def check_domain_covers_the_sites():
    """The load-bearing direction, and the one that decides whether a modeled
    domain is honest: the guard must not exclude anything the modeled sites can
    actually hand these renderers.

    Both sites are driven over their own grids; for every (installation, tick
    list) either site produces, the corresponding domain must HOLD. If any real
    site input fell outside it, the specification would be silent about a
    reachable call and the guard would be an escape hatch rather than a scope
    statement.

    Then the converse, which is what makes the excluded region harmless: where the
    domain fails, the site produces NO legend — the refusal propagates out of the
    modeled region instead of yielding labels a clause could be wrong about. That
    is measured at both sites, on the very configuration the boundary pair pins.

    Returns (n_site_inputs, n_escapes, escape_examples)."""
    from seaborn.utils import locator_to_legend_entries
    n = 0
    # site B: the classic interface's own entry point, linear and log arms.
    for lo, hi in _limit_grid()[::3]:
        for loc in (mticker.MaxNLocator(nbins=3), mticker.LogLocator(numticks=6)):
            is_log = isinstance(loc, mticker.LogLocator)
            try:
                ticks, _labels = locator_to_legend_entries(loc, (lo, hi), float)
            except Exception as exc:                            # noqa: BLE001
                raise AssertionError(
                    "the site itself refused inside the ordinary grid, which the "
                    "domain claim does not cover: limits=(%r, %r) locator=%s -> "
                    "%s: %s" % (lo, hi, type(loc).__name__,
                                type(exc).__name__, exc)) from None
            if not len(ticks):
                continue
            cfg = _Cfg("site(%g,%g)" % (lo, hi), view=(lo, hi))
            ticks = [float(t) for t in ticks]
            if is_log:
                ok, why = renders_log(cfg, ticks)
                assert ok, (
                    "the modeled domain excludes a REAL site input: the log arm "
                    "at limits (%r, %r) produced ticks %r, which `rendersLog` "
                    "does not cover (%s)" % (lo, hi, ticks, why))
            else:
                ok, why = renders(cfg, False, False, ticks)
                assert ok, (
                    "the modeled domain excludes a REAL site input: the linear "
                    "arm at limits (%r, %r) produced ticks %r, which `renders _ "
                    "false false` does not cover (%s)" % (lo, hi, ticks, why))
            n += 1
    assert n > 0

    # ... and where the domain fails, no legend is produced at either site.
    escapes = []
    for lim in ((-_MAXF, _MAXF), (-9e307, 9e307), (-1e308, 1e308)):
        cfg = _Cfg("escape%r" % (lim,), view=lim)
        assert not renders(cfg, False, False, [0.0])[0]
        try:
            locator_to_legend_entries(mticker.FixedLocator([0.0]), lim, float)
        except Exception as exc:                                # noqa: BLE001
            escapes.append(("site_B", lim, "%s: %s" % (type(exc).__name__, exc)))
        else:
            raise AssertionError(
                "site B produced a legend at limits %r where the modeled domain "
                "says the renderer yields nothing, so the excluded region is NOT "
                "outside the modeled region and the restriction is unsound" % (lim,))
    try:
        import pandas as pd
        from seaborn._core.properties import PointSize
        from seaborn._core.scales import Continuous
    except Exception:                                           # noqa: BLE001
        pass
    else:
        s = pd.Series([0.0, 1e150, _MAXF], name="s")
        try:
            Continuous(norm=(-_MAXF, _MAXF)).tick(at=[0.0])._setup(s, PointSize())
        except Exception as exc:                                # noqa: BLE001
            escapes.append(("site_A", (-_MAXF, _MAXF),
                            "%s: %s" % (type(exc).__name__, exc)))
        else:
            raise AssertionError(
                "site A produced a legend at norm (-max, max) where the modeled "
                "domain says the renderer yields nothing, so the excluded region "
                "is not outside the modeled region")
    return n, len(escapes), escapes


# --- the modeled site's own renderers, driven through the site itself ---------

# A grid of DATA limits — the interval the modeled site installs on its renderer.
# `hi/lo` spans several decades because the log renderer's abbreviation threshold
# is a span, so a grid confined to one decade could not see it.
def _limit_grid():
    out = []
    for lo_e in range(-4, 5):
        for hi_e in range(lo_e, lo_e + 9):
            for f1 in (1.0, 1.5, 3.0, 7.0):
                for f2 in (1.0, 1.5, 3.0, 7.0):
                    lo, hi = f1 * 10.0 ** lo_e, f2 * 10.0 ** hi_e
                    if hi > lo:
                        out.append((lo, hi))
    return out


def _site_sequence(fmt, locs):
    """The modeled site's own way of driving a renderer: `set_locs(locs)` then one
    call per tick. `Formatter.format_ticks` IS this sequence, which is why the
    axioms may be stated in terms of either."""
    fmt.set_locs(locs)
    return [fmt(x) for x in locs]


def check_log_site_faithful():
    """Obligation (i): `renderLog(cfg, ticks)` IS the modeled site's log-path
    function. Drive the site's own entry point over the limit grid and compare its
    labels with the axiom's model at the installation the site used; then measure
    where a ticks-only model would disagree, so the handle argument is justified
    by a divergence rather than by caution.

    Returns (n_compared, n_ticks_only_bad, n_distinct_tick_lists, n_ambiguous)."""
    from seaborn.utils import locator_to_legend_entries
    n = bad_only = 0
    seen = {}
    for lo, hi in _limit_grid():
        ticks, labels = locator_to_legend_entries(
            mticker.LogLocator(numticks=6), (lo, hi), float)
        if not ticks:
            continue
        n += 1
        cfg = _Cfg("site_log(%g,%g)" % (lo, hi), view=(lo, hi))
        model = render_log(cfg, ticks)
        assert model == list(labels), (
            "renderLog unfaithful to the modeled site: data limits (%r, %r) with "
            "ticks %r print %r at the site but %r in the model"
            % (lo, hi, list(ticks), list(labels), model))
        if render_log_ticks_only(ticks) != list(labels):
            bad_only += 1
        seen.setdefault(tuple(ticks), set()).add(tuple(labels))
    ambiguous = sum(1 for v in seen.values() if len(v) > 1)
    assert bad_only > 0 and ambiguous > 0, (
        "a ticks-only model of the log renderer disagreed with the site nowhere "
        "on this grid (%d comparisons), so the handle argument would be "
        "unmotivated" % n)
    return n, bad_only, len(seen), ambiguous


def check_linear_site_faithful():
    """The same two-step chain on the site's OTHER arm, which is the one the
    modeled change configures:

      step 1 — the replica IS the site: built the way the site builds its numeric
               renderer (a fresh `ScalarFormatter` on an axis whose view interval
               is the data limits) and driven the way the site drives it, it
               reproduces the site's own labels for every install on the grid,
               with the two switches left exactly as they arrive; and
      step 2 — the axiom IS the replica with the switches set: `renderTicks(cfg,
               om, sm, ticks)` equals the replica driven through the site's
               sequence after setting them, for all four settings. This is what
               lets the axioms be stated over `format_ticks` while the site uses
               `set_locs` + one call per tick.

    Returns (n_compared, n_settings_compared)."""
    from seaborn.utils import locator_to_legend_entries
    n = m = 0
    for lo, hi in _limit_grid()[::7]:
        ticks, labels = locator_to_legend_entries(
            mticker.MaxNLocator(nbins=3), (lo, hi), float)
        if not ticks:
            continue
        n += 1
        cfg = _Cfg("site_lin(%g,%g)" % (lo, hi), view=(lo, hi))
        # step 1: switches untouched, exactly as the arm reaches the renderer.
        replica = _site_sequence(cfg.build(ticks), [float(t) for t in ticks])
        assert replica == list(labels), (
            "the site replica is not the site: data limits (%r, %r) ticks %r "
            "print %r at the site but %r in the replica"
            % (lo, hi, list(ticks), list(labels), replica))
        # step 2: the axiom equals that same sequence once the switches are set.
        for om in (False, True):
            for sm in (False, True):
                f = cfg.build(ticks)
                f.set_useOffset(om)
                f.set_scientific(sm)
                seq = _site_sequence(f, [float(t) for t in ticks])
                assert render_ticks(cfg, om, sm, ticks)[0] == seq, (
                    "renderTicks does not equal the site's own call sequence: "
                    "cfg=%s om=%s sm=%s ticks=%r -> %r vs %r"
                    % (cfg.name, om, sm, list(ticks),
                       render_ticks(cfg, om, sm, ticks)[0], seq))
                m += 1
    assert n > 0 and m > 0
    return n, m


def check_hoists_witness():
    """sharedTerm_hoists: the switches really do hoist a shared term out, on the
    instance's own data — AND the witness lies in the domain with both switches
    on, which is the other half of the axiom's conjunction now that it is stated
    as `renders cfg true true ticks ∧ sharedTerm cfg true true ticks ≠ ""`. Only
    the both-on setting can witness it, so the count is taken there.

    Returns (witnesses, n_hoisting_at_other_settings)."""
    wit, other = [], 0
    for cfg in CFGS:
        for ticks in (BOUNDARY_TICKS[3], BOUNDARY_TICKS[4]):
            for om, sm in ((True, True), (True, False), (False, True)):
                if not renders(cfg, om, sm, ticks)[0]:
                    continue
                labels, off = render_ticks(cfg, om, sm, ticks)
                if off == "":
                    continue
                if om and sm:
                    wit.append((cfg.name, om, sm, off, labels[0]))
                else:
                    other += 1
    assert wit, (
        "sharedTerm_hoists unwitnessed: no configuration that is in the domain "
        "with both switches on reported a shared term separately, so the "
        "sharedTerm = \"\" clause would be idle")
    return wit, other


# --- the other renderers the modeled site can meet ---------------------------

def _alt_renderers():
    """(name, ticks, factory) for every renderer OTHER than a `ScalarFormatter`
    that the modeled site can find already installed (mapping.md §1.1: the
    returns of `Continuous._get_formatter` and `Temporal._get_formatter`, plus a
    caller-supplied one via `label(formatter=)`).

    Each factory builds a FRESH instance so the same starting state can be
    rendered twice: once untouched (that is `ownLabels`) and once through the
    site's own guarded sequence (that is `labels`)."""
    levels = [1e8 + 2.5 * k for k in range(4)]       # the instance's data levels
    logs = [10.0 ** (2 * k) for k in range(1, 5)]    # log-spaced levels
    days = [1.0, 32.0, 60.0, 91.0]                   # days since mpl's epoch
    yield ("LogFormatter", logs, lambda: mticker.LogFormatter())
    # Continuous(trans="log") / Continuous().tick(...) with a base:
    yield ("LogFormatterSciNotation", logs,
           lambda: mticker.LogFormatterSciNotation(base=10))
    # Continuous().label(unit="g"):
    yield ("EngFormatter", levels, lambda: mticker.EngFormatter(unit="g", sep=" "))
    # Continuous().label(like="{x:.2f}") / like=callable:
    yield ("StrMethodFormatter", levels,
           lambda: mticker.StrMethodFormatter("{x:.2f}"))
    yield ("FuncFormatter", levels,
           lambda: mticker.FuncFormatter(lambda x, p: "L%d" % (p or 0)))
    # Continuous().label(formatter=<any matplotlib Formatter the caller likes>):
    yield ("PercentFormatter", levels, lambda: mticker.PercentFormatter())
    yield ("FixedFormatter", levels,
           lambda: mticker.FixedFormatter(["a", "b", "c", "d"]))
    # Temporal(): the same _setup, a date renderer.
    yield ("ConciseDateFormatter", days,
           lambda: mdates.ConciseDateFormatter(mdates.AutoDateLocator()))
    yield ("AutoDateFormatter", days,
           lambda: mdates.AutoDateFormatter(mdates.AutoDateLocator()))


def _attach(fmt, locs):
    fmt.axis = _DummyAxis(*((min(locs), max(locs)) if locs else (0.0, 1.0)))
    return fmt


def check_alt_renderers():
    """Facts (a)-(e): the `modesAvailable` / `ownLabels` modelling of the site is
    faithful to what the other renderers really do."""
    n_alt = 0
    for name, ticks, factory in _alt_renderers():
        n_alt += 1
        locs = [float(t) for t in ticks]
        # `ownLabels`: what the installed renderer prints on its own.
        own_fmt = _attach(factory(), locs)
        own = list(own_fmt.format_ticks(locs))
        # the site's own sequence, with its two questions asked separately
        # exactly as the site asks them.
        fmt = _attach(factory(), locs)
        has_off = hasattr(fmt, "set_useOffset")
        has_sca = hasattr(fmt, "set_scientific")
        if has_off:
            fmt.set_useOffset(False)
        if has_sca:
            fmt.set_scientific(False)
        labels = list(fmt.format_ticks(locs))
        # (a) the site's two questions always answer together.
        assert has_off == has_sca, (
            "modesAvailable unfaithful: %s answers set_useOffset=%s but "
            "set_scientific=%s, so one Bool cannot model both guards"
            % (name, has_off, has_sca))
        # (b) modesAvailable == False is a real case, not an empty one.
        assert not has_off, (
            "%s unexpectedly exposes the shared-term mode setters; the "
            "modesAvailable == False case would not cover it" % name)
        # (c) one label per tick — the `require ownLabels.length = ticks.length`
        #     modelling precondition.
        assert len(own) == len(ticks), (
            "ownLabels length precondition unsound: %s printed %d labels for "
            "%d ticks" % (name, len(own), len(ticks)))
        assert len(labels) == len(ticks)
        # (d) the site is INERT here: neither setter ran, so the labels are
        #     exactly the renderer's own (`labels = ownLabels`).
        assert labels == own, (
            "labels = ownLabels unsound: %s printed %r through the site but %r "
            "on its own" % (name, labels, own))
        # (e) and on THIS tick list none of them hoists anything out, so the
        #     labels checked in (d) each stand on their own.
        #
        #     Scoped to the tick list on purpose: "these renderers never hoist
        #     anything" would be FALSE, and it is not what the arm claims.
        #     Measured at base_commit (mpl 3.7.2), `ConciseDateFormatter`
        #     reports a term separately as soon as the span narrows — '1973-Jan'
        #     over four years, '1970-Jan' over a month, '1970-Jan-02' over a day
        #     or an hour — and only this quarter-span fixture leaves it empty.
        #     What the `modesAvailable = false` arm actually asserts is (d),
        #     `labels = ownLabels`; it says NOTHING about a separately reported
        #     term, because the site cannot influence one there. That is checked
        #     across all five spans in `check_date_spans` below, and it holds on
        #     every one, including the four where the term is non-empty.
        assert own_fmt.get_offset() == "", (
            "%s reported %r separately for %r, so the labels checked above do "
            "not each stand on their own" % (name, own_fmt.get_offset(), ticks))
    return n_alt


def check_date_spans():
    """Fact (f): the `modesAvailable = false` arm is INERT for a date renderer at
    every span, not just at the one `_alt_renderers` happens to pass.

    A date renderer is the one non-`ScalarFormatter` renderer whose separately
    reported term depends on the ticks, so it is the one that could make the
    arm's obligation span-dependent. It does not: neither guard question answers
    yes at any span, so the site runs neither setter, and the labels come back
    exactly as the renderer printed them on its own. Returns (n, n_hoisting) so
    the record can show that the non-empty case really was exercised."""
    spans = {
        "quarter": [1.0, 32.0, 60.0, 91.0],
        "year": [1.0, 366.0, 731.0, 1096.0],
        "month": [1.0, 8.0, 15.0, 22.0],
        "day": [1.0, 1.25, 1.5, 1.75],
        "hour": [1.0, 1.0 + 1 / 96, 1.0 + 2 / 96, 1.0 + 3 / 96],
    }
    factories = (
        ("ConciseDateFormatter",
         lambda: mdates.ConciseDateFormatter(mdates.AutoDateLocator())),
        ("AutoDateFormatter",
         lambda: mdates.AutoDateFormatter(mdates.AutoDateLocator())),
    )
    n, n_hoisting = 0, 0
    for span, locs in spans.items():
        for name, factory in factories:
            n += 1
            own_fmt = _attach(factory(), locs)
            own = list(own_fmt.format_ticks(locs))
            fmt = _attach(factory(), locs)
            has_off = hasattr(fmt, "set_useOffset")
            has_sca = hasattr(fmt, "set_scientific")
            if has_off:
                fmt.set_useOffset(False)
            if has_sca:
                fmt.set_scientific(False)
            labels = list(fmt.format_ticks(locs))
            assert has_off == has_sca, (
                "modesAvailable unfaithful: %s at a %s span answers "
                "set_useOffset=%s but set_scientific=%s"
                % (name, span, has_off, has_sca))
            assert not has_off, (
                "%s at a %s span exposes the shared-term mode setters"
                % (name, span))
            assert len(own) == len(locs), (
                "ownLabels length precondition unsound: %s printed %d labels "
                "for %d ticks at a %s span" % (name, len(own), len(locs), span))
            assert labels == own, (
                "labels = ownLabels unsound: %s at a %s span printed %r through "
                "the site but %r on its own" % (name, span, labels, own))
            if own_fmt.get_offset() != "":
                n_hoisting += 1
    assert n_hoisting > 0, (
        "no date span reported a term separately, so fact (f) never exercised "
        "the case it exists for")
    return n, n_hoisting


def check_formatter_partition():
    """Facts (a)/(b) EXHAUSTIVELY rather than over a hand-picked list: enumerate
    every `Formatter` subclass matplotlib exposes in the two modules a seaborn
    scale draws its renderers from, and check the two guard questions partition
    them cleanly.

    `hasattr` on a bound method is decided by the class, so this needs no
    instantiation and cannot miss a subclass that happens to be awkward to
    construct — it closes the gap between "these nine behave so" and the
    modelling claim "one Bool is faithful for every renderer that can arrive".
    """
    import inspect
    both, neither = [], []
    for mod in (mticker, mdates):
        for name, obj in sorted(vars(mod).items()):
            if not (inspect.isclass(obj) and issubclass(obj, mticker.Formatter)):
                continue
            if obj is mticker.Formatter:
                continue
            has_off = hasattr(obj, "set_useOffset")
            has_sca = hasattr(obj, "set_scientific")
            # (a) the site's two questions never disagree — for ANY subclass.
            assert has_off == has_sca, (
                "modesAvailable unfaithful: %s.%s answers set_useOffset=%s but "
                "set_scientific=%s, so one Bool cannot model the two guards"
                % (mod.__name__, name, has_off, has_sca))
            (both if has_off else neither).append(name)
    # (b) exactly one kind answers YES, and it is the renderer the modeled
    #     branch is about; everything else lands on the `labels = ownLabels` arm.
    assert both == ["ScalarFormatter"], (
        "expected ScalarFormatter to be the only Formatter carrying the two "
        "shared-term mode setters, found %r" % (both,))
    # A near-miss worth pinning by measurement rather than by name: EngFormatter
    # reads like a numeric formatter, and in some matplotlib releases it derives
    # from ScalarFormatter — where it would inherit both setters and land on the
    # OTHER arm. Under the version this instance pins it derives from Formatter
    # directly and answers no to both questions, which is why the partition above
    # holds. Stated so the claim is read as version-specific and re-measured here.
    assert mticker.ScalarFormatter not in mticker.EngFormatter.__mro__ \
        and not hasattr(mticker.EngFormatter, "set_useOffset"), (
        "EngFormatter derives from ScalarFormatter in matplotlib %s (mro %r), so "
        "it carries the two setters and the partition claim must be restated"
        % (mpl.__version__, [c.__name__ for c in mticker.EngFormatter.__mro__]))
    assert len(neither) >= 10, (
        "expected the modesAvailable == False arm to cover many renderers, "
        "found only %r" % (neither,))
    return len(both) + len(neither), len(neither)


# --- the link to the instance's own assertion (facts (f), (g)) ---------------

def check_assertion_link():
    """Fact (f): where the tests look, `sharedTerm == ""` is exactly what makes
    a label stand for its own tick; and fact (g): where labels are typeset, no
    read-back obligation could be stated at all, which is why the specification
    states the shared-term clause instead.

    Returns (n_plain_cfgs, n_typeset_cfgs, n_hoisting_misreads)."""
    plain, typeset, misreads = 0, 0, 0
    for cfg in CFGS:
        for ticks in (BOUNDARY_TICKS[3], BOUNDARY_TICKS[4], BOUNDARY_TICKS[5]):
            labels, off = render_ticks(cfg, False, False, ticks)
            assert off == ""
            vals = [_reads_back(lab) for lab in labels]
            if all(v is not None for v in vals):
                # (f) nothing hoisted => every label stands for its own tick, to
                #     the precision the renderer prints, and in particular the
                #     ~1e8 positions the assertion checks stay above 1e7.
                for t, v in zip(ticks, vals):
                    assert abs(v - t) <= 1e-9 * max(1.0, abs(t)), (
                        "fact (f) failed: cfg=%s tick=%r read back as %r"
                        % (cfg.name, t, v))
                    if t > 1e7:
                        assert v > 1e7, (
                            "fact (f) failed: cfg=%s tick=%r read back as %r, "
                            "which the assertion would reject"
                            % (cfg.name, t, v))
                plain += 1
            else:
                # (g) typeset labels: no numeric reading exists, yet nothing is
                #     hoisted. A read-back clause would be UNSOUND here.
                typeset += 1
            # every hoisting setting misreads or fails to read, on this data
            for om, sm in ((True, True), (True, False), (False, True)):
                hl, ho = render_ticks(cfg, om, sm, ticks)
                if ho == "":
                    continue          # that setting was inert for this data
                hv = [_reads_back(lab) for lab in hl]
                assert any(v is None or abs(v - t) > 1e-9 * max(1.0, abs(t))
                           for t, v in zip(ticks, hv)), (
                    "non-vacuity failed: cfg=%s om=%s sm=%s reported %r "
                    "separately yet every label still stood for its own tick"
                    % (cfg.name, om, sm, ho))
                misreads += 1
    assert typeset > 0, (
        "fact (g) unwitnessed: no configuration produced labels that a numeric "
        "reading cannot parse, so the choice not to state a read-back clause "
        "would be unmotivated")
    assert plain > 0 and misreads > 0
    return plain, typeset, misreads


def main():
    rng = random.Random(3187)
    num_tally = {"in": 0, "out": 0}
    log_tally = {"in": 0, "out": 0}

    # --- exhaustive: every configuration x every boundary tick list ---------
    for cfg in CFGS:
        for ticks in BOUNDARY_TICKS:
            check_length_and_none(cfg, ticks, num_tally)
            check_handle_is_a_function(cfg, ticks)
    for cfg in LOG_CFGS:
        for ticks in LOG_TICKS:
            check_log_length(cfg, ticks, log_tally)
            check_log_handle_is_a_function(cfg, ticks)

    # --- and the same, ON BOTH SIDES OF THE DOMAIN BOUNDARY -----------------
    # The grid above stops at ordinary magnitudes, which is exactly how an
    # unguarded totality claim survives measurement. This one reaches the end of
    # the double range and includes non-finite positions, so every guarded fact is
    # exercised where it is guarded and where it is not.
    for cfg in EXTREME_CFGS + CFGS:
        for ticks in EXTREME_TICKS + NONFINITE_TICKS:
            check_length_and_none(cfg, ticks, num_tally)
            check_handle_is_a_function(cfg, ticks)
    for cfg in EXTREME_CFGS + LOG_CFGS:
        for ticks in EXTREME_TICKS + NONFINITE_TICKS + LOG_TICKS:
            check_log_length(cfg, ticks, log_tally)
            check_log_handle_is_a_function(cfg, ticks)

    # --- randomized fuzz over FLOAT tick lists ------------------------------
    # The carrier is `List Float`: the positions really are IEEE-754 doubles and
    # really are not whole numbers in general (the instance's own levels are
    # half-integral), so the fuzz draws non-integral ticks on purpose.
    n_fuzz = 6000
    for _ in range(n_fuzz):
        cfg = rng.choice(CFGS)
        n = rng.randint(0, 8)
        base = rng.choice([0.0, 1.0, 1e3, 1e6, 1e8, 1e9, 1e12, -1e8, -1.0])
        step = rng.choice([1.0, 2.5, 0.5, 0.02, 1e-6, 1e3, 1e6,
                           rng.uniform(-1e3, 1e3)])
        ticks = [base + step * k for k in range(n)]
        if rng.random() < 0.3:
            ticks = [rng.uniform(-1e9, 1e9) for _ in range(n)]
        check_length_and_none(cfg, ticks, num_tally)
        check_log_length(rng.choice(LOG_CFGS),
                         [abs(t) + 1.0 for t in ticks], log_tally)

    # --- randomized fuzz ACROSS the boundary, on both renderers -------------
    # Drawn so that a good share of the draws land outside the domain: the point
    # is that every draw that lands INSIDE it satisfies the guarded facts, and
    # every draw that lands outside is a call the model does not describe.
    n_fuzz_x = 3000
    for _ in range(n_fuzz_x):
        span_e = rng.uniform(295.0, 308.26)
        half = min(10.0 ** span_e, _MAXF)
        view = rng.choice([(-half, half), (0.0, half), (half / 7.0, half),
                           (-half, half / 3.0)])
        cfg = _Cfg("fuzz_x", rc=rng.choice(
            [{}, {"axes.formatter.use_mathtext": True},
             {"axes.formatter.limits": (-1, 1)}]), view=view)
        n = rng.randint(0, 3)
        mag = rng.choice([0.0, 1.0, 1e150, 1e300, 1e307, _MAXF, _INF, _NAN])
        ticks = [rng.choice([1.0, -1.0]) * mag for _ in range(n)]
        check_length_and_none(cfg, ticks, num_tally)
        check_log_length(cfg, ticks, log_tally)

    # --- the log renderer's handle: not idle, and faithful to the site -------
    log_wit = check_log_handle_matters()
    n_log_site, n_log_only_bad, n_log_lists, n_log_ambig = check_log_site_faithful()
    n_lin_site, n_lin_settings = check_linear_site_faithful()

    # --- the modeled DOMAIN: inhabited, not idle, and covering the sites -----
    dom_wit = check_domain_nonvacuous()
    n_out, boundary, sw_wit, log_wider = check_domain_not_idle()
    n_ordinary = check_domain_covers_the_ordinary_region()
    n_site_in, n_escapes, escapes = check_domain_covers_the_sites()

    # --- non-vacuity + the other renderers + the assertion link -------------
    wit, n_hoist_other = check_hoists_witness()
    n_alt = check_alt_renderers()
    n_span, n_span_hoisting = check_date_spans()
    n_cls, n_cls_neither = check_formatter_partition()
    n_plain, n_typeset, n_misreads = check_assertion_link()

    domain_msg = ("G-AX DOMAIN: the two renderers are PARTIAL and the model says so. "
          "`renders` held on %d of the %d (cfg, switches, ticks) observations "
          "checked and failed on %d; `rendersLog` held on %d of %d and failed on "
          "%d. Every guarded fact was asserted on every in-domain observation (0 "
          "violations) and every refusal was reproduced on a second call, so the "
          "domain is a function of the arguments. It is INHABITED: cfg=%s with "
          "ticks %r renders %r numerically and %r logarithmically "
          "(renders_nonvacuous). It is NOT IDLE: %d observations lie outside it, "
          "the boundary is a pair differing only in the interval span -- "
          "(-9e307, 9e307) with ticks [0.0] and both switches off yields nothing "
          "(%s) while (-8e307, 8e307) yields %r -- it depends on the SWITCHES "
          "(cfg=%s ticks=%r yields nothing with both off and %r with the "
          "multiplicative one on), and the two renderers' domains differ (cfg=%s "
          "ticks=%r: the log renderer yields %r where the numeric one with both "
          "switches off yields nothing). And it does not duck any reachable input: "
          "all %d ordinary (configuration, tick list, switch setting) observations "
          "-- every install the site can make crossed with every tick list it "
          "really produces, the instance's own F2P/P2P levels among them -- lie "
          "inside it with NO exclusions, all %d (installation, tick list) pairs the "
          "two modeled sites produced on their own grids lie inside it too, and in "
          "the excluded region the sites produce no legend at all rather than a "
          "misleading one (%d escapes measured, e.g. %s). "
          % (num_tally["in"], num_tally["in"] + num_tally["out"],
             num_tally["out"], log_tally["in"],
             log_tally["in"] + log_tally["out"], log_tally["out"],
             dom_wit[0], dom_wit[1], dom_wit[2], dom_wit[3], n_out,
             boundary[0], boundary[1], sw_wit[0], sw_wit[1], sw_wit[2],
             log_wider[0], log_wider[1], log_wider[2],
             n_ordinary, n_site_in, n_escapes,
             escapes[0] if escapes else "none"))

    ok_msg = ("G-AX OK (matplotlib %s): renderTicks_length + sharedTerm_none hold "
          "over %d renderer configurations x %d boundary tick lists x 4 switch "
          "settings and %d fuzzed float tick lists (0 violations), and each "
          "configuration rebuilds to byte-identical labels, so RendererConfig is "
          "a faithful handle; renderLog_length holds on %d log installations x %d "
          "log tick lists, renderLog reproduces the modeled site's own log-path "
          "labels byte-for-byte on %d (interval, tick list) pairs the site itself "
          "produced (0 disagreements) where a ticks-only model of it disagrees on "
          "%d of them and %d of the %d distinct tick lists print more than one "
          "label list (so the handle argument is load-bearing, witnessed %d times "
          "directly, e.g. ticks=%r prints %r on %s and %r on %s), and the site's "
          "numeric arm is reproduced too: the replica equals the site on %d "
          "installs and renderTicks equals the site's own set_locs-then-call "
          "sequence on %d configuration/switch combinations; "
          "sharedTerm_hoists witnessed %d times inside the domain with both "
          "switches on -- the axiom's conjunction, both halves (e.g. cfg=%s om=%s "
          "sm=%s reports %r separately and prints %r), plus %d further hoisting "
          "observations at one-switch settings -- so the clause is not idle; "
          "of all %d Formatter subclasses in matplotlib.ticker + matplotlib.dates "
          "the two mode questions never disagree and exactly one "
          "(ScalarFormatter) answers yes, so %d land on the "
          "modesAvailable = false arm, and the %d instantiated ones each print "
          "one label per tick, hoist nothing for the tick lists they are driven "
          "with, and are left byte-identical by the site (labels = ownLabels) -- "
          "which is that arm's whole obligation and is span-independent: the two "
          "date renderers were driven at %d (span, renderer) settings from an "
          "hour to four years, neither guard question ever answers yes, and "
          "labels = ownLabels held on every one INCLUDING the %d where the "
          "renderer does report a term separately (the arm claims nothing about "
          "that term, because the site cannot influence it there); where the "
          "tests look, both-off labels stand "
          "for their own ticks (%d cfg/tick combinations) while every hoisting "
          "setting misreads (%d), and %d combinations print typeset labels that "
          "no numeric reading parses at all -- which is why the specification "
          "constrains the separately-reported term rather than the label text."
          % (mpl.__version__, len(CFGS), len(BOUNDARY_TICKS), n_fuzz,
             len(LOG_CFGS), len(LOG_TICKS),
             n_log_site, n_log_only_bad, n_log_ambig, n_log_lists,
             len(log_wit), log_wit[0][0], log_wit[0][2], log_wit[0][1],
             log_wit[0][4], log_wit[0][3], n_lin_site, n_lin_settings,
             len(wit), wit[0][0], wit[0][1], wit[0][2],
             wit[0][3], wit[0][4], n_hoist_other, n_cls, n_cls_neither, n_alt,
             n_span, n_span_hoisting,
             n_plain, n_misreads, n_typeset))
    # One final line, because the gate records the LAST line of stdout: the
    # domain evidence is the load-bearing part of this check and has to be in
    # the record, not only in the log.
    print(ok_msg + " " + domain_msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
