#!/usr/bin/env python3
"""G-CONF differential conformance for mwaskom__seaborn-3187 (nagini backend).

Runs INSIDE the instance image with the gold patch already applied by the gate
(apply_gold=True, PYTHONPATH=/testbed). stdlib + matplotlib/numpy/pandas (the
very libraries the modeled legend code uses); the fuzzer is stdlib `random`
with a pinned seed, so no hypothesis dependency.

WHAT IS BEING REFUTED
---------------------
model.py claims three things about the patched repo, for a list of tick
locations, an axis range, and a formatter that arrives already built:

  (i)   the legend's labels are EXACTLY the label sequence that formatter
        renders for that whole tick set on that axis range, in order
        (`ToSeq(Result()) == rendered_labels(convention, locs, residual,
        view_lo, view_hi)`);
  (ii)  the formatter is LEFT with residual rendering disabled
        (`not fmt.residual`), with its rendering convention unchanged
        (`fmt.convention == Old(fmt.convention)`) and with the axis range it
        was handed unchanged (`fmt.view_lo == Old(fmt.view_lo)`, same for
        `view_hi`);
  (iii) for the default (full-value) convention every label reads back to its
        tick's full value (`legend_reads_ticks(Result(), locs)`).

This script tries to break all three against the real code.  Labels are
compared as EXACT TEXT, never as parsed numbers: the legend stores the text, and
two different texts ('0.2' and '0.20') read back to the same number, so a
numeric comparison would not see a difference the repo's own tests do.

SHADOW - the pure + impl regions of model.py, copied VERBATIM
------------------------------------------------------------
`shadow_legend_values_continuous` / `shadow_legend_values_locator` are the code
between `# impl-start` and `# impl-end` of `legend_values_continuous` /
`legend_values_locator`, character-for-character, with only the contract calls
deleted (`Invariant`, `Assert` and the `# invariants-start/-end` markers).  No
renaming, no restructuring: the dead-looking `conv0 = fmt.convention` and
`old_seq = ToSeq(result)` bindings are kept because they are in the region.
`TickFormatter` and `legend_reads_ticks` are the pure region, copied the same
way, and `PSeq` / `ToSeq` are the usual immutable-sequence shim.

`rendered_labels` and `reading` are `@Pure @ContractOnly` - they have no body to
copy, so per the contract they CALL THE REAL CALLEES they axiomatize instead of
assuming the axioms:

  * `rendered_labels(convention, ticks, residual, view_lo, view_hi)` builds a
    real matplotlib formatter of the kind `convention` denotes, puts it in the
    residual-rendering state `residual` names, attaches it to an axis whose
    range is exactly `(view_lo, view_hi)`, and returns its label sequence for
    that whole tick set.  So the model's length axiom AND its reading axiom are
    EXERCISED here rather than assumed: if the real formatter rendered a
    different number of labels, or stopped reading back to the ticks with
    residual rendering disabled, the diff below would fire.
  * `reading(label)` parses the label text back to a number, normalising the
    Unicode minus and digit-grouping spaces - the number a reader recovers.

The model's `ticks`, `residual`, `view_lo` and `view_hi` arguments are the
model's OWN values, passed straight through; the driver supplies only which real
formatter kind the opaque `convention` code denotes and which of the two
rendering APIs the site under test uses.  Neither is model state, so the
abstraction is not inverted.

THE AXIS RANGE IS AN INPUT, DRAWN INDEPENDENTLY OF THE TICKS
------------------------------------------------------------
A formatter renders through the axis it is attached to, and on the rendering
path the only thing it reads from that axis is the range currently in view.  The
model therefore carries the range as state of the formatter, and the driver
DRAWS IT SEPARATELY from the tick set - a legend's ticks are chosen inside its
variable's range and are normally narrower than it, so a driver that reused the
tick set's own span would present the callee with only the collapsed diagonal
and would never notice a rendering that consulted the wrong range.  Every case
is run at the diagonal AND at ranges one, ten and a thousand tick-spans wider on
each side; the range always contains the tick set, because both sites clip their
ticks to it, and the driver hands the oracle the very same interval it gave the
model (`_setup` on a two-point series at the range's ends; `limits=` at site 2).
`wider_than_ticks_checks` in the JSON counts the cases whose range is strictly
wider than the ticks.

`rendered_labels` is memoised on its full argument tuple.  It is a pure
function, so this changes no result; a purity control on every boundary case
recomputes it with a fresh formatter and requires the same answer.

ORACLE - the REAL patched repo functions, CALLED, not transliterated
-------------------------------------------------------------------
Both modeled sites are driven live; neither needs a figure or a Plot:

  site 1  `legend_values_continuous`  <->  the legend branch of
          `ContinuousBase._setup`, seaborn/_core/scales.py:377-390 post-patch.
          Driven as `Continuous().tick(at=locs).label(formatter=f)._setup(
          pd.Series([min, max]), Color())` and read off `scale._legend` - a
          `FixedLocator` at exactly the requested ticks, with the view interval
          spanning them so the `(vmin <= locs) & (locs <= vmax)` clip keeps all
          of them.  Because the formatter is passed IN, the same object can be
          inspected afterwards: its residual-rendering state and its kind are
          checked against clause (ii).  Driven with FOUR formatter kinds, so
          the default convention and three others are all covered.

  site 2  `legend_values_locator`     <->  `seaborn.utils
          .locator_to_legend_entries`, seaborn/utils.py:687-712 post-patch.
          Called directly with `FixedLocator(locs)`, `limits=(min, max)`,
          `float`.  This site builds its own formatter, so only the default
          convention is reachable and the formatter object is not observable;
          clause (ii)'s state half is checked at site 1 only, and recorded as
          such.

TOTAL BEHAVIOUR, INCLUDING FAILURE
----------------------------------
Shadow and oracle are compared on their WHOLE outcome: either both return and
the label sequences must be identical, or both must fail with the same exception
type.  Nothing is skipped.  This matters because one of the four conventions
really does fail on part of the domain: matplotlib's SI-prefixed-unit formatter
takes the logarithm of the axis range's WIDTH, so on a range of no width it
raises `ValueError: math domain error` - measured identically at the real
site 1 and in the bridge.  Recording that agreement,
rather than dropping those inputs, keeps the non-default conventions' coverage
honest: `raise_agreements` in the JSON counts them.

TYPE BRIDGE (mapping.md, inverted)
----------------------------------
model carrier -> repo: `List[int]` tick locations become `[float(v) for v in
locs]` fed to a `FixedLocator` (both sites take their ticks from a locator);
`view_lo` / `view_hi` become the axis range the site is set up with; the model's
opaque `convention` code becomes a real formatter kind.
repo -> model carrier: each emitted label is its own opaque code - the EXACT
text, compared byte for byte - and the `list(locs)` half of each site's return
value is checked to be the identity on the input.  Domain: `|loc| <= 2**53`,
where int <-> IEEE double is exact, so the tick round-trip loses nothing.
Every generated input satisfies the model's `Requires` (`Acc(list_pred(locs),
1/2)` - any list of ints, including the empty one; `Acc(fmt.convention) and
Acc(fmt.residual)`, `Acc(fmt.view_lo) and Acc(fmt.view_hi)` - any formatter in
any state, on any range).

NON-VACUITY
-----------
The pre-state skeleton is exactly this impl with the residual-rendering mode
left as it arrived (model_prepatch.py / model_prepatch_2.py).  The driver
evaluates that variant too on large-magnitude cases and records that it
DISAGREES with the patched oracle (`discriminates_prepatch`); a run in which no
case separates the two is reported as a failure, because it would mean the input
domain never reached the behaviour the gold patch changed.  The F2P shape
(ticks ~1e8 apart by 1) is in the boundary matrix.

Exit 0 iff zero disagreements.  Pinned seed: 3187.  >= 1e5 Requires-satisfying
inputs: 30 boundary cases x 4 axis ranges + 100000 seeded fuzz draws each with
an independently drawn range, every one diffed against
site 2, the boundary cases and every 20th fuzz draw also diffed against site 1
under the default convention, and the boundary cases plus every 2000th draw
against site 1 under each of the three other conventions.  Any cap on the
negative-control evaluations is reported in the JSON, never silently applied.
"""
import json
import random
import sys

SEED = 3187
N_FUZZ = 100_000
SITE1_EVERY = 20          # every Nth fuzz draw also goes through site 1
SITE1_KINDS_EVERY = 2000  # ... and every Nth through the other conventions
MAX_EXACT = 2 ** 53       # int <-> float64 exactness bound (bridge domain)
MAX_CONTROL = 20_000      # cap on negative-control evaluations (reported)
MAX_REPORTED = 5

# The model's `convention` is an opaque int and only `== 0` is ever tested; 0 is
# the default (full-value) convention.  The driver keeps distinct codes for
# distinct real formatter kinds, so the model's "two conventions need not render
# alike" is exercised rather than collapsed.
CONVENTIONS = {
    0: "scalar",        # the formatter a numeric legend gets by default
    1: "eng",           # re-expresses ticks in an SI-prefixed unit
    2: "strmethod_3g",  # re-expresses ticks at a chosen precision
    3: "log",           # re-expresses ticks as powers
}
DEFAULT_CONVENTION = 0


# ---------------------------------------------------------------------------
# nagini carrier shim: PSeq is an immutable sequence, ToSeq materialises one.
# ---------------------------------------------------------------------------
class PSeq:
    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, items):
        s = cls()
        s._t = tuple(items)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __hash__(self):
        return hash(self._t)


def ToSeq(lst):
    return PSeq._wrap(lst)


# ---------------------------------------------------------------------------
# @ContractOnly callees: the REAL matplotlib formatter and the real parse.
# ---------------------------------------------------------------------------
# Site identity, not model state: which of the two rendering APIs the site under
# test uses.  ("format_ticks" = the whole tick set handed over at once;
# "set_locs" = the tick set announced, then each tick rendered.)
_VIA = "format_ticks"
_CACHE = {}


def _set_via(via):
    global _VIA
    _VIA = via


def real_formatter(convention):
    """A freshly built real formatter of the kind the model's opaque
    `convention` code denotes (mapping.md)."""
    import matplotlib as mpl
    kind = CONVENTIONS[convention]
    if kind == "scalar":
        return mpl.ticker.ScalarFormatter()
    if kind == "eng":
        return mpl.ticker.EngFormatter("g")
    if kind == "strmethod_3g":
        return mpl.ticker.StrMethodFormatter("{x:.3g}")
    if kind == "log":
        return mpl.ticker.LogFormatter()
    raise AssertionError("unknown convention %r" % (convention,))


def residual_state(fmt):
    """The model's `fmt.residual` read off a real formatter: True iff some
    control by which it could factor a magnitude common to the ticks out of
    them is still enabled.  A formatter with no such control can never factor
    anything out, so its residual state is False (refinement.md)."""
    on = False
    if hasattr(fmt, "get_useOffset"):
        on = on or bool(fmt.get_useOffset())
    if hasattr(fmt, "set_scientific"):
        on = on or bool(getattr(fmt, "_scientific", False))
    return on


def _apply_residual(fmt, residual):
    """Put a real formatter into the residual-rendering state the model's
    `residual` names."""
    for setter, val in (("set_useOffset", residual),
                        ("set_scientific", residual)):
        if hasattr(fmt, setter):
            getattr(fmt, setter)(val)


def _render(convention, ticks, residual, view_lo, view_hi, via):
    fmt = real_formatter(convention)
    # The axis range comes from the model's own state, NEVER from the tick set:
    # it is an independent input the real formatter reads, and the driver hands
    # the oracle the very same interval.
    span = (float(view_lo), float(view_hi))

    class _DummyAxis:
        def get_view_interval(self):
            return span

    _apply_residual(fmt, residual)
    fmt.axis = _DummyAxis()
    tick_list = [float(t) for t in ticks]
    if via == "format_ticks":
        return PSeq._wrap([str(s) for s in fmt.format_ticks(tick_list)])
    fmt.set_locs(tick_list)
    return PSeq._wrap([str(fmt(t)) for t in tick_list])


def rendered_labels(convention, ticks, residual, view_lo, view_hi):
    """@ContractOnly in model.py - no body to copy, so call the REAL callee it
    axiomatizes: the label sequence a real formatter of this convention, in this
    residual-rendering state, attached to an axis of this numeric range, renders
    for this whole tick set.  Memoised (a pure function of its arguments); the
    purity control recomputes it fresh."""
    key = (convention, tuple(ticks), residual, view_lo, view_hi, _VIA)
    hit = _CACHE.get(key)
    if hit is None:
        hit = _render(convention, list(ticks), residual, view_lo, view_hi, _VIA)
        _CACHE[key] = hit
    return hit


def reading(label):
    """@ContractOnly in model.py - the number a reader recovers from a label's
    text.  None when the text does not read back as a number at all."""
    t = (label.replace("−", "-")   # U+2212 MINUS SIGN -> ASCII
              .replace(" ", "")    # thin space
              .replace(" ", "")    # narrow no-break space
              .replace("\xa0", "")      # no-break space
              .replace(" ", "")
              .replace(",", "")
              .strip())
    try:
        return float(t)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# SHADOW: model.py's pure region + impl regions, verbatim, contracts stripped.
# ---------------------------------------------------------------------------
class TickFormatter:
    def __init__(self, convention, residual, view_lo, view_hi):
        self.convention = convention
        self.residual = residual
        self.view_lo = view_lo
        self.view_hi = view_hi


def legend_reads_ticks(labels, ticks):
    return len(labels) == len(ticks) and all(
        reading(labels[k]) == ticks[k] for k in range(len(ticks)))


def shadow_legend_values_continuous(fmt, locs):
    # impl-start (legend_values_continuous, verbatim; contracts stripped)
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        i = i + 1
    return result
    # impl-end


def shadow_legend_values_locator(fmt, locs):
    # impl-start (legend_values_locator, verbatim; contracts stripped)
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    fmt.residual = False
    result = []  # type: List[int]
    i = 0
    while i < len(locs):
        lab = rendered_labels(fmt.convention, ToSeq(locs), fmt.residual,
                              fmt.view_lo, fmt.view_hi)[i]
        old_seq = ToSeq(result)
        result.append(lab)
        i = i + 1
    return result
    # impl-end


# ---------------------------------------------------------------------------
# PRE-STATE shadow (model_prepatch{,_2}.py): same region, mode left as it
# arrived.  Negative control only - never compared for conformance.
# ---------------------------------------------------------------------------
def prepatch_shadow(fmt, locs):
    conv0 = fmt.convention
    lo0 = fmt.view_lo
    hi0 = fmt.view_hi
    result = []
    i = 0
    while i < len(locs):
        result.append(rendered_labels(fmt.convention, ToSeq(locs),
                                      fmt.residual, fmt.view_lo,
                                      fmt.view_hi)[i])
        i = i + 1
    return result


# ---------------------------------------------------------------------------
# ORACLE: the real patched repo functions.
# ---------------------------------------------------------------------------
def _import_repo():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib as mpl
    import pandas as pd
    from seaborn._core.scales import Continuous
    from seaborn._core.properties import Color
    from seaborn.utils import locator_to_legend_entries
    return mpl, pd, Continuous, Color, locator_to_legend_entries


def oracle_site1(mpl, pd, Continuous, Color, locs, convention, view):
    """REAL seaborn/_core/scales.py ContinuousBase._setup legend branch, driven
    with a caller-supplied formatter of the given convention and a data range of
    `view`.  The range is what the site announces to the axis the formatter
    reads (`axis.set_view_interval(vmin, vmax)`), and it is driven INDEPENDENTLY
    of the tick locations - which is how a legend actually arises, its ticks
    being chosen inside a wider data range.  Returns the tick locations, the
    label texts, and the formatter object afterwards."""
    at = [float(v) for v in locs]
    lo, hi = float(view[0]), float(view[1])
    data = pd.Series([lo, hi], name="c", dtype=float)
    fmt = real_formatter(convention)
    scale = (Continuous().tick(at=at).label(formatter=fmt)
             ._setup(data, Color()))
    out_locs, labels = scale._legend
    return list(out_locs), [str(s) for s in labels], fmt


def oracle_site2(mpl, locator_to_legend_entries, locs, view):
    """REAL seaborn/utils.py locator_to_legend_entries (builds its own default
    formatter, so the default convention only).  `limits` is this site's axis
    range - the interval its formatter reads - and is likewise driven
    independently of the tick locations."""
    at = [float(v) for v in locs]
    lo, hi = float(view[0]), float(view[1])
    locator = mpl.ticker.FixedLocator(at)
    raw_levels, formatted = locator_to_legend_entries(locator, (lo, hi), float)
    return list(raw_levels), [str(s) for s in formatted]


# ---------------------------------------------------------------------------
def boundary_cases():
    """Boundary + F2P shapes.  The impl region's only branch is the loop, so
    zero / one / many iterations are all covered, plus every magnitude regime
    where a formatter would factor a residual out."""
    f2p_plot = [100000000 + k for k in (1, 2, 3, 4)]
    return [
        [],                                    # loop body never runs
        [0],                                   # singleton, zero
        [1],
        [-1],
        [7],
        [-3],
        [0, 1],                                # two iterations, no residual
        [1, 1, 1],                             # duplicates
        [3, 1, 2],                             # unsorted
        f2p_plot,                              # the exact F2P tick shape
        [100000000, 100000500, 100001000],     # large + small span
        [100000000],                           # large singleton
        [-100000004, -100000003, -100000002],  # large negative
        [-5000000, 0, 5000000],                # spans zero
        [1000000000, 1000000001],
        [999999999, 1000000000, 1000000001],   # magnitude rollover
        [10 ** 12, 10 ** 12 + 1],
        [-(10 ** 12), 10 ** 12],
        [10 ** 15, 10 ** 15 + 1],
        [10 ** 15 + 1],
        [2 ** 53 - 2, 2 ** 53],                # exactness bound of the bridge
        [-(2 ** 53), 2 ** 53],
        [123456789, 123456790],
        [20000000 * k for k in range(6)],
        [10 ** 8 for _ in range(12)],          # long list, all identical large
        list(range(12)),                       # long list, small
        [100000000 + k for k in range(12)],    # long list, large + unit span
        [-1000000000000, -999999999999],
        [0, 100000000],                        # tiny + huge together
        [2 ** 52, 2 ** 52 + 1, 2 ** 52 + 2],
    ]


def fuzz_case(rng):
    """A Requires-satisfying List[int] inside the bridge's exact domain."""
    n = rng.randint(0, 12)
    mag = rng.choice([1, 10, 100, 10 ** 3, 10 ** 5, 10 ** 6, 10 ** 7,
                      10 ** 8, 10 ** 9, 10 ** 12, 10 ** 15, 2 ** 52])
    base = rng.randint(-mag, mag)
    if rng.random() < 0.2:
        step = 0
    else:
        step = rng.randint(1, max(1, mag // 4))
    locs = [base + k * step for k in range(n)]
    if rng.random() < 0.15:
        rng.shuffle(locs)
    return [v for v in locs if abs(v) <= MAX_EXACT]


def widen(locs, factor):
    """An axis range for this tick set, widened by `factor` times its span.

    The range is a SEPARATE input from the tick locations - a legend's ticks are
    chosen inside its variable's range, and that range is normally wider than
    them - so the driver must move it independently or it would never present
    the callee with the inputs the real sites do.  `factor == 0` is the diagonal
    a careless driver would use (range == tick span), which is exactly the
    collapse that makes a range-blind rendering model look sound.

    The range always CONTAINS the tick set, because both sites clip their ticks
    to it (`locs[(vmin <= locs) & (locs <= vmax)]`, scales.py; the `raw_levels`
    filter in utils.py), so a range excluding a tick could not be presented with
    that tick surviving.  Both bounds stay inside the bridge's exact int/float
    domain.
    """
    if not locs:
        return (0, 1)
    lo, hi = min(locs), max(locs)
    if factor == 0:
        return (lo, hi)
    width = max(hi - lo, 1)
    span = width * factor
    lo2, hi2 = lo - span, hi + span
    if abs(lo2) > MAX_EXACT or abs(hi2) > MAX_EXACT:
        return (lo, hi)
    return (lo2, hi2)


# Widening factors used for the boundary cases: the diagonal, then ranges 1x,
# 10x and 1000x the tick span wider on each side.
BOUNDARY_FACTORS = (0, 1, 10, 1000)


def outcome(thunk):
    """The WHOLE outcome of a call: the value, or the exception type it failed
    with.  Shadow and oracle are compared on this, so a failure on one side and
    a value on the other is a disagreement, and the same failure on both sides
    is an agreement."""
    try:
        return ("ok", thunk())
    except Exception as e:  # noqa: BLE001 - the outcome IS the observation
        return ("raise", type(e).__name__)


def _j(got):
    """A JSON-safe rendering of an outcome, for the disagreement report."""
    if got[0] == "raise":
        return ["raise", got[1]]
    return ["ok", repr(got[1])[:400]]


def main():
    try:
        mpl, pd, Continuous, Color, l2le = _import_repo()
    except Exception as e:
        print(json.dumps({"status": "error",
                          "instance": "mwaskom__seaborn-3187",
                          "reason": "import failed: %r" % (e,)}))
        return 2

    rng = random.Random(SEED)
    cases = []
    for c in boundary_cases():
        for factor in BOUNDARY_FACTORS:
            cases.append((c, widen(c, factor), True, True))
    for k in range(N_FUZZ):
        c = fuzz_case(rng)
        # the axis range is drawn independently of the tick set
        factor = rng.choice([0, 1, 1, 2, 10, 100, 1000])
        cases.append((c, widen(c, factor), k % SITE1_EVERY == 0,
                      k % SITE1_KINDS_EVERY == 0))

    disagreements = []
    checks = 0
    site1_checks = 0
    site2_checks = 0
    state_checks = 0
    reads_checks = 0
    purity_checks = 0
    raise_agreements = 0
    controls = 0
    discriminated = 0

    wide_range_checks = 0
    for locs, view, do_site1, do_other_conventions in cases:
        if locs and (view[0] < min(locs) or view[1] > max(locs)):
            wide_range_checks += 1
        # ---- site 2: legend_values_locator vs the real utils.py function ---
        _set_via("set_locs")
        got_s = outcome(lambda: shadow_legend_values_locator(
            TickFormatter(DEFAULT_CONVENTION, True, view[0], view[1]),
            list(locs)))
        got_o = outcome(lambda: oracle_site2(mpl, l2le, locs, view))
        site2_checks += 1
        checks += 1
        if got_s[0] != got_o[0] or (got_s[0] == "raise"
                                   and got_s[1] != got_o[1]):
            disagreements.append({
                "site": 2, "locs": locs, "view": list(view),
                "convention": DEFAULT_CONVENTION,
                "shadow_outcome": _j(got_s), "oracle_outcome": _j(got_o),
                "reason": "shadow and oracle disagree on whether the call "
                          "succeeds",
            })
        elif got_s[0] == "raise":
            raise_agreements += 1
        else:
            shadow2 = got_s[1]
            raw2, labels2 = got_o[1]
            raw2_model = [int(x) for x in raw2]
            if labels2 != shadow2 or raw2_model != list(locs):
                disagreements.append({
                    "site": 2, "locs": locs, "view": list(view),
                    "convention": DEFAULT_CONVENTION,
                    "oracle_labels": labels2, "oracle_locs": raw2_model,
                    "shadow_labels": shadow2,
                })
            # clause (iii) on the real labels, default convention
            reads_checks += 1
            if not legend_reads_ticks(labels2, list(locs)):
                disagreements.append({
                    "site": 2, "locs": locs, "view": list(view),
                    "oracle_labels": labels2,
                    "reason": "labels do not all read back to their ticks",
                })

        # ---- site 1: legend_values_continuous vs the real scales.py branch -
        if do_site1:
            conventions = ([DEFAULT_CONVENTION] if not do_other_conventions
                           else sorted(CONVENTIONS))
            for conv in conventions:
                _set_via("format_ticks")
                got_s = outcome(lambda: shadow_legend_values_continuous(
                    TickFormatter(conv, True, view[0], view[1]), list(locs)))
                got_o = outcome(lambda: oracle_site1(
                    mpl, pd, Continuous, Color, locs, conv, view))
                site1_checks += 1
                checks += 1
                if got_s[0] != got_o[0] or (got_s[0] == "raise"
                                           and got_s[1] != got_o[1]):
                    disagreements.append({
                        "site": 1, "locs": locs, "view": list(view),
                        "convention": conv, "shadow_outcome": _j(got_s),
                        "oracle_outcome": _j(got_o),
                        "reason": "shadow and oracle disagree on whether the "
                                  "call succeeds",
                    })
                    continue
                if got_s[0] == "raise":
                    raise_agreements += 1
                    continue
                shadow1 = got_s[1]
                raw1, labels1, fmt_after = got_o[1]
                raw1_model = [int(x) for x in raw1]
                # clause (i): exact label texts, in order
                if labels1 != shadow1 or raw1_model != list(locs):
                    disagreements.append({
                        "site": 1, "locs": locs, "view": list(view),
                        "convention": conv,
                        "oracle_labels": labels1, "oracle_locs": raw1_model,
                        "shadow_labels": shadow1,
                    })
                # clause (ii): the formatter the call was handed is left with
                # residual rendering disabled, and is still the same kind
                state_checks += 1
                if residual_state(fmt_after):
                    disagreements.append({
                        "site": 1, "locs": locs, "view": list(view),
                        "convention": conv,
                        "reason": "formatter left with residual rendering on",
                    })
                if type(fmt_after) is not type(real_formatter(conv)):
                    disagreements.append({
                        "site": 1, "locs": locs, "view": list(view),
                        "convention": conv,
                        "reason": "formatter convention changed by the call",
                    })
                # clause (iii): only for the default convention
                if conv == DEFAULT_CONVENTION:
                    reads_checks += 1
                    if not legend_reads_ticks(labels1, list(locs)):
                        disagreements.append({
                            "site": 1, "locs": locs, "view": list(view),
                            "convention": conv, "oracle_labels": labels1,
                            "reason": "labels do not all read back to ticks",
                        })

        # ---- purity control on the bridge (boundary cases only) ------------
        if locs and do_other_conventions:
            for conv in sorted(CONVENTIONS):
                for via in ("format_ticks", "set_locs"):
                    purity_checks += 1
                    a = outcome(lambda: _render(conv, list(locs), False,
                                                view[0], view[1], via))
                    b = outcome(lambda: _render(conv, list(locs), False,
                                                view[0], view[1], via))
                    if a != b:
                        disagreements.append({
                            "locs": locs, "view": list(view),
                            "convention": conv, "via": via,
                            "reason": "bridge not a pure function of its "
                                      "arguments",
                        })

        # ---- negative control: would the PRE-STATE impl have differed? -----
        if (locs and controls < MAX_CONTROL
                and max(abs(v) for v in locs) > 10 ** 7):
            controls += 1
            _set_via("format_ticks")
            try:
                pre = prepatch_shadow(
                    TickFormatter(DEFAULT_CONVENTION, True, view[0], view[1]),
                    list(locs))
                post = shadow_legend_values_continuous(
                    TickFormatter(DEFAULT_CONVENTION, True, view[0], view[1]),
                    list(locs))
            except Exception:
                pre = post = None
            if pre is not None and pre != post:
                discriminated += 1

        if len(disagreements) >= MAX_REPORTED:
            break

    ok = (not disagreements) and checks >= 100_000 and discriminated > 0
    print(json.dumps({
        "status": "pass" if ok else "fail",
        "instance": "mwaskom__seaborn-3187",
        "backend": "nagini",
        "checks": checks,
        "site1_checks": site1_checks,
        "site2_checks": site2_checks,
        "state_checks": state_checks,
        "reads_checks": reads_checks,
        "purity_checks": purity_checks,
        "raise_agreements": raise_agreements,
        "inputs": len(cases),
        "boundary_cases": len(boundary_cases()),
        "fuzz_draws": N_FUZZ,
        "seed": SEED,
        "label_comparison": "exact text",
        "axis_range_driven_independently": True,
        "wider_than_ticks_checks": wide_range_checks,
        "boundary_range_factors": list(BOUNDARY_FACTORS),
        "conventions_driven": CONVENTIONS,
        "state_half_observed_at": "site 1 (site 2 builds its own formatter)",
        "oracle": ["seaborn._core.scales.ContinuousBase._setup legend branch",
                   "seaborn.utils.locator_to_legend_entries"],
        "shadow_provenance": "pure + impl regions of model.py, verbatim",
        "prepatch_controls_evaluated": controls,
        "prepatch_controls_cap": MAX_CONTROL,
        "discriminates_prepatch": discriminated > 0,
        "prepatch_disagreeing_cases": discriminated,
        "disagreements": disagreements[:MAX_REPORTED],
    }))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
