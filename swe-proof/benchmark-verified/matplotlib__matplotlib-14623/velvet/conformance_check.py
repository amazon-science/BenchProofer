#!/usr/bin/env python3
"""G-CONF differential conformance for matplotlib__matplotlib-14623 (velvet).

Band: order-only + exact-value (CLAUDE.md float rule). TWO operations are modeled,
the two coordinated halves of the gold patch, and both are checked here.

OPERATION 1 (`commitLimits`) is the limit-commit block: capture the requested
orientation, consult the axis normalizer, commit the normalizer's endpoints in the
requested orientation. OPERATION 2 (`defaultMemberAdjust`) is the base
`Locator.nonsingular` (ticker.py:1523-1525, also edited by the gold patch): sort
the two requested values, widen the ascending interval, and report THAT -- the
patch drops `increasing=False`, which is what stops the member reinstating the
received order. Sections at the end of this file check operation 2 against the
real patched member, and HARD-ASSERT that each half is load-bearing alone. The
endpoint VALUES come from the real float normalizer in both shadow and oracle
(same callee, same call), so committed pairs are compared for EXACT float
equality; the only modeled logic is the boolean `lo > hi` and the conditional
transposition, both exact.

SHADOW (provenance: transliterated -- the weakest link, per
docs/adding_a_backend.md 1). The `do` block of `commitLimits` in Solution.lean:

    let swapped := lo > hi
    let n     <- normalizeRange lo hi        -- A-tagged: the REAL callee
    let out   := if swapped then (n.2, n.1) else (n.1, n.2)

ORACLE. Two, and the strong one is not a transliteration at all:

  ORACLE-A (END-TO-END, the real patched functions). The gold patch edits FIVE
  limit setters -- `Axes.set_xlim`, `Axes.set_ylim` (axes/_base.py 3262, 3645)
  and `Axes3D.set_xlim3d`, `set_ylim3d`, `set_zlim3d` (mplot3d/axes3d.py 623,
  681, 739) -- and each RETURNS the pair it committed. So the oracle can be the
  patched function itself, called on a real axis. Everything the setter does to
  the REQUEST before the modeled block (`_process_unit_info`,
  `_validate_converted_limits`, the None-defaulting, and -- at the 2D sites only
  -- the log-scale non-positive clamp) is upstream of the block and is
  transliterated here as `upstream_request`, so the comparison is made at the
  block's real entry pair rather than by excluding awkward inputs. Everything
  after it (the `viewLim` assignment, autoscale flags, the shared-axis emit
  cascade) is downstream of the returned pair.

  ORACLE-B (the block, transliterated verbatim from the patched source) carries
  the volume: it is what the >=1e5-input fuzz runs against.

CALLEE. `normalize` (`normalizeRange` in Solution.lean) is the A-consumed axiom
modeling

    axis.get_major_locator().nonsingular(lo, hi)  o  axis.limit_range_for_scale

Shadow and oracle call the SAME real chain on the SAME axis in the SAME state
(the shadow runs first and does not mutate), so this gate refutes only the R/I
transliteration of the capture/restore around the callee -- the callee's own
soundness is G-AX's job (axiom_check.py).

WHAT ELSE IS ASSERTED HERE, and why it belongs in this gate

  1. THE SPEC CLAUSES, ON THE REAL CODE. The six `ensures` of `commitLimits` are
     evaluated against ORACLE-A's committed pair, i.e. against matplotlib's own
     output, at every end-to-end observation. A spec clause that is false of the
     patched implementation dies here. This is the check the previous revision of
     this file did not do, and it is why that revision let an unfaithful clause
     survive.

  2. THE CONDITIONING IS FORCED, NOT COSMETIC. Q4/Q5/Q6 condition orientation on
     the order the normalizer REPORTED on this call. The UNCONDITIONAL form ("a
     descending request commits a descending pair"), which this file used to
     assert, is measured here to be FALSE of the real patched code: on a date
     axis `DateLocator.nonsingular` does not sort, so a descending request comes
     back descending and the patch's swap-back turns it ASCENDING. The script
     REQUIRES at least one such counterexample -- if the unconditional form ever
     became true of the callee family, the conditioned clauses would be weaker
     than they need to be and this check would say so.

  3. THE FAIL-TO-PASS AND REGRESSION BEHAVIOUR, PINNED. The gold test's new leg
     (test_axes.py::test_inverted_limits, added by test_patch) is a LOG axis
     asked for (10, 1): post-patch `get_ylim() == (10, 1)`, where pre-patch
     `LogLocator.nonsingular` sorted it to (1, 10) and nothing swapped back. The
     same test's pre-existing legs pass a descending pair through the LINEAR path
     -- (4, -5) on x and (5, -3) on y, via autoscale with an inverted axis -- and
     must still come back verbatim (that path worked before the patch, because
     `Locator.nonsingular(..., increasing=False)` preserved order; the patch
     dropped `increasing=False`, so preserving it is now the swap-back's job).
     Both are hard-asserted, the log leg at every site whose scale can be set and
     the linear legs at all five.

  4. THE FALSIFICATION BATTERY'S RIVALS ARE BEHAVIOURALLY WRONG. Each of the 15
     `expect: reject` rivals in properties.py is transliterated (11 for operation
     1, 4 for operation 2) and required to DISAGREE with the oracle somewhere in
     the swept domain, and each of the 5 `expect: verify` positives is required to
     agree EVERYWHERE. G-PBT shows the rivals are unprovable against the spec;
     this shows they are also wrong about matplotlib, so the spec is rejecting
     them for a real reason.

  5. BOTH HALVES OF THE GOLD PATCH ARE LOAD-BEARING (hard assertion). The four
     combinations (caller half x callee half) are composed here on a real linear
     default-locator axis and the failing test's own PRE-EXISTING legs are pushed
     through each: the gold pair must return them verbatim, and EITHER half alone
     must not. That is what makes the second modeled operation and its prepatch
     twin necessary rather than decorative. The previous revision of this bundle
     asserted the opposite in prose -- "the ticker hunk needs no clause ... the
     same commit is correct on either side of it" -- and that error is precisely
     what let a refinement that implements the commit block exactly and leaves
     ticker.py at base_commit verify while NOT resolving. The claim is now
     executable and fatal.

Exit 0 iff there are zero shadow/oracle disagreements for EITHER operation, zero
spec-clause violations for either, at least one refutation of the unconditional
order claim, the F2P pairs come back as recorded, every rival is discriminated,
every positive agrees, and each half of the patch is measured to be load-bearing.
stdlib + matplotlib only.
"""
import json
import math
import random
import sys
import warnings

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms
from mpl_toolkits.mplot3d import Axes3D  # noqa: F401  (registers '3d')

SEED = 14623


# ==========================================================================
# the modeled callee
# ==========================================================================
def real_normalize(axis, lo, hi):
    """The A-tagged callee, verbatim (mapping.md 3.1):

        lo, hi = axis.get_major_locator().nonsingular(lo, hi)
        lo, hi = axis.limit_range_for_scale(lo, hi)
    """
    lo, hi = axis.get_major_locator().nonsingular(lo, hi)
    lo, hi = axis.limit_range_for_scale(lo, hi)
    return lo, hi


# ==========================================================================
# SHADOW: the `commitLimits` do block from Solution.lean
# ==========================================================================
def shadow_commit(axis, lo, hi):
    swapped = lo > hi
    n = real_normalize(axis, lo, hi)
    out = (n[1], n[0]) if swapped else (n[0], n[1])
    return out


# ==========================================================================
# ORACLE-B: the patched limit-commit block, transliterated verbatim
#   axes/_base.py (post-patch, set_ylim):
#       swapped = bottom > top
#       bottom, top = self.yaxis.get_major_locator().nonsingular(bottom, top)
#       bottom, top = self.yaxis.limit_range_for_scale(bottom, top)
#       if swapped:
#           bottom, top = top, bottom
# ==========================================================================
def oracle_block(axis, lo, hi):
    swapped = lo > hi
    lo, hi = real_normalize(axis, lo, hi)
    if swapped:
        lo, hi = hi, lo
    return (lo, hi)


# ==========================================================================
# ORACLE-A: the real patched setters, plus the request preprocessing that is
# upstream of the modeled block.
# ==========================================================================
def upstream_request(axis, lo, hi, *, log_guard):
    """Transliteration of everything the setter does to the REQUEST before the
    modeled block. At the 2D sites (axes/_base.py, patched set_ylim):

        if self.get_yscale() == 'log':
            if bottom <= 0: warn; bottom = old_bottom
            if top    <= 0: warn; top    = old_top

    The three mplot3d setters have no such clamp (axes3d.py: the block is
    reached straight after `_validate_converted_limits`), hence `log_guard`.
    `_process_unit_info` / `_validate_converted_limits` / the None-defaulting are
    the identity on the finite floats used here.
    """
    if log_guard and axis.get_scale() == "log":
        old_lo, old_hi = axis.get_view_interval()
        if lo <= 0:
            lo = old_lo
        if hi <= 0:
            hi = old_hi
    return lo, hi


# ==========================================================================
# the family of axes the same block is reached on: (scale x major locator)
# ==========================================================================
def _cfg_linear(axis):
    pass


def _cfg_log(axis):
    _set_scale(axis, "log")


def _cfg_symlog(axis):
    _set_scale(axis, "symlog")


def _cfg_logit(axis):
    _set_scale(axis, "logit")


def _cfg_log_fixed(axis):
    _set_scale(axis, "log")
    axis.set_major_locator(mticker.FixedLocator([1, 2, 3]))


def _cfg_date(axis):
    axis.set_major_locator(mdates.AutoDateLocator())


def _cfg_multiple(axis):
    axis.set_major_locator(mticker.MultipleLocator(2))


def _cfg_maxn(axis):
    axis.set_major_locator(mticker.MaxNLocator(4))


def _cfg_null(axis):
    axis.set_major_locator(mticker.NullLocator())


def _set_scale(axis, name):
    """Set the scale of `axis` whatever axis of whatever Axes it belongs to."""
    ax = axis.axes
    which = _axis_letter(ax, axis)
    getattr(ax, "set_%sscale" % which)(name)


def _axis_letter(ax, axis):
    for letter in ("x", "y", "z"):
        if getattr(ax, "%saxis" % letter, None) is axis:
            return letter
    raise RuntimeError("axis does not belong to its Axes")


MEMBERS = [
    ("linear/AutoLocator", _cfg_linear),
    ("log/LogLocator", _cfg_log),
    ("symlog/SymmetricalLogLocator", _cfg_symlog),
    ("logit/LogitLocator", _cfg_logit),
    ("log/FixedLocator", _cfg_log_fixed),
    ("linear/AutoDateLocator", _cfg_date),
    ("linear/MultipleLocator", _cfg_multiple),
    ("linear/MaxNLocator", _cfg_maxn),
    ("linear/NullLocator", _cfg_null),
]


# ==========================================================================
# the five patched call sites
# ==========================================================================
def _build_2d():
    fig = plt.figure()
    ax = fig.add_subplot(111)
    return fig, ax


def _build_3d():
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="3d")
    return fig, ax


SITES = [
    # (tag, builder, axis letter, setter name, has upstream log clamp)
    ("Axes.set_xlim", _build_2d, "x", "set_xlim", True),
    ("Axes.set_ylim", _build_2d, "y", "set_ylim", True),
    ("Axes3D.set_xlim3d", _build_3d, "x", "set_xlim3d", False),
    ("Axes3D.set_ylim3d", _build_3d, "y", "set_ylim3d", False),
    ("Axes3D.set_zlim3d", _build_3d, "z", "set_zlim3d", False),
]


def make(site, member):
    """Build a fresh (fig, axis, setter) for this (site, member), or None if the
    member's configuration is not available at this site."""
    _tag, build, letter, setter_name, _guard = site
    _mtag, cfg = member
    fig, ax = build()
    axis = getattr(ax, "%saxis" % letter)
    try:
        cfg(axis)
    except Exception:
        plt.close(fig)
        return None
    return fig, axis, getattr(ax, setter_name)


# ==========================================================================
# the six `ensures` of commitLimits, as predicates over one observation
# ==========================================================================
def committed_limits(axis, lo, hi):
    """The `pure` function `committedLimits` from Solution.lean:
        if lo > hi then ((normalize lo hi).2, (normalize lo hi).1)
                   else normalize lo hi
    """
    n = real_normalize(axis, lo, hi)
    return (n[1], n[0]) if lo > hi else (n[0], n[1])


def spec_violations(lo, hi, n, out):
    """Q1..Q6 of Solution.lean, evaluated on a committed pair `out` produced
    from request (lo, hi) when the normalizer reported `n`."""
    bad = []
    expect = (n[1], n[0]) if lo > hi else (n[0], n[1])
    if out != expect:                                            # Q1
        bad.append(("Q1 out = committedLimits lo hi", expect))
    if lo > hi and out != (n[1], n[0]):                          # Q2
        bad.append(("Q2 lo > hi -> out = (n.2, n.1)", (n[1], n[0])))
    if lo <= hi and out != (n[0], n[1]):                         # Q3
        bad.append(("Q3 lo <= hi -> out = n", (n[0], n[1])))
    if n[0] <= n[1] and lo > hi and not (out[1] <= out[0]):      # Q4
        bad.append(("Q4 n.1 <= n.2 -> lo > hi -> out.2 <= out.1", None))
    if n[0] <= n[1] and lo < hi and not (out[0] <= out[1]):      # Q5
        bad.append(("Q5 n.1 <= n.2 -> lo < hi -> out.1 <= out.2", None))
    if n[0] < n[1] and ((lo > hi) != (out[1] < out[0])):         # Q6
        bad.append(("Q6 n.1 < n.2 -> (lo > hi <-> out.2 < out.1)", None))
    return bad


# ==========================================================================
# the falsification battery's rivals and positives, transliterated
# ==========================================================================
def _rival_no_restore(axis, lo, hi, n):
    return (n[0], n[1])


def _rival_cmp_lt(axis, lo, hi, n):
    swapped = lo < hi
    return (n[1], n[0]) if swapped else (n[0], n[1])


def _rival_cmp_ge(axis, lo, hi, n):
    swapped = lo >= hi
    return (n[1], n[0]) if swapped else (n[0], n[1])


def _rival_always_swap(axis, lo, hi, n):
    return (n[1], n[0])


def _rival_partial_no_expand(axis, lo, hi, n):
    return (lo, hi)


def _rival_equal_raw(axis, lo, hi, n):
    if lo > hi:
        return (n[1], n[0])
    if lo == hi:
        return (lo, hi)
    return (n[0], n[1])


def _rival_positivity_gate(axis, lo, hi, n):
    swapped = lo > hi and 0 < lo and 0 < hi
    return (n[1], n[0]) if swapped else (n[0], n[1])


def _rival_postcall_flag(axis, lo, hi, n):
    swapped = n[0] > n[1]
    return (n[1], n[0]) if swapped else (n[0], n[1])


def _rival_ascending_gate(axis, lo, hi, n):
    swapped = (lo > hi) and (n[0] <= n[1])
    return (n[1], n[0]) if swapped else (n[0], n[1])


def _rival_canonicalize(axis, lo, hi, n):
    asc = (n[0], n[1]) if n[0] <= n[1] else (n[1], n[0])
    return (asc[1], asc[0]) if lo > hi else asc


def _rival_echo_transposed(axis, lo, hi, n):
    return committed_limits(axis, hi, lo)


RIVALS = [
    ("reject-no-restore", _rival_no_restore),
    ("reject-cmp-lt", _rival_cmp_lt),
    ("reject-cmp-ge", _rival_cmp_ge),
    ("reject-always-swap", _rival_always_swap),
    ("reject-partial-no-expand", _rival_partial_no_expand),
    ("reject-equal-raw", _rival_equal_raw),
    ("reject-positivity-gate", _rival_positivity_gate),
    ("reject-postcall-flag", _rival_postcall_flag),
    ("reject-ascending-gate", _rival_ascending_gate),
    ("reject-canonicalize", _rival_canonicalize),
    ("reject-echo-transposed", _rival_echo_transposed),
]


def _pos_inline_orientation(axis, lo, hi, n):
    # `let out := if lo > hi then (n.2, n.1) else (n.1, n.2)` -- the `swapped`
    # let inlined.
    return (n[1], n[0]) if lo > hi else (n[0], n[1])


def _pos_branch_select(axis, lo, hi, n):
    # `if lo > hi then (let n <- ...; return (n.2, n.1)) else (...)`
    if lo > hi:
        return (n[1], n[0])
    return (n[0], n[1])


def _pos_pure_reference(axis, lo, hi, n):
    # `let out := committedLimits lo hi`
    return committed_limits(axis, lo, hi)


POSITIVES = [
    ("pos-inline-orientation", _pos_inline_orientation),
    ("pos-branch-select", _pos_branch_select),
    ("pos-pure-reference", _pos_pure_reference),
]


# ==========================================================================
# THE SECOND MODELED OPERATION: `defaultMemberAdjust`, i.e. the base
# `Locator.nonsingular` the gold patch also edits (ticker.py:1523-1525).
# ==========================================================================
def expand_ascending(a, b):
    """The A-tagged callee of the second operation, verbatim from the patched
    source: `mtransforms.nonsingular(v0, v1, expander=.05)`."""
    return tuple(mtransforms.nonsingular(a, b, expander=.05))


def expand_ascending_prepatch(a, b):
    """The same call at base_commit: `increasing=False` still present."""
    return tuple(mtransforms.nonsingular(a, b, increasing=False, expander=.05))


def real_member(v0, v1):
    """ORACLE for the second operation: the REAL patched member itself."""
    return tuple(mticker.Locator().nonsingular(v0, v1))


def shadow_member(v0, v1):
    """The `do` block of `defaultMemberAdjust` in Solution.lean, transliterated:

        let reversed := v1 < v0
        let a := if reversed then v1 else v0
        let b := if reversed then v0 else v1
        let e <- expandRange a b            -- A-tagged: the REAL widener
        return e
    """
    reversed_ = v1 < v0
    a = v1 if reversed_ else v0
    b = v0 if reversed_ else v1
    return expand_ascending(a, b)


def default_nonsingular(v0, v1):
    """The `pure` function `defaultMemberPair` from Solution.lean."""
    return expand_ascending(v1, v0) if v1 < v0 else expand_ascending(v0, v1)


def member_spec_violations(v0, v1, out):
    """P1..P4 of `defaultMemberAdjust`, evaluated on a reported pair `out`."""
    bad = []
    ref = default_nonsingular(v0, v1)
    if out != ref:                                                    # P1
        bad.append(("P1 out = defaultMemberPair e0 e1", ref))
    if v1 < v0 and out != expand_ascending(v1, v0):                   # P2
        bad.append(("P2 v1 < v0 -> out = expandAscending v1 v0",
                    expand_ascending(v1, v0)))
    if not (v1 < v0) and out != expand_ascending(v0, v1):             # P3
        bad.append(("P3 not (v1 < v0) -> out = expandAscending v0 v1",
                    expand_ascending(v0, v1)))
    if ref[0] <= ref[1] and not (out[0] <= out[1]):                   # P4
        bad.append(("P4 ref ordered -> out.1 <= out.2", None))
    return bad


def _mrival_restores_order(v0, v1):
    reversed_ = v1 < v0
    a = v1 if reversed_ else v0
    b = v0 if reversed_ else v1
    e = expand_ascending(a, b)
    return (e[1], e[0]) if reversed_ else (e[0], e[1])


def _mrival_swap_always(v0, v1):
    e = shadow_member(v0, v1)
    return (e[1], e[0])


def _mrival_degenerate_raw(v0, v1):
    if v0 == v1:
        return (v0, v1)
    return shadow_member(v0, v1)


def _mrival_echo_sibling(v0, v1):
    """Answers with the SIBLING operation's reference expression. Needs an axis,
    so it is evaluated against the linear default axis the caller-side sweep
    already builds; `committed_limits` supplies the per-scale chain."""
    return None            # supplied per-observation by main() (needs an axis)


MEMBER_RIVALS = [
    ("reject-member-restores-order", _mrival_restores_order),
    ("reject-member-swap-always", _mrival_swap_always),
    ("reject-member-degenerate-raw", _mrival_degenerate_raw),
]


def _mpos_branch_select(v0, v1):
    if v1 < v0:
        return expand_ascending(v1, v0)
    return expand_ascending(v0, v1)


def _mpos_pure_reference(v0, v1):
    return default_nonsingular(v0, v1)


MEMBER_POSITIVES = [
    ("pos-member-branch-select", _mpos_branch_select),
    ("pos-member-pure-reference", _mpos_pure_reference),
]


def compose(lo, hi, axis, *, member, restore):
    """The whole modeled composition, with either half independently reverted.

    `member` is the default normalizer member (post-patch or pre-patch) and
    `restore` says whether the caller reinstates the requested orientation. The
    gold patch is (post-patch member, restore=True); base_commit is (pre-patch
    member, restore=False).
    """
    swapped = lo > hi
    a, b = member(lo, hi)
    a, b = axis.limit_range_for_scale(a, b)
    return (b, a) if (restore and swapped) else (a, b)


def _member_prepatch(v0, v1):
    """The base member AT base_commit: sort, widen, then un-sort."""
    return expand_ascending_prepatch(v0, v1)


def check_halves_independent(axis):
    """HARD ASSERTION: each half of the gold patch is load-bearing ALONE.

    Returns (rows, failures). The linear pre-existing legs of the failing test
    must come back verbatim under the gold pair of halves, and must NOT under
    either single half -- which is the executable form of "the ticker.py hunk is
    independently observable", the claim the previous revision of this bundle got
    wrong in prose and which let a verifying-but-unresolving refinement through.
    """
    rows, bad = [], []
    for lo, hi in ((4.0, -5.0), (5.0, -3.0), (10.0, 1.0)):
        cell = {}
        for tag, member, restore in (
                ("gold (both halves)", real_member, True),
                ("caller half only", _member_prepatch, True),
                ("callee half only", real_member, False),
                ("base_commit (neither)", _member_prepatch, False)):
            cell[tag] = compose(lo, hi, axis, member=member, restore=restore)
        rows.append(((lo, hi), cell))
        if cell["gold (both halves)"] != (lo, hi):
            bad.append(("gold", (lo, hi), cell["gold (both halves)"]))
        if cell["caller half only"] == (lo, hi):
            bad.append(("caller-half-alone-suffices", (lo, hi),
                        cell["caller half only"]))
        if cell["callee half only"] == (lo, hi):
            bad.append(("callee-half-alone-suffices", (lo, hi),
                        cell["callee half only"]))
    return rows, bad


# ==========================================================================
# probe inputs
# ==========================================================================
STRUCTURED = [
    (10.0, 1.0), (1.0, 10.0), (7.0, 3.0), (3.0, 7.0), (3.0, 2.0), (2.0, 3.0),
    (4.0, -5.0), (5.0, -3.0), (-5.0, 4.0), (-3.0, 5.0), (-1.0, -5.0),
    (-5.0, -1.0), (0.0, 0.0), (3.0, 3.0), (4.0, 4.0), (5.0, 5.0), (2.0, 7.0),
    (0.0, 1.0), (1.0, 0.0), (1e-3, 1e3), (1e3, 1e-3), (0.9, 0.1), (0.1, 0.9),
    (737577.0, 737425.0), (737425.0, 737577.0), (1.0000001, 1.0),
    (123.456, 123.456), (-0.5, 0.5), (0.5, -0.5),
]


def fuzz_pairs(rng, n):
    out = []
    for _ in range(n):
        lo = rng.uniform(-1e6, 1e6)
        hi = rng.uniform(-1e6, 1e6)
        r = rng.random()
        if r < 0.10:
            lo = 10.0 ** rng.uniform(-9, 9)
            hi = 10.0 ** rng.uniform(-9, 9)
        elif r < 0.16:
            lo = -(10.0 ** rng.uniform(-9, 9))
            hi = 10.0 ** rng.uniform(-9, 9)
        if rng.random() < 0.04:
            hi = lo
        if rng.random() < 0.10:            # dense in (0, 1): the logit domain
            lo, hi = rng.random(), rng.random()
        out.append((lo, hi))
    return out


# ==========================================================================
# the run
# ==========================================================================
def main():
    rng = random.Random(SEED)
    warnings.simplefilter("ignore")

    disagreements = []          # shadow vs oracle
    spec_bad = []               # a spec clause false of the REAL committed pair
    pos_bad = []                # a battery positive differing from gold
    checks_block = 0
    checks_e2e = 0
    sites_seen = set()
    members_seen = set()
    rival_split = {tag: None for tag, _ in RIVALS}
    uncond_counterexamples = []

    def observe(axis, lo, hi, real=None, where=""):
        """One observation. `real` is ORACLE-A's committed pair when we have it."""
        nonlocal checks_block, checks_e2e
        n = real_normalize(axis, lo, hi)
        s = shadow_commit(axis, lo, hi)
        b = oracle_block(axis, lo, hi)
        checks_block += 1
        if s != b:
            disagreements.append((where, lo, hi, s, b, "block"))
        if real is not None:
            checks_e2e += 1
            if s != tuple(real):
                disagreements.append((where, lo, hi, s, tuple(real), "e2e"))
        # the six ensures, on the REAL committed pair when available
        target = tuple(real) if real is not None else b
        for clause, want in spec_violations(lo, hi, n, target):
            spec_bad.append((where, lo, hi, n, target, clause, want))
        # the UNCONDITIONAL order claim this file used to assert, on real output
        if lo > hi and not (target[1] <= target[0]):
            if len(uncond_counterexamples) < 6:
                uncond_counterexamples.append((where, lo, hi, n, target))
        # rivals must disagree with gold somewhere; positives never may
        for tag, fn in RIVALS:
            if rival_split[tag] is None:
                try:
                    r = fn(axis, lo, hi, n)
                except Exception:
                    continue
                if r != target:
                    rival_split[tag] = (where, lo, hi, r, target)
        for tag, fn in POSITIVES:
            if fn(axis, lo, hi, n) != target:
                pos_bad.append((tag, where, lo, hi, target))

    # ---- ORACLE-A: the five real patched setters, fresh axis per request ----
    for site in SITES:
        for member in MEMBERS:
            built = make(site, member)
            if built is None:
                continue
            plt.close("all")
            where = "%s [%s]" % (site[0], member[0])
            for lo, hi in STRUCTURED:
                built = make(site, member)
                if built is None:
                    break
                fig, axis, setter = built
                try:
                    req = upstream_request(axis, lo, hi, log_guard=site[4])
                    real = setter(lo, hi)
                    if not all(math.isfinite(v) for v in real):
                        disagreements.append(
                            (where, lo, hi, None, tuple(real), "non-finite"))
                        continue
                    observe(axis, req[0], req[1], real=real, where=where)
                finally:
                    plt.close(fig)
            sites_seen.add(site[0])
            members_seen.add(member[0])

    # ---- ORACLE-A, volume: reuse one axis, state read fresh each request ----
    e2e_fuzz = fuzz_pairs(rng, 400)
    for site in SITES:
        for member in MEMBERS:
            built = make(site, member)
            if built is None:
                continue
            fig, axis, setter = built
            where = "%s [%s] fuzz" % (site[0], member[0])
            try:
                for lo, hi in e2e_fuzz:
                    req = upstream_request(axis, lo, hi, log_guard=site[4])
                    real = setter(lo, hi)
                    if not all(math.isfinite(v) for v in real):
                        disagreements.append(
                            (where, lo, hi, None, tuple(real), "non-finite"))
                        continue
                    observe(axis, req[0], req[1], real=real, where=where)
            finally:
                plt.close(fig)

    # ---- ORACLE-B: the >=1e5-input fuzz, every member ----
    block_fuzz = fuzz_pairs(rng, 12000)
    for member in MEMBERS:
        built = make(SITES[1], member)          # Axes.set_ylim's axis
        if built is None:
            continue
        fig, axis, _setter = built
        where = "block [%s]" % member[0]
        try:
            for lo, hi in STRUCTURED + block_fuzz:
                observe(axis, lo, hi, real=None, where=where)
        finally:
            plt.close(fig)

    # ---- the pinned fail-to-pass leg: LOG axis, (10, 1) commits (10, 1) ----
    # (test_axes.py::test_inverted_limits, the leg test_patch adds. Pre-patch
    # LogLocator.nonsingular sorted this to (1, 10) and nothing swapped back.)
    f2p_bad = []
    f2p_sites = []
    for site in SITES:
        built = make(site, ("log/LogLocator", _cfg_log))
        if built is None:
            continue                            # scale not settable at this site
        fig, _axis, setter = built
        try:
            got = tuple(setter(10.0, 1.0))
        finally:
            plt.close(fig)
        f2p_sites.append(site[0])
        if got != (10.0, 1.0):
            f2p_bad.append((site[0], "log", (10.0, 1.0), got))
    if not set(("Axes.set_xlim", "Axes.set_ylim")) <= set(f2p_sites):
        f2p_bad.append(("Axes.set_xlim/set_ylim", "log", (10.0, 1.0),
                        "log scale not exercised at the 2D sites"))

    # ---- the pinned regression legs: LINEAR axis, descending pair verbatim ----
    for site in SITES:
        for lo, hi in ((4.0, -5.0), (5.0, -3.0)):
            built = make(site, MEMBERS[0])      # linear axis, default locator
            if built is None:
                f2p_bad.append((site[0], "linear", (lo, hi), "site unavailable"))
                continue
            fig, _axis, setter = built
            try:
                got = tuple(setter(lo, hi))
            finally:
                plt.close(fig)
            if got != (lo, hi):
                f2p_bad.append((site[0], "linear", (lo, hi), got))

    undiscriminated = [t for t, v in rival_split.items() if v is None]

    # ---------------------------------------------------------------------
    # THE SECOND OPERATION: shadow vs the real patched member, its four
    # clauses, its rivals and positives, and the load-bearing-halves table.
    # ---------------------------------------------------------------------
    m_disagree, m_spec_bad, m_pos_bad = [], [], []
    m_checks = 0
    m_split = {tag: None for tag, _ in MEMBER_RIVALS}
    m_split["reject-member-echo-sibling"] = None
    member_points = STRUCTURED + fuzz_pairs(rng, 6000)
    for v0, v1 in member_points:
        m_checks += 1
        want = real_member(v0, v1)
        got = shadow_member(v0, v1)
        if got != want:
            m_disagree.append((v0, v1, got, want))
            continue
        for clause, exp in member_spec_violations(v0, v1, want):
            m_spec_bad.append((v0, v1, want, clause, exp))
        for tag, fn in MEMBER_RIVALS:
            if m_split[tag] is None and fn(v0, v1) != want:
                m_split[tag] = (v0, v1, fn(v0, v1), want)
        for tag, fn in MEMBER_POSITIVES:
            if fn(v0, v1) != want:
                m_pos_bad.append((tag, v0, v1, want))

    # the cross-operation echo rival needs an axis (it answers with the SIBLING
    # operation's reference expression, which consults the per-scale chain).
    for member in MEMBERS:
        if m_split["reject-member-echo-sibling"] is not None:
            break
        built = make(SITES[1], member)
        if built is None:
            continue
        fig, axis, _setter = built
        try:
            for v0, v1 in STRUCTURED:
                echo = committed_limits(axis, v0, v1)
                if echo != real_member(v0, v1):
                    m_split["reject-member-echo-sibling"] = (
                        v0, v1, echo, real_member(v0, v1))
                    break
        finally:
            plt.close(fig)
    m_undiscriminated = [t for t, v in m_split.items() if v is None]

    fig_h, ax_h = plt.subplots()
    try:
        halves_rows, halves_bad = check_halves_independent(ax_h.yaxis)
    finally:
        plt.close(fig_h)

    # ---------------------------------------------------------------- verdict
    fatal = False
    if disagreements:
        fatal = True
        print("G-CONF FAIL: %d shadow/oracle disagreement(s) in %d block + %d "
              "end-to-end observations. First few:"
              % (len(disagreements), checks_block, checks_e2e))
        for where, lo, hi, s, o, kind in disagreements[:10]:
            print("  - %s commit(%r, %r): shadow=%s oracle(%s)=%s"
                  % (where, lo, hi, s, kind, o))
    if spec_bad:
        fatal = True
        print("G-CONF FAIL: %d spec-clause violation(s) -- an `ensures` of "
              "commitLimits is FALSE of the real patched code. First few:"
              % len(spec_bad))
        for where, lo, hi, n, out, clause, want in spec_bad[:10]:
            print("  - %s request(%r, %r): normalize=%s committed=%s violates %s"
                  "%s" % (where, lo, hi, n, out, clause,
                          "" if want is None else " (wanted %s)" % (want,)))
    if pos_bad:
        fatal = True
        print("G-CONF FAIL: %d battery POSITIVE(s) differ from gold behaviour -- "
              "an `expect: accept` case is not gold-equivalent. First few:"
              % len(pos_bad))
        for tag, where, lo, hi, out in pos_bad[:10]:
            print("  - %s at %s request(%r, %r), gold committed %s"
                  % (tag, where, lo, hi, out))
    if undiscriminated:
        fatal = True
        print("G-CONF FAIL: battery rival(s) never disagreed with the real "
              "patched code over the whole swept domain, so G-PBT is rejecting "
              "them for no behavioural reason: %s" % ", ".join(undiscriminated))
    if not uncond_counterexamples:
        fatal = True
        print("G-CONF FAIL: no member of the callee family refutes the "
              "UNCONDITIONAL order claim (`lo > hi` -> committed descending). "
              "Q4/Q5/Q6 condition on the normalizer's reported order; if that "
              "conditioning is unnecessary the clauses are weaker than the code "
              "permits and must be strengthened to the unconditional form.")
    if f2p_bad:
        fatal = True
        print("G-CONF FAIL: the fail-to-pass / regression behaviour is not what "
              "the spec pins: %s" % (f2p_bad[:6],))
    if not (len(sites_seen) == len(SITES)):
        fatal = True
        print("G-CONF FAIL: only %d of %d patched call sites were exercised: %s"
              % (len(sites_seen), len(SITES), sorted(sites_seen)))
    if m_disagree:
        fatal = True
        print("G-CONF FAIL: %d disagreement(s) between the shadow of "
              "`defaultMemberAdjust` and the REAL patched `Locator.nonsingular` "
              "over %d observations. First few:" % (len(m_disagree), m_checks))
        for v0, v1, g, w in m_disagree[:10]:
            print("  - member(%r, %r): shadow=%s real=%s" % (v0, v1, g, w))
    if m_spec_bad:
        fatal = True
        print("G-CONF FAIL: %d clause violation(s) -- an `ensures` of "
              "defaultMemberAdjust is FALSE of the real patched member. First few:"
              % len(m_spec_bad))
        for v0, v1, out, clause, exp in m_spec_bad[:10]:
            print("  - member(%r, %r) = %s violates %s%s"
                  % (v0, v1, out, clause,
                     "" if exp is None else " (wanted %s)" % (exp,)))
    if m_pos_bad:
        fatal = True
        print("G-CONF FAIL: %d second-operation POSITIVE(s) differ from the real "
              "member: %s" % (len(m_pos_bad), m_pos_bad[:6]))
    if m_undiscriminated:
        fatal = True
        print("G-CONF FAIL: second-operation rival(s) never disagreed with the "
              "real patched member, so G-PBT is rejecting them for no "
              "behavioural reason: %s" % ", ".join(m_undiscriminated))
    if halves_bad:
        fatal = True
        print("G-CONF FAIL: the two halves of the gold patch are NOT each "
              "load-bearing, so modeling them as two operations with two "
              "prepatch twins is not justified by the code: %s" % (halves_bad,))

    report = {
        "band": "order-only+exact-value",
        "shadow": "commitLimits do-block (transliterated)",
        "oracle_a": "real patched setters: %s" % ", ".join(s[0] for s in SITES),
        "oracle_b": "patched commit block (transliterated verbatim)",
        "inputs_block": checks_block,
        "inputs_end_to_end": checks_e2e,
        "members": len(members_seen),
        "disagreements": len(disagreements),
        "spec_clause_violations": len(spec_bad),
        "rivals_discriminated": len(RIVALS) - len(undiscriminated),
        "positives_agreeing": len(POSITIVES) - len(set(t for t, *_ in pos_bad)),
        "unconditional_order_refutations": len(uncond_counterexamples),
        "f2p_log_sites": f2p_sites,
        "shadow_2": "defaultMemberAdjust do-block (transliterated)",
        "oracle_2": "real patched ticker.Locator.nonsingular",
        "inputs_member": m_checks,
        "member_disagreements": len(m_disagree),
        "member_clause_violations": len(m_spec_bad),
        "member_rivals_discriminated": len(m_split) - len(m_undiscriminated),
        "member_positives_agreeing":
            len(MEMBER_POSITIVES) - len(set(t for t, *_ in m_pos_bad)),
        "halves_independently_observable": not halves_bad,
        "unsupported": [],
    }
    print(json.dumps(report, sort_keys=True))

    if fatal:
        sys.exit(1)

    ce = uncond_counterexamples[0]
    print("G-CONF OK: the transliterated shadow of `commitLimits` agrees with "
          "the real gold-patched code on %d observations (%d of them END-TO-END "
          "against the five patched setters themselves, %d against the "
          "verbatim block), over %d members of the (scale x major locator) "
          "callee family, seed=%d, 0 disagreements. All six `ensures` hold of "
          "matplotlib's own committed pair at every end-to-end observation. The "
          "conditioning in Q4/Q5/Q6 is FORCED: at %s the request (%r, %r) is "
          "descending, the normalizer reports %s (descending, it does not sort), "
          "and the patched code commits %s -- ASCENDING -- so the unconditional "
          "order claim is false of the real code and only the reported-order "
          "hypothesis makes the clause true. The fail-to-pass leg is pinned (a "
          "LOG axis asked for (10, 1) commits (10, 1) at %d site(s): %s) and so "
          "are the regression legs ((4, -5) and (5, -3) come back verbatim on a "
          "linear axis at all five sites). All %d falsification rivals disagree "
          "with the real code somewhere in the swept domain and all %d positives "
          "agree with it everywhere."
          % (checks_block + checks_e2e, checks_e2e, checks_block,
             len(members_seen), SEED, ce[0], ce[1], ce[2], ce[3], ce[4],
             len(f2p_sites), ", ".join(f2p_sites),
             len(RIVALS), len(POSITIVES)))

    print("G-CONF OK (second operation): the transliterated shadow of "
          "`defaultMemberAdjust` agrees with the REAL patched "
          "`ticker.Locator.nonsingular` on %d observations (boundary set + 6000 "
          "fuzzed pairs), 0 disagreements; all four `ensures` (P1-P4) hold of the "
          "real member's own output at every one of them; its %d rivals each "
          "disagree with it somewhere and its %d positives agree everywhere."
          % (m_checks, len(m_split), len(MEMBER_POSITIVES)))
    print("G-CONF OK (both halves load-bearing): with either half of the gold "
          "patch reverted, the failing test's own PRE-EXISTING linear legs break. "
          "Measured on a linear default-locator axis:")
    for (lo, hi), cell in halves_rows:
        print("    request (%r, %r): gold=%s | caller half only=%s | callee half "
              "only=%s | base_commit=%s"
              % (lo, hi, cell["gold (both halves)"], cell["caller half only"],
                 cell["callee half only"], cell["base_commit (neither)"]))
    print("  So neither hunk is decoration: the caller-side restore is correct "
          "ONLY because the member stopped restoring, and vice versa. That is why "
          "the spec models TWO operations with TWO prepatch twins, and it is the "
          "claim the previous revision of this bundle asserted the OPPOSITE of in "
          "prose -- which is how a refinement that implements the commit block "
          "exactly and leaves ticker.py at base_commit verified while not "
          "resolving.")
    sys.exit(0)


if __name__ == "__main__":
    main()
