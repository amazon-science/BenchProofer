# properties.py — PBT manifest for mwaskom__seaborn-3069. NOT a Nagini module; a
# record of adversarial cases. The runner (swebench_nagini.pbt) executes each and
# stamps RESULT. Spec cases are full model.py variants (frozen spec, swapped impl
# region only) checked by Nagini verify + same_spec; axiom cases are real-callee
# probes checked in the instance Docker image (apply_gold=True).
#
# DEFENDED SURFACE (reasoned, not mechanical):
#   finalize_axis_range(is_categorical, has_explicit, is_vertical, user_lo, user_hi)
#     -> Tuple[float,float]. ALL inputs are read-only SCALARS passed by value
#     (bool / float). There is NO mutable reference input (no Acc(x,1/2)), so the
#     frame-mutation weakness class is N/A here — there is nothing to overwrite.
#     The postcondition fully pins the value in EVERY guarded sub-domain:
#       cat & !explicit & !vertical : lo+0.5==0  (lo==-0.5),  hi+0.5==slot_count()
#                                     (hi==n-0.5), lo<hi
#       cat & !explicit &  vertical : hi+0.5==0,  lo+0.5==slot_count(), lo>hi
#       has_explicit (any cat/vert) : Result[0]==user_lo, Result[1]==user_hi
#       !cat & !explicit            : Result[0]==user_lo, Result[1]==user_hi
#                                     (ordinary axis left at its pre-existing
#                                     automatic-margin range, untouched)
#     The non-categorical & non-explicit clause is NOT optional: the G-EQ
#     auditor built a verifying rival that dropped the is_categorical gate and
#     applied the categorical (-0.5, n-0.5) range to EVERY non-explicit axis;
#     its faithful patch clobbered ordinary (log-scaled) axes and FAILED the
#     hidden PASS_TO_PASS tests (test_faceted_log_scale,
#     test_paired_single_log_scale). The spec now pins that sub-domain to the
#     identity (range returned unchanged), and rival-cat-everywhere below
#     replays that exact attack and must be rejected.
#   finalize_axis_grid(is_categorical, pre_visible) -> bool :
#       categorical      -> False (grid turned off, whatever it was before);
#       non-categorical  -> pre_visible (the finalizer never touches an
#                           ordinary axis's grid — identity). The identity
#       clause is NOT optional: the earlier spec hardcoded the ordinary-axis
#       result to True, which misstates the real finalizer (it does NOTHING
#       to an ordinary axis's grid; visibility stays whatever it was going
#       in) and admitted a rival whose faithful patch FORCES a grid state on
#       ordinary axes. rival-grid-always-on / rival-grid-force-off below
#       replay that shape and must be rejected.
#
#   slot_count() is @Pure @ContractOnly with Ensures(Result()>=1). It appears in
#   BOTH the postcondition (hi+0.5==slot_count()) and is callable from the impl,
#   so it is a GROUNDED oracle (the upper edge is pinned to the very same opaque
#   value the work consumes) — there is no separate answer-key to echo, hence the
#   ungrounded-oracle-echo class is N/A; the cheapest grounded impl IS gold and is
#   used as a positive control. Both functions are pure value-returning (no raise,
#   no side effect), so the control-flow-effect class is N/A too. The live attack
#   surface is therefore PARTIAL-DOMAIN (a rival correct on most guards but wrong
#   on one F2P-exercised guard) + positive-control/admissibility soundness.
from pathlib import Path

INSTANCE = "mwaskom__seaborn-3069"
FLOAT_ENCODING = "real"   # meta.json float_encoding — the range is interpreted reals

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ----------------------------------------------------------------------------
# Exact frozen impl-region bodies (the ONLY text any variant edits). Lifted
# verbatim from model.py so a swap is guaranteed to land inside impl-start/end.
# ----------------------------------------------------------------------------
_RANGE_IMPL = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        # Caller pinned the range explicitly: use it verbatim. The categorical
        # special-casing below is skipped.
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

_GRID_IMPL = """    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible"""


# ============================ POSITIVE CONTROLS =============================

# pos-range-reorder: a structurally DIFFERENT but correct range impl. It handles
# the categorical case with explicit conditional expressions and computes the
# vertical pair via direct (hi, lo) assignment instead of a tmp-swap, and orders
# the branches differently (categorical first, explicit verbatim as the else).
# Every guarded value is identical to gold, so it MUST verify. No framing
# lemma is needed (the postcondition pins concrete linear equations the verifier
# discharges directly from the assignments).
_POS_RANGE = """    lo = user_lo
    hi = user_hi
    if not has_explicit and is_categorical:
        n = slot_count()
        if is_vertical:
            lo = n - 0.5
            hi = -0.5
        else:
            lo = -0.5
            hi = n - 0.5
    else:
        lo = user_lo
        hi = user_hi
    return (lo, hi)"""

# pos-grid-direct: a structurally different correct grid impl — a conditional
# expression instead of the assign-then-override shape.
_POS_GRID = """    visible = False if is_categorical else pre_visible
    return visible"""

# cheapest-grounded-range: the honest cheapest impl for the categorical case.
# Because slot_count() is a GROUNDED oracle (the postcondition pins hi to the
# very same slot_count() value), returning (-0.5, slot_count()-0.5) directly is
# gold, not a wrong echo — it MUST verify. This is the ungrounded-oracle slot's
# honest positive control (there is no wrong echo to build).
_CHEAP_RANGE = """    if has_explicit:
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        if is_vertical:
            return (n - 0.5, -0.5)
        return (-0.5, n - 0.5)
    else:
        lo = user_lo
        hi = user_hi
    return (lo, hi)"""


# ============================ ADMISSIBILITY ================================

# admiss-range: a positive-control caller that invokes finalize_axis_range on a
# representative F2P-shaped input (the x-categorical witness: cats ["a","b","c"]
# so the *intended* range is (-0.5, 2.5)) and the explicit-range witness. The
# caller asserts the precondition (genuine non-NaN numbers; a non-singular
# pair when explicit) is establishable and that the result it gets back satisfies
# the categorical lower-edge / verbatim clauses. If the Requires rejected a
# normal numeric input the self-call would fail to establish it -> PRECOND-TOO-
# STRONG. To keep the spec view byte-identical (same_spec preserved) we embed the
# caller INSIDE the finalize_axis_grid impl region (only impl text changes); the
# grid function still returns the correct grid value afterwards.
_ADMISS_GRID = """    # admissibility self-call: the precondition (non-NaN numbers; explicit
    # pair non-singular) must admit a genuine numeric F2P-shaped input.
    r = finalize_axis_range(True, False, False, 0.0, 0.0)
    Assert(r[0] + 0.5 == 0.0)          # categorical lower edge is exactly -0.5
    r2 = finalize_axis_range(True, True, False, -1.0, 2.1)
    Assert(r2[0] == -1.0)              # explicit caller range used verbatim
    Assert(r2[1] == 2.1)
    grid_visible = pre_visible
    if is_categorical:
        grid_visible = False
    return grid_visible"""


# ============================ UNIQUENESS RIVALS =============================
# Each is a faithful-looking impl that gets ONE F2P-exercised guard wrong. Each
# carries the refinement argument that its real patch would NOT resolve the F2P.

# rival-lo-zero: drops the -0.5 categorical lower edge (uses 0.0). On the
# horizontal categorical F2P this returns (0.0, n-0.5) instead of (-0.5, n-0.5).
_RIVAL_LO_ZERO = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = 0.0
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

# rival-no-invert: omits the vertical swap, so a vertical categorical axis gets
# the increasing (-0.5, n-0.5) pair instead of the inverted (n-0.5, -0.5).
_RIVAL_NO_INVERT = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
    return (lo, hi)"""

# rival-cat-over-explicit: when BOTH categorical and explicit, applies the
# categorical range instead of honoring the caller's verbatim (lo, hi). On the
# .limit(x=(-1,2.1)) F2P this would return (-0.5, n-0.5) instead of (-1, 2.1).
_RIVAL_CAT_OVER_EXPLICIT = """    lo = user_lo
    hi = user_hi
    if is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

# rival-wrong-upper: off-by-one on the upper edge (n + 0.5 instead of n - 0.5).
# Returns (-0.5, n+0.5) on horizontal categorical — too wide by exactly one slot.
_RIVAL_WRONG_UPPER = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        n = slot_count()
        lo = -0.5
        hi = n + 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

# rival-hardcode-one: hardcodes the upper edge as 0.5 (the n==1 special case),
# ignoring slot_count(). Correct ONLY when there is exactly one category, wrong
# for the 3-category F2P (would give (-0.5, 0.5) instead of (-0.5, 2.5)).
_RIVAL_HARDCODE_ONE = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    elif is_categorical:
        lo = -0.5
        hi = 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

# rival-cat-everywhere: drops the is_categorical gate — applies the categorical
# (-0.5, n-0.5) range (inverted on y) to EVERY axis without an explicit caller
# range, categorical or not. This is the exact rival the G-EQ auditor built
# (atk_1): it verified under the old spec (which left !cat & !explicit
# unconstrained) but its faithful patch clobbered ordinary log-scaled axes and
# failed the hidden P2P tests. Under the strengthened spec the !cat & !explicit
# identity clauses must reject it.
_RIVAL_CAT_EVERYWHERE = """    lo = user_lo
    hi = user_hi
    if has_explicit:
        lo = user_lo
        hi = user_hi
    else:
        n = slot_count()
        lo = -0.5
        hi = n - 0.5
        if is_vertical:
            tmp = lo
            lo = hi
            hi = tmp
    return (lo, hi)"""

# rival-grid-always-on: forces the grid ON for every axis — never turns it off
# for a categorical axis (the pre-patch behaviour on the F2P witnesses under
# a grid-drawing style) AND clobbers ordinary axes whose grid was off.
_RIVAL_GRID_ON = """    grid_visible = True
    return grid_visible"""

# rival-grid-inverted: returns is_categorical (grid ON for categorical, OFF for
# ordinary) — exactly backwards from the patch.
_RIVAL_GRID_INVERTED = """    visible = is_categorical
    return visible"""

# rival-grid-passthrough = the genuine prepatch behaviour: the finalizer never
# touches ANY axis's grid, so a categorical axis keeps its incoming visibility
# instead of being forced off.
_RIVAL_GRID_PASSTHROUGH = """    grid_visible = pre_visible
    return grid_visible"""

# rival-grid-force-off: turns the grid off for EVERY axis, categorical or not
# — the shape the old hardcoded-ordinary-result spec could not distinguish
# from correct on the categorical side, now rejected by the identity clause.
_RIVAL_GRID_FORCE_OFF = """    grid_visible = False
    return grid_visible"""


SPEC_TESTS = [
    # ----------------------- positive controls (verify) -----------------------
    {
        "id": "pos-range-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RANGE_IMPL, _POS_RANGE),
        "rationale": "a structurally-different but value-identical correct range "
                     "impl (categorical-first branch order, direct (hi,lo) for the "
                     "vertical case instead of a tmp-swap). It pins exactly the same "
                     "linear edges, so all Ensures discharge directly — must verify "
                     "(else SPEC-TOO-STRONG). No framing lemma needed.",
    },
    {
        "id": "pos-grid-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GRID_IMPL, _POS_GRID),
        "rationale": "a structurally different correct grid impl: a conditional "
                     "expression instead of assign-then-override. Satisfies both "
                     "grid clauses (categorical off, ordinary pass-through) — must "
                     "verify.",
    },
    {
        "id": "cheap-grounded-range",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _RANGE_IMPL, _CHEAP_RANGE),
        "rationale": "ungrounded-oracle slot is N/A (slot_count() is grounded — the "
                     "postcondition pins hi to the same slot_count() value). The "
                     "honest cheapest grounded impl, returning (-0.5, slot_count()-"
                     "0.5) (inverted on y) directly, IS gold and must verify; there "
                     "is no wrong echo to construct.",
    },
    # ----------------------- admissibility (verify) ---------------------------
    {
        "id": "admiss-fshaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GRID_IMPL, _ADMISS_GRID),
        "rationale": "a positive-control caller invokes finalize_axis_range on the "
                     "F2P-shaped categorical-x input (and the explicit-range "
                     "witness, a genuine non-singular pair). The precondition must "
                     "admit these normal numeric inputs; the caller's Asserts on "
                     "the returned edges must discharge — else PRECOND-TOO-STRONG.",
    },
    # --------------------- partial-domain rivals (reject) ---------------------
    {
        "id": "rival-lo-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_LO_ZERO),
        "refinement": "Its faithful real patch sets lo=0.0 for the categorical "
                      "lower edge, so on the F2P test_nominal_x_axis_tweaks the real "
                      "get_xlim() would be (0.0, 2.5) != (-0.5, 2.5) — the test "
                      "asserts == (-.5, 2.5), so it would FAIL to resolve.",
        "rationale": "violates the postcondition clause Result()[0]+0.5==0.0 (the "
                      "categorical lower edge -0.5) for cat & !explicit & !vertical. "
                      "If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-no-invert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_NO_INVERT),
        "refinement": "Its faithful real patch omits the `if axis=='y': lo,hi="
                      "hi,lo` swap, so on test_nominal_y_axis_tweaks the real "
                      "get_ylim() would be (-0.5, 2.5) (increasing) rather than the "
                      "asserted (2.5, -0.5) (inverted) — the test would FAIL.",
        "rationale": "violates the vertical clauses Result()[1]+0.5==0.0, "
                      "Result()[0]+0.5==slot_count(), and Result()[0]>Result()[1] "
                      "for cat & !explicit & vertical. If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-cat-over-explicit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_CAT_OVER_EXPLICIT),
        "refinement": "Its faithful real patch drops the `if axis_key not in "
                      "p._limits:` guard, so it applies the categorical (-0.5,n-0.5) "
                      "range even when the caller pinned a limit. On the F2P "
                      "`p.limit(x=(-1,2.1))` clause the real get_xlim() would be "
                      "(-0.5, 2.5) rather than the asserted (-1, 2.1) — FAILS.",
        "rationale": "violates Implies(has_explicit, Result()[0]==user_lo and "
                      "Result()[1]==user_hi): when both has_explicit and "
                      "is_categorical, the verbatim caller range must win. If it "
                      "verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-wrong-upper",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_WRONG_UPPER),
        "refinement": "Its faithful real patch uses nticks + .5 for the upper edge, "
                      "so on test_nominal_x_axis_tweaks the real get_xlim() would be "
                      "(-0.5, 3.5) != asserted (-0.5, 2.5) — FAILS to resolve.",
        "rationale": "violates Result()[1]+0.5==slot_count() (upper edge must be "
                      "n-0.5, i.e. slot_count()-0.5). If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-hardcode-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_HARDCODE_ONE),
        "refinement": "Its faithful real patch hardcodes hi=0.5 (ignores nticks), so "
                      "on the 3-category F2P the real get_xlim() would be (-0.5, 0.5) "
                      "!= asserted (-0.5, 2.5) — FAILS. (Correct only for n==1, which "
                      "the F2P never uses.)",
        "rationale": "violates Result()[1]+0.5==slot_count(): the upper edge must "
                      "equal slot_count()-0.5 for the OPAQUE slot_count()>=1, not the "
                      "n==1 constant 0.5. If it verifies => SPEC-TOO-WEAK (the spec "
                      "would have failed to bind the edge to the real category count).",
    },
    {
        "id": "rival-cat-everywhere",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _RANGE_IMPL, _RIVAL_CAT_EVERYWHERE),
        "refinement": "The G-EQ auditor's actual attack: its faithful real patch "
                      "drops the isinstance(..., Nominal) gate and applies the "
                      "(-0.5, nticks-0.5) range to every non-explicit axis, so "
                      "ordinary log-scaled axes get clobbered — the hidden P2P "
                      "tests test_faceted_log_scale and test_paired_single_log_"
                      "scale FAIL (observed: resolved=False in the recorded G-EQ "
                      "attack run).",
        "rationale": "violates the new identity clauses Implies(not is_categorical "
                      "and not has_explicit, Result()[0]==user_lo and Result()[1]=="
                      "user_hi): a non-categorical non-explicit axis must be left "
                      "at its incoming automatic-margin range. If it verifies => "
                      "SPEC-TOO-WEAK (the original G-EQ break).",
    },
    {
        "id": "rival-grid-always-on",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GRID_IMPL, _RIVAL_GRID_ON),
        "refinement": "Its faithful real patch forces every axis's grid ON: the "
                      "categorical F2P axis still shows gridlines, so the assertion "
                      "`not any(x.get_visible() ...)` on test_nominal_x_axis_tweaks "
                      "FAILS.",
        "rationale": "violates Implies(is_categorical, not Result()): a categorical "
                      "axis must report grid OFF; also violates the ordinary-axis "
                      "identity when pre_visible is False. If it verifies => "
                      "SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-grid-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GRID_IMPL, _RIVAL_GRID_INVERTED),
        "refinement": "Its faithful real patch turns the grid OFF for ordinary axes "
                      "and keeps it ON for categorical — the exact inverse of the "
                      "patch — so the categorical-axis F2P gridline assertion FAILS.",
        "rationale": "violates Implies(is_categorical, not Result()) (returns "
                      "is_categorical). If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-grid-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GRID_IMPL, _RIVAL_GRID_PASSTHROUGH),
        "refinement": "The genuine prepatch behaviour: its faithful real patch never "
                      "calls the grid-off routine, so under the default grid-drawing "
                      "style the categorical F2P axis keeps visible gridlines and "
                      "`not any(x.get_visible() ...)` FAILS.",
        "rationale": "violates Implies(is_categorical, not Result()) when "
                      "pre_visible is True (the F2P scenario: the incoming style "
                      "draws the grid). If it verifies => SPEC-TOO-WEAK.",
    },
    {
        "id": "rival-grid-force-off",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GRID_IMPL, _RIVAL_GRID_FORCE_OFF),
        "refinement": "Its faithful real patch turns the grid off unconditionally "
                      "(drops the categorical gate on the grid-off call), so an "
                      "ordinary axis whose active style draws gridlines loses them "
                      "— a behaviour change on axes the finalizer must leave alone "
                      "(observable whenever a grid-drawing style is active on a "
                      "continuous axis).",
        "rationale": "violates Implies(not is_categorical, Result()==pre_visible) "
                      "when pre_visible is True: an ordinary axis must keep its "
                      "incoming grid visibility. If it verifies => SPEC-TOO-WEAK "
                      "(the exact hole the old hardcoded-ordinary-result spec left).",
    },
]


# ============================ AXIOM LANE ===================================
# slot_count() is the one @ContractOnly axiom (A-consumed); the range & grid deep
# models are A-references validated == the real callee. The probes below are
# self-contained (only the probe is mounted at /work; they import stdlib +
# seaborn/matplotlib which live in the instance image) and run with apply_gold=
# True (the axiom describes post-gold behaviour). Logic mirrors axiom_check.py.

_AX_SOUND_SLOT = r'''
import sys
import matplotlib
matplotlib.use("Agg")
from seaborn._core.plot import Plot
import string

# axiom-soundness: slot_count()'s Ensures is Result()>=1 (the weakest fact the
# proof needs). The real callee is len(axis.get_major_ticks()) on a categorical
# axis. Under the caller's runtime config (a categorical/Nominal axis with no
# explicit limit, exactly what _finalize_figure reaches), assert the real count
# is >= 1 AND equals the category count (so n-0.5 is grounded in the real n).
viol = 0
for n in range(1, 13):
    cats = list(string.ascii_lowercase[:n])
    ydata = list(range(n))
    # categorical x
    axx = Plot(x=cats, y=ydata).plot()._figure.axes[0]
    ntx = len(axx.xaxis.get_major_ticks())
    if ntx < 1:
        print("UNSOUND: cat-x n=%d reported %d major ticks (<1)" % (n, ntx)); viol += 1
    elif ntx != n:
        print("GROUNDING-BROKEN: cat-x n=%d reported %d ticks != %d cats" % (n, ntx, n)); viol += 1
    # categorical y
    axy = Plot(x=ydata, y=cats).plot()._figure.axes[0]
    nty = len(axy.yaxis.get_major_ticks())
    if nty < 1:
        print("UNSOUND: cat-y n=%d reported %d major ticks (<1)" % (n, nty)); viol += 1
    elif nty != n:
        print("GROUNDING-BROKEN: cat-y n=%d reported %d ticks != %d cats" % (n, nty, n)); viol += 1
if viol:
    print("slot_count axiom: %d violation(s)" % viol); sys.exit(1)
print("slot_count axiom SOUND: real major-tick count >= 1 and == #categories on "
      "n=1..12 (x & y); Ensures(Result()>=1) holds, edge grounded in real n.")
sys.exit(0)
'''

_AX_REF_RANGE = r'''
import sys
import matplotlib
matplotlib.use("Agg")
from seaborn._core.plot import Plot
import string

def model_range(is_cat, has_exp, is_vert, ulo, uhi, n):
    lo, hi = ulo, uhi
    if has_exp:
        lo, hi = ulo, uhi
    elif is_cat:
        lo, hi = -0.5, n - 0.5
        if is_vert:
            lo, hi = hi, lo
    return (lo, hi)

def real_axis(xv, yv, lim=None):
    p = Plot(x=xv, y=yv)
    if lim is not None:
        p = p.limit(**lim)
    return p.plot()._figure.axes[0]

viol = 0
# A-reference: the deep range model == real get_xlim/get_ylim on the exact F2P
# witnesses + an n=1..12 sweep + verbatim explicit ranges.
# F2P witnesses
ax = real_axis(["a","b","c"], [1,2,3])
if tuple(ax.get_xlim()) != model_range(True, False, False, None, None, 3):
    print("RANGE-UNSOUND cat-x F2P: real %r != model %r" % (tuple(ax.get_xlim()), (-0.5, 2.5))); viol += 1
ax = real_axis([1,2,3], ["a","b","c"])
if tuple(ax.get_ylim()) != model_range(True, False, True, None, None, 3):
    print("RANGE-UNSOUND cat-y F2P: real %r != model %r" % (tuple(ax.get_ylim()), (2.5, -0.5))); viol += 1
ax = real_axis(["a","b","c"], [1,2,3], lim={"x": (-1, 2.1)})
if tuple(ax.get_xlim()) != model_range(True, True, False, -1, 2.1, 3):
    print("RANGE-UNSOUND explicit-x F2P: real %r != (-1, 2.1)" % (tuple(ax.get_xlim()),)); viol += 1
ax = real_axis([1,2,3], ["a","b","c"], lim={"y": (-1, 2.1)})
if tuple(ax.get_ylim()) != model_range(True, True, True, -1, 2.1, 3):
    print("RANGE-UNSOUND explicit-y F2P: real %r != (-1, 2.1)" % (tuple(ax.get_ylim()),)); viol += 1
# sweep
for n in range(1, 13):
    cats = list(string.ascii_lowercase[:n]); yd = list(range(n))
    axx = real_axis(cats, yd)
    if tuple(axx.get_xlim()) != model_range(True, False, False, None, None, n):
        print("RANGE-UNSOUND cat-x n=%d: real %r != model %r" % (n, tuple(axx.get_xlim()), (-0.5, n-0.5))); viol += 1
    axy = real_axis(yd, cats)
    if tuple(axy.get_ylim()) != model_range(True, False, True, None, None, n):
        print("RANGE-UNSOUND cat-y n=%d: real %r != model %r" % (n, tuple(axy.get_ylim()), (n-0.5, -0.5))); viol += 1
    for lim in [(-1.0, 2.1), (0.0, 10.0), (-5.0, 5.0)]:
        axx = real_axis(cats, yd, lim={"x": lim})
        if tuple(axx.get_xlim()) != tuple(lim):
            print("RANGE-UNSOUND explicit-x n=%d lim=%r: real %r" % (n, lim, tuple(axx.get_xlim()))); viol += 1
        axy = real_axis(yd, cats, lim={"y": lim})
        if tuple(axy.get_ylim()) != tuple(lim):
            print("RANGE-UNSOUND explicit-y n=%d lim=%r: real %r" % (n, lim, tuple(axy.get_ylim()))); viol += 1
# identity clause (!cat & !explicit): a continuous axis keeps its range
# untouched — the finalizer never enters the Nominal block. Ground it by
# capturing the real range immediately BEFORE Plotter._finalize_figure runs
# (that is user_lo/user_hi) and asserting the finalized range equals it.
from seaborn._core.plot import Plotter
for xv, yv in [([1, 2, 3], [1, 2, 3]), ([0.5, 1.5, 2.5, 3.5], [10, 20, 5, 40])]:
    captured = {}
    orig = Plotter._finalize_figure
    def cap(self, p, _c=captured, _o=orig):
        for a in self._figure.axes:
            _c[id(a)] = (tuple(a.get_xlim()), tuple(a.get_ylim()))
        return _o(self, p)
    Plotter._finalize_figure = cap
    try:
        fig = Plot(x=xv, y=yv).plot()._figure
    finally:
        Plotter._finalize_figure = orig
    ax = fig.axes[0]
    pre_x, pre_y = captured[id(ax)]
    if tuple(ax.get_xlim()) != model_range(False, False, False, pre_x[0], pre_x[1], None):
        print("RANGE-UNSOUND identity-x %r: finalized %r != pre-finalize %r" % (xv, tuple(ax.get_xlim()), pre_x)); viol += 1
    if tuple(ax.get_ylim()) != model_range(False, False, True, pre_y[0], pre_y[1], None):
        print("RANGE-UNSOUND identity-y %r: finalized %r != pre-finalize %r" % (yv, tuple(ax.get_ylim()), pre_y)); viol += 1
# and the P2P observable the gate-dropping rival broke: a log-scaled continuous
# axis finalizes untouched (the rival crashed in get_major_ticks / clobbered
# the range) with an intact log transform (the tests' exact assertion).
captured = {}
orig = Plotter._finalize_figure
def cap_log(self, p, _c=captured, _o=orig):
    for a in self._figure.axes:
        _c[id(a)] = tuple(a.get_ylim())
    return _o(self, p)
Plotter._finalize_figure = cap_log
try:
    figl = Plot(y=[1, 10, 100]).scale(y="log").plot()._figure
finally:
    Plotter._finalize_figure = orig
axl = figl.axes[0]
pre_ly = captured[id(axl)]
if tuple(axl.get_ylim()) != model_range(False, False, True, pre_ly[0], pre_ly[1], None):
    print("RANGE-UNSOUND identity-log: finalized %r != pre-finalize %r" % (tuple(axl.get_ylim()), pre_ly)); viol += 1
got = [float(v) for v in axl.yaxis.get_transform().transform([1, 10, 100])]
if got != [0.0, 1.0, 2.0]:
    print("RANGE-UNSOUND identity-log: transform([1,10,100]) == %r != [0,1,2]" % (got,)); viol += 1
if viol:
    print("range deep-model: %d violation(s)" % viol); sys.exit(1)
print("range deep-model == real get_xlim/get_ylim on the 4 F2P witnesses + "
      "n=1..12 (x & y) + verbatim explicit ranges + identity sub-domain "
      "(continuous axes untouched, log axis intact). 0 violations.")
sys.exit(0)
'''

_AX_REF_GRID = r'''
import sys
import matplotlib
matplotlib.use("Agg")
from seaborn._core.plot import Plot, Plotter
import string

def grid_on(axis_obj):
    return any(g.get_visible() for g in axis_obj.get_gridlines())

def model_grid(is_cat, pre_visible):
    if is_cat:
        return False
    return pre_visible

viol = 0
# A-reference: the deep grid model finalize_axis_grid(is_cat, pre_visible):
# categorical -> grid OFF whatever it was before; ordinary -> the finalizer
# leaves the pre-finalization visibility unchanged. Categorical checked under
# both a grid-drawing and a grid-suppressing rc theme; the ordinary identity
# checked by capturing visibility immediately before _finalize_figure runs.
for rc in (None, {"axes.grid": True}, {"axes.grid": False}):
    for n in range(1, 13):
        cats = list(string.ascii_lowercase[:n]); yd = list(range(n))
        px = Plot(x=cats, y=yd)
        py = Plot(x=yd, y=cats)
        if rc is not None:
            px = px.theme(rc); py = py.theme(rc)
        axx = px.plot()._figure.axes[0]
        if grid_on(axx.xaxis) != model_grid(True, True):
            print("GRID-UNSOUND cat-x n=%d rc=%r: gridlines visible (model predicts none)" % (n, rc)); viol += 1
        axy = py.plot()._figure.axes[0]
        if grid_on(axy.yaxis) != model_grid(True, True):
            print("GRID-UNSOUND cat-y n=%d rc=%r: gridlines visible (model predicts none)" % (n, rc)); viol += 1
# ordinary-axis grid identity: capture pre-finalization visibility, assert the
# finalized visibility equals the model's prediction from it, for both truth
# values of pre_visible (driven by the theme).
seen = set()
for rc in ({"axes.grid": True}, {"axes.grid": False}):
    captured = {}
    orig = Plotter._finalize_figure
    def cap(self, p, _c=captured, _o=orig):
        for a in self._figure.axes:
            _c[id(a)] = (grid_on(a.xaxis), grid_on(a.yaxis))
        return _o(self, p)
    Plotter._finalize_figure = cap
    try:
        fig = Plot(x=[1, 2, 3], y=[1, 2, 3]).theme(rc).plot()._figure
    finally:
        Plotter._finalize_figure = orig
    ax = fig.axes[0]
    pre_gx, pre_gy = captured[id(ax)]
    seen.update((pre_gx, pre_gy))
    if grid_on(ax.xaxis) != model_grid(False, pre_gx):
        print("GRID-UNSOUND identity-x rc=%r: finalized %r != pre %r" % (rc, grid_on(ax.xaxis), pre_gx)); viol += 1
    if grid_on(ax.yaxis) != model_grid(False, pre_gy):
        print("GRID-UNSOUND identity-y rc=%r: finalized %r != pre %r" % (rc, grid_on(ax.yaxis), pre_gy)); viol += 1
if seen != {True, False}:
    print("GRID-COVERAGE: pre_visible only took %r across themes" % (seen,)); viol += 1
if viol:
    print("grid deep-model: %d violation(s)" % viol); sys.exit(1)
print("grid deep-model == real gridline visibility: every categorical axis "
      "(n=1..12, x & y, both grid rc themes) shows no visible gridlines; "
      "ordinary axes keep their pre-finalization visibility (both truth "
      "values exercised). 0 violations.")
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-slot_count",
        "axiom": "slot_count",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_SLOT,
        "rationale": "slot_count()'s Ensures is Result()>=1. The real callee "
                     "len(axis.get_major_ticks()) must be >=1 (and == #categories, "
                     "grounding the n-0.5 edge) on every categorical axis the "
                     "finalizer reaches (n=1..12, x & y). A count <1 => AXIOM-UNSOUND.",
    },
    {
        "id": "ax-ref-range",
        "axiom": "finalize_axis_range",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_RANGE,
        "rationale": "A-reference: the range deep model must equal the real "
                     "get_xlim/get_ylim on every caller-reachable categorical input "
                     "(F2P witnesses + n=1..12 sweep + verbatim explicit ranges). Any "
                     "disagreement => the deep model is unsound vs the real callee.",
    },
    {
        "id": "ax-ref-grid",
        "axiom": "finalize_axis_grid",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_REF_GRID,
        "rationale": "A-reference: the grid deep model (categorical -> off, "
                     "ordinary -> pre-finalization visibility unchanged) must equal "
                     "the real gridline visibility — a categorical axis draws no "
                     "visible gridlines under either grid rc theme (n=1..12, x & y), "
                     "and an ordinary axis keeps exactly the visibility it had "
                     "before the finalizer ran (both truth values exercised). Any "
                     "disagreement => the deep model is unsound vs the real callee.",
    },
]
