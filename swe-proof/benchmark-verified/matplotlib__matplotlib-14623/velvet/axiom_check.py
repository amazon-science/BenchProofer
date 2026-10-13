#!/usr/bin/env python3
"""G-AX soundness check for matplotlib__matplotlib-14623 (velvet).

Validates the TWO consumed axioms of the bundle:

    Solution.lean:   axiom normalize       : Endpoint -> Endpoint
                                             -> Endpoint x Endpoint
    Solution.lean:   axiom expandAscending : Endpoint -> Endpoint
                                             -> Endpoint x Endpoint

Both are BARE FUNCTION TYPES. The second one appeared when the callee-side half
of the gold patch was modeled as a second operation, `defaultMemberAdjust`
(ticker.py `Locator.nonsingular`): that member sorts its two arguments and then
applies the shared range widener `matplotlib.transforms.nonsingular(..., expander
= .05)` to the ascending pair, and `expandAscending` is exactly that widener.
Sections E-H below are its validation; A-D validate `normalize`.

`normalize` models the axis-normalizer chain the limit setter consults between
receiving a requested endpoint pair and committing it (mapping.md 3.1):

    lo, hi = axis.get_major_locator().nonsingular(lo, hi)
    lo, hi = axis.limit_range_for_scale(lo, hi)

WHAT THE AXIOM ASSERTS, EXACTLY. It is a bare function type. It says the chain is
a TOTAL FUNCTION of the two requested endpoints -- for the axis at hand it always
answers, always with a pair of two finite endpoints, and it answers the same way
every time it is asked the same question. It asserts NOTHING about the values it
returns and -- load-bearing -- NOTHING about the ORDER it returns them in.

WHY THE ORDER CLAUSE IS GONE (this bundle previously carried an axiom
`normalize_ascending` saying the chain always reports ascending). The chain is a
FAMILY, one member per (scale, major-locator) pair, and its members DISAGREE
about ordering. After the patch `Locator.nonsingular` canonicalizes to ascending
(ticker.py:1523-1524 is part of the gold patch), and `LogLocator` /
`LogitLocator` already did -- but `matplotlib.dates.DateLocator.nonsingular`
never sorts, so a date axis hands a descending request straight back descending.
An axiom asserting ascending is therefore FALSE of the real patched callee, and
worse, it handed the operation under spec a fact it is not entitled to. So the
spec now treats the reported order as an OBSERVABLE: the orientation clauses of
`commitLimits` take it as a HYPOTHESIS about the pair returned on this call. This
checker's job is correspondingly (A) to establish the functionality the bare
axiom does assert, and (B) to MEASURE the order disagreement, so that "the order
is unconstrained" is a recorded fact about the real code rather than a
convenience.

THE CALLEE IS PATCHED, so this probe runs on the PATCHED tree
(`ax_apply_gold: true` in meta.json). `ticker.py` `Locator.nonsingular` is one of
the three files the gold patch touches; validating at base_commit would validate
a DIFFERENT function from the one the patched operation consults. Every claim
below is nonetheless written to hold on either tree (each realisability claim is
satisfied by SOME member of the family on both sides of the patch), and the
script prints which tree it observed.

WHAT IS CHECKED (all four are hard assertions; exit 0 iff all hold):

  A. FUNCTIONALITY / DETERMINISM. For every member of the family and every probe
     request: asking twice gives the same pair; asking again after other requests
     have been interleaved gives the same pair (no hidden state in the locator);
     and a freshly constructed, identically configured axis gives the same pair.
     This is the whole content of
     `axiom normalize : Endpoint -> Endpoint -> Endpoint x Endpoint`.

  B. TOTALITY over the carrier. The operation under spec has NO precondition, so
     the modeled callee must answer for every requested pair the carrier admits.
     Fuzzed + boundary requests of either sign, in either order, degenerate
     included, on every member: no exception, and both returned endpoints finite.
     (A log-scaled axis fed a non-positive endpoint clamps it to the scale's
     positive floor and warns; it does not fail. That is exactly why the
     `require 0 < lo` / `require 0 < hi` this bundle used to carry was
     unfaithful: the setter really does receive such requests.)

  C. ORDER CENSUS. At one and the same descending request, some member reports
     its pair ascending and some member reports it descending. This is the
     executable refutation of the deleted `normalize_ascending` axiom.

  D. REALISABILITY of every conditioning hypothesis the G-PBT battery's
     refutation witnesses rest on (properties.py, WITNESS-POINT DISCIPLINE). A
     hypothesis about an opaque callee is satisfiable in Lean for almost
     anything, so each witness point is only honest if some member of the real
     family satisfies it. Each is asserted here against a member, and the member
     that realises it is printed.

  E. FUNCTIONALITY / DETERMINISM / TOTALITY of `expandAscending`, i.e. of
     `mtransforms.nonsingular(a, b, expander=.05)`: it answers for every pair the
     carrier admits (ascending, descending, degenerate, either sign, extreme
     magnitudes), always with a pair of finite endpoints, always the same answer
     for the same arguments, and with no dependence on any axis or locator state
     (it is a module-level function of its arguments alone -- asked from three
     unrelated call orders it answers identically). That is the entire content of
     `axiom expandAscending : Endpoint -> Endpoint -> Endpoint x Endpoint`.

  F. THE TICKER HUNK IS INDEPENDENTLY OBSERVABLE (hard assertion). The gold patch
     drops `increasing=False` from the base member. Both expressions are
     evaluated here -- the post-patch `nonsingular(v0, v1, expander=.05)` and the
     pre-patch `nonsingular(v0, v1, increasing=False, expander=.05)` -- and they
     are asserted to DISAGREE on a reversed request. If they ever agreed
     everywhere, the second modeled operation would be unobservable and modeling
     it would be decoration; the previous revision of this bundle asserted
     exactly that in prose and it was WRONG, so the claim is now executable.

  G. THE WIDENER IS SYMMETRIC (hard assertion, and it is a constraint ON THE
     BATTERY). `nonsingular` sorts its arguments internally
     (transforms.py:2807-2809) and, post-patch, never un-sorts, so
     `expandAscending a b == expandAscending b a` for every probe pair. This is
     recorded because it is the reason a whole family of attractive rivals (sort
     the wrong way round / sort descending / gate the sort) is NOT shipped in
     properties.py: refuting them needs a hypothesis this measurement shows to be
     FALSE of the real callee.

  H. REALISABILITY of the four conditioning hypotheses the second operation's
     witnesses rest on, exactly as D does for the first.

Imports only matplotlib (+ stdlib). No exact endpoint value is pinned by either
axiom; the values printed are provenance, not obligations.
"""
import math
import random
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.transforms as mtransforms


# --------------------------------------------------------------------------
# the modeled callee, and the family of axes it is instantiated on
# --------------------------------------------------------------------------
def normalize_real(ax, lo, hi):
    """The REAL axis-normalizer chain (mapping.md 3.1), on ax's y-axis."""
    lo, hi = ax.yaxis.get_major_locator().nonsingular(lo, hi)
    lo, hi = ax.yaxis.limit_range_for_scale(lo, hi)
    return lo, hi


def _plain():
    fig, ax = plt.subplots()
    return fig, ax


def _log():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    return fig, ax


def _symlog():
    fig, ax = plt.subplots()
    ax.set_yscale("symlog")
    return fig, ax


def _logit():
    fig, ax = plt.subplots()
    ax.set_yscale("logit")
    return fig, ax


def _log_fixed():
    fig, ax = plt.subplots()
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(mticker.FixedLocator([1, 2, 3]))
    return fig, ax


def _date():
    fig, ax = plt.subplots()
    ax.yaxis.set_major_locator(mdates.AutoDateLocator())
    return fig, ax


def _multiple():
    fig, ax = plt.subplots()
    ax.yaxis.set_major_locator(mticker.MultipleLocator(2))
    return fig, ax


def _maxn():
    fig, ax = plt.subplots()
    ax.yaxis.set_major_locator(mticker.MaxNLocator(4))
    return fig, ax


def _null():
    fig, ax = plt.subplots()
    ax.yaxis.set_major_locator(mticker.NullLocator())
    return fig, ax


# Every member is a (scale, major locator) pair the same commit block is reached
# with. The `normalize` axiom is instantiated per call, i.e. per member.
MEMBERS = [
    ("linear/AutoLocator", _plain),
    ("log/LogLocator", _log),
    ("symlog/SymmetricalLogLocator", _symlog),
    ("logit/LogitLocator", _logit),
    ("log/FixedLocator", _log_fixed),
    ("linear/AutoDateLocator", _date),
    ("linear/MultipleLocator", _multiple),
    ("linear/MaxNLocator", _maxn),
    ("linear/NullLocator", _null),
]

# Requests used by the battery's witnesses, plus boundary shapes.
PROBE_POINTS = [
    (10.0, 1.0), (1.0, 10.0), (7.0, 3.0), (3.0, 7.0), (3.0, 2.0),
    (4.0, -5.0), (5.0, -3.0), (-5.0, 4.0), (-1.0, -5.0), (-5.0, -1.0),
    (0.0, 0.0), (3.0, 3.0), (4.0, 4.0), (5.0, 5.0), (2.0, 7.0),
    (0.0, 1.0), (1.0, 0.0), (1e-300, 1.0), (1e300, 1.0), (5e-324, 5e-324),
    (0.9, 0.1), (0.1, 0.9), (737577.0, 737425.0), (737425.0, 737577.0),
]

errors = []
notes = []


def fail(msg):
    errors.append(msg)


# --------------------------------------------------------------------------
# A. functionality / determinism, and B. totality
# --------------------------------------------------------------------------
def check_functionality_and_totality(rng):
    checks = 0
    fuzz = []
    for _ in range(4000):
        lo = rng.uniform(-1e6, 1e6)
        hi = rng.uniform(-1e6, 1e6)
        if rng.random() < 0.05:
            hi = lo
        if rng.random() < 0.10:
            lo = 10.0 ** rng.uniform(-320, 300)
            hi = 10.0 ** rng.uniform(-320, 300)
        if rng.random() < 0.05:
            lo, hi = -lo, -hi
        fuzz.append((lo, hi))

    for tag, build in MEMBERS:
        fig, ax = build()
        try:
            for lo, hi in PROBE_POINTS + fuzz:
                checks += 1
                try:
                    first = normalize_real(ax, lo, hi)
                except Exception as exc:                       # B: totality
                    fail(f"TOTALITY[{tag}] normalize({lo!r}, {hi!r}) raised "
                         f"{type(exc).__name__}: {exc}")
                    continue
                if len(first) != 2 or not all(math.isfinite(v) for v in first):
                    fail(f"TOTALITY[{tag}] normalize({lo!r}, {hi!r}) = {first!r} "
                         f"is not a pair of finite endpoints")
                    continue
                again = normalize_real(ax, lo, hi)             # A: determinism
                if again != first:
                    fail(f"FUNCTIONALITY[{tag}] normalize({lo!r}, {hi!r}) gave "
                         f"{first!r} then {again!r} on the SAME axis")
                # interleave an unrelated request, then re-ask: no hidden state
                normalize_real(ax, -12345.0, 6789.0)
                normalize_real(ax, 2.5, 2.5)
                third = normalize_real(ax, lo, hi)
                if third != first:
                    fail(f"FUNCTIONALITY[{tag}] normalize({lo!r}, {hi!r}) gave "
                         f"{first!r}, then {third!r} after other requests "
                         f"(hidden state in the locator)")
        finally:
            plt.close(fig)

        # a freshly built, identically configured axis answers identically
        fig2, ax2 = build()
        try:
            for lo, hi in PROBE_POINTS:
                fig3, ax3 = build()
                try:
                    a, b = normalize_real(ax2, lo, hi), normalize_real(ax3, lo, hi)
                finally:
                    plt.close(fig3)
                checks += 1
                if a != b:
                    fail(f"FUNCTIONALITY[{tag}] normalize({lo!r}, {hi!r}) = {a!r} "
                         f"on one axis but {b!r} on a fresh identical axis")
        finally:
            plt.close(fig2)
    return checks


# --------------------------------------------------------------------------
# C. order census  and  D. witness-point realisability
# --------------------------------------------------------------------------
def at(tag_build, lo, hi):
    _tag, build = tag_build
    fig, ax = build()
    try:
        return normalize_real(ax, lo, hi)
    finally:
        plt.close(fig)


def find_member(pred):
    """First member of the family satisfying pred(lambda lo,hi: pair), or None."""
    for tag, build in MEMBERS:
        def call(lo, hi, _b=build):
            return at((tag, _b), lo, hi)
        try:
            if pred(call):
                return tag
        except Exception:
            continue
    return None


def check_order_census():
    asc = find_member(lambda f: f(10.0, 1.0)[0] < f(10.0, 1.0)[1])
    desc = find_member(lambda f: f(10.0, 1.0)[1] < f(10.0, 1.0)[0])
    if asc is None:
        fail("ORDER CENSUS: no member reports (10,1) ascending")
    if desc is None:
        fail("ORDER CENSUS: no member reports (10,1) descending -- the deleted "
             "`normalize_ascending` axiom would then be UNREFUTED, and treating "
             "the reported order as an unconstrained observable would be "
             "gratuitous rather than forced")
    if asc and desc:
        notes.append(
            f"ORDER CENSUS: at the SAME descending request (10,1), member "
            f"{asc!r} reports {at((asc, dict(MEMBERS)[asc]), 10.0, 1.0)!r} "
            f"(ascending) while member {desc!r} reports "
            f"{at((desc, dict(MEMBERS)[desc]), 10.0, 1.0)!r} (descending). The "
            f"reported ORDER is therefore not a property of the callee, which is "
            f"why the spec takes it as a hypothesis (Q4/Q5/Q6) and pins only the "
            f"pair's identity (Q1/Q2/Q3).")


# Every conditioning hypothesis the G-PBT witnesses rest on, as a predicate over
# one member of the family. (case id, human form, predicate)
WITNESS_FACTS = [
    ("reject-no-restore", "(normalize 10 1).1 != (normalize 10 1).2",
     lambda f: f(10.0, 1.0)[0] != f(10.0, 1.0)[1]),
    ("reject-cmp-lt", "(normalize 7 3).1 != (normalize 7 3).2",
     lambda f: f(7.0, 3.0)[0] != f(7.0, 3.0)[1]),
    ("reject-cmp-ge", "(normalize 5 5).1 != (normalize 5 5).2",
     lambda f: f(5.0, 5.0)[0] != f(5.0, 5.0)[1]),
    ("reject-always-swap", "(normalize 1 10).1 != (normalize 1 10).2",
     lambda f: f(1.0, 10.0)[0] != f(1.0, 10.0)[1]),
    ("reject-partial-no-expand", "(normalize 3 3).1 != 3",
     lambda f: f(3.0, 3.0)[0] != 3.0),
    ("reject-equal-raw", "(normalize 4 4).1 != 4",
     lambda f: f(4.0, 4.0)[0] != 4.0),
    ("reject-positivity-gate", "(normalize 4 (-5)).1 != (normalize 4 (-5)).2",
     lambda f: f(4.0, -5.0)[0] != f(4.0, -5.0)[1]),
    ("reject-postcall-flag", "(normalize 10 1).1 < (normalize 10 1).2",
     lambda f: f(10.0, 1.0)[0] < f(10.0, 1.0)[1]),
    ("reject-ascending-gate", "(normalize 10 1).2 < (normalize 10 1).1",
     lambda f: f(10.0, 1.0)[1] < f(10.0, 1.0)[0]),
    ("reject-canonicalize", "(normalize 10 1).2 < (normalize 10 1).1",
     lambda f: f(10.0, 1.0)[1] < f(10.0, 1.0)[0]),
    ("reject-echo-transposed", "(normalize 1 10).1 != (normalize 10 1).2",
     lambda f: f(1.0, 10.0)[0] != f(10.0, 1.0)[1]),
]


def check_witness_realisability():
    for case, form, pred in WITNESS_FACTS:
        who = find_member(pred)
        if who is None:
            fail(f"WITNESS POINT [{case}]: no member of the real callee family "
                 f"satisfies {form} -- the witness would refute its rival only "
                 f"at an input the carrier never realises")
        else:
            notes.append(f"WITNESS POINT [{case}]: {form} -- realised by member "
                         f"{who!r}")


# --------------------------------------------------------------------------
# E-H. the SECOND axiom: `expandAscending`, the shared range widener the
#      default normalizer member applies to its sorted arguments
# --------------------------------------------------------------------------
def expand_real(a, b):
    """The REAL widener: post-patch `Locator.nonsingular`'s call, verbatim.

    ticker.py post-patch: `return mtransforms.nonsingular(v0, v1, expander=.05)`.
    """
    return mtransforms.nonsingular(a, b, expander=.05)


def expand_prepatch(a, b):
    """The SAME call at base_commit: `increasing=False` still present.

    transforms.py:2840-2841 (`if swapped and not increasing: vmin, vmax = vmax,
    vmin`) is the only step of `nonsingular` that reads `increasing`, so this is
    the pre-patch member's whole behavioural difference.
    """
    return mtransforms.nonsingular(a, b, increasing=False, expander=.05)


def member_real(v0, v1):
    """The REAL default normalizer member, i.e. the second modeled operation."""
    return mticker.Locator().nonsingular(v0, v1)


def check_widener_axiom(rng):
    """E: functionality / determinism / totality of `expandAscending`."""
    checks = 0
    pts = list(PROBE_POINTS)
    for _ in range(4000):
        a = rng.uniform(-1e6, 1e6)
        b = rng.uniform(-1e6, 1e6)
        if rng.random() < 0.08:
            b = a
        if rng.random() < 0.10:
            a = 10.0 ** rng.uniform(-320, 300)
            b = 10.0 ** rng.uniform(-320, 300)
        pts.append((a, b))
    for a, b in pts:
        checks += 1
        try:
            first = expand_real(a, b)
        except Exception as exc:
            fail(f"TOTALITY[expandAscending] nonsingular({a!r}, {b!r}, "
                 f"expander=.05) raised {type(exc).__name__}: {exc}")
            continue
        if len(first) != 2 or not all(math.isfinite(v) for v in first):
            fail(f"TOTALITY[expandAscending] nonsingular({a!r}, {b!r}) = "
                 f"{first!r} is not a pair of finite endpoints")
            continue
        if expand_real(a, b) != first:
            fail(f"FUNCTIONALITY[expandAscending] nonsingular({a!r}, {b!r}) is "
                 f"not repeat-stable")
        # no axis / locator / global state: interleave unrelated calls, re-ask
        expand_real(-98765.0, 4321.0)
        member_real(2.5, 2.5)
        if expand_real(a, b) != first:
            fail(f"FUNCTIONALITY[expandAscending] nonsingular({a!r}, {b!r}) "
                 f"changed after unrelated calls (hidden state)")
        checks += 2
    return checks


def check_hunk_observable():
    """F: the dropped `increasing=False` really changes the member's answer."""
    seen = []
    for a, b in ((10.0, 1.0), (7.0, 3.0), (5.0, -3.0), (0.9, 0.1)):
        post, pre = expand_real(a, b), expand_prepatch(a, b)
        if post != pre:
            seen.append((a, b, post, pre))
    if not seen:
        fail("TICKER HUNK NOT OBSERVABLE: the post-patch widener call "
             "`nonsingular(v0, v1, expander=.05)` and the pre-patch call "
             "`nonsingular(v0, v1, increasing=False, expander=.05)` agree at "
             "every reversed probe request. Modeling the callee half as a second "
             "operation would then be decoration, and the second prepatch twin "
             "would be vacuous")
        return
    a, b, post, pre = seen[0]
    notes.append(
        f"TICKER HUNK OBSERVABLE: at the reversed request ({a}, {b}) the "
        f"post-patch member reports {post!r} but the pre-patch member reports "
        f"{pre!r} ({len(seen)}/4 reversed probes disagree). The pre-patch member "
        f"hands the pair back in the order it received it, so a caller that "
        f"reinstates the requested orientation exchanges the endpoints a SECOND "
        f"time -- which is why the two halves of the gold patch are two modeled "
        f"operations with two prepatch twins, not one.")
    # and the composed member post-patch is the sorted-and-widened pair
    for v0, v1 in ((10.0, 1.0), (1.0, 10.0), (3.0, 3.0), (5.0, -3.0)):
        want = expand_real(min(v0, v1), max(v0, v1))
        got = member_real(v0, v1)
        if tuple(got) != tuple(want):
            fail(f"MEMBER SHADOW: Locator.nonsingular({v0}, {v1}) = {got!r} but "
                 f"`defaultMemberPair` models it as {want!r} (sort, then widen, "
                 f"then report AS IS)")


def check_widener_symmetric():
    """G: `expandAscending a b == expandAscending b a` -- a bound on the battery."""
    bad = []
    for a, b in PROBE_POINTS:
        if expand_real(a, b) != expand_real(b, a):
            bad.append((a, b, expand_real(a, b), expand_real(b, a)))
    if bad:
        a, b, x, y = bad[0]
        fail(f"WIDENER SYMMETRY: nonsingular({a}, {b}) = {x!r} but "
             f"nonsingular({b}, {a}) = {y!r}. properties.py DROPS a family of "
             f"rivals (sort the wrong way round / sort descending / gate the "
             f"sort) on the ground that refuting them needs the FALSE hypothesis "
             f"`expandAscending 10 1 != expandAscending 1 10`; if the widener is "
             f"asymmetric after all, those rivals are refutable honestly and must "
             f"be shipped")
    else:
        notes.append(
            f"WIDENER SYMMETRY: nonsingular(a, b) == nonsingular(b, a) at all "
            f"{len(PROBE_POINTS)} probe requests (it sorts internally, "
            f"transforms.py:2807-2809, and post-patch never un-sorts). So "
            f"`expandAscending 10 1 != expandAscending 1 10` is FALSE of the real "
            f"callee, and the rivals that would need it are deliberately NOT "
            f"shipped (properties.py, ATTACK FAMILIES / NOT SHIPPED). The honest "
            f"coverage of that freedom is P2/P3 naming the widener's arguments "
            f"plus G-CONF executing the member against the real source.")


# The four conditioning hypotheses the SECOND operation's witnesses rest on.
# These are facts about ONE function (not a family), so each is checked directly.
WITNESS_FACTS_2 = [
    ("reject-member-restores-order",
     "(expandAscending 1 10).1 < (expandAscending 1 10).2",
     lambda: expand_real(1.0, 10.0)[0] < expand_real(1.0, 10.0)[1]),
    ("reject-member-swap-always",
     "(expandAscending 1 10).1 < (expandAscending 1 10).2",
     lambda: expand_real(1.0, 10.0)[0] < expand_real(1.0, 10.0)[1]),
    ("reject-member-degenerate-raw",
     "(expandAscending 3 3).1 != 3",
     lambda: expand_real(3.0, 3.0)[0] != 3.0),
]


def check_witness_realisability_2():
    for case, form, pred in WITNESS_FACTS_2:
        try:
            ok = pred()
        except Exception as exc:
            ok, form = False, f"{form} [raised {type(exc).__name__}: {exc}]"
        if not ok:
            fail(f"WITNESS POINT [{case}]: the real widener does NOT satisfy "
                 f"{form} -- the witness would refute its rival only at an input "
                 f"the carrier never realises")
        else:
            notes.append(f"WITNESS POINT [{case}]: {form} -- realised by the real "
                         f"widener, nonsingular(1, 10) = "
                         f"{expand_real(1.0, 10.0)!r}, nonsingular(3, 3) = "
                         f"{expand_real(3.0, 3.0)!r}")
    # the cross-axiom hypothesis of reject-member-echo-sibling: the per-scale
    # chain and the shared 5% widener disagree on a degenerate request.
    who = find_member(lambda f: f(3.0, 3.0) != tuple(expand_real(3.0, 3.0)))
    if who is None:
        fail("WITNESS POINT [reject-member-echo-sibling]: no member of the "
             "normalizer family satisfies `normalize 3 3 != expandAscending 3 3` "
             "-- the echo rival would be refuted only at an unrealisable input")
    else:
        fig, ax = dict(MEMBERS)[who]()
        try:
            got = normalize_real(ax, 3.0, 3.0)
        finally:
            plt.close(fig)
        notes.append(
            f"WITNESS POINT [reject-member-echo-sibling]: normalize 3 3 != "
            f"expandAscending 3 3 -- realised by member {who!r}, which widens the "
            f"degenerate request to {got!r} while the shared 5% widener gives "
            f"{expand_real(3.0, 3.0)!r}. The two operations are pinned to "
            f"DIFFERENT callees and a rival cannot answer one with the other's "
            f"reference expression.")


def record_value_preservation():
    """Why two witness points had to be DEGENERATE requests (recorded, not asserted).

    On strictly-positive DISTINCT endpoints the chain is value-preserving, so
    `(normalize a b).1 != a` is FALSE there; a witness resting on it would be
    satisfiable in Lean and false of the callee. A DEGENERATE request is widened,
    which is what makes the same hypothesis honest at (3,3) and (4,4).
    """
    for tag, build in (MEMBERS[0], MEMBERS[1]):
        fig, ax = build()
        try:
            keep = normalize_real(ax, 2.0, 7.0)
            widen = normalize_real(ax, 3.0, 3.0)
        finally:
            plt.close(fig)
        notes.append(f"VALUE PRESERVATION [{tag}]: normalize(2, 7) = {keep!r} "
                     f"(value-preserving, so `(normalize 2 7).1 != 2` is FALSE of "
                     f"the callee) but normalize(3, 3) = {widen!r} (a degenerate "
                     f"request IS widened, so `(normalize 3 3).1 != 3` is TRUE) -- "
                     f"which is why the two value-attacking witnesses stand at "
                     f"degenerate requests.")


def main():
    rng = random.Random(14623)

    try:
        import matplotlib.ticker as t
        import inspect
        patched = "increasing=False" not in inspect.getsource(t.Locator.nonsingular)
    except Exception:
        patched = None
    print(f"tree: matplotlib {matplotlib.__version__}, "
          f"Locator.nonsingular canonicalizes = {patched} "
          f"(True == gold patch applied, ticker.py:1523-1524)")

    checks = check_functionality_and_totality(rng)
    check_order_census()
    check_witness_realisability()
    record_value_preservation()
    checks += check_widener_axiom(rng)
    check_hunk_observable()
    check_widener_symmetric()
    check_witness_realisability_2()

    for n in notes:
        print("  *", n)

    if errors:
        print(f"G-AX FAIL: {len(errors)} violation(s) over {checks} "
              f"observation(s). First few:")
        for e in errors[:12]:
            print("  -", e)
        sys.exit(1)

    print(f"G-AX OK (second axiom): `axiom expandAscending : Endpoint -> "
          f"Endpoint -> Endpoint x Endpoint` is sound for the REAL shared "
          f"range widener "
          f"`mtransforms.nonsingular(a, b, expander=.05)` -- total (never raised; "
          f"every answer a pair of finite endpoints) and a FUNCTION of its two "
          f"arguments (repeat-stable, no dependence on axis/locator state) over "
          f"the boundary set plus 4000 fuzzed pairs. Measured, not assumed: the "
          f"dropped `increasing=False` really changes the member's answer on a "
          f"reversed request (so the second modeled operation is observable and "
          f"its prepatch twin is not vacuous), the widener is SYMMETRIC (which is "
          f"why one rival family is deliberately not shipped), and the composed "
          f"member `Locator.nonsingular` equals sort-then-widen-then-report at "
          f"every probe. No endpoint value is pinned.")
    print(f"G-AX OK: `axiom normalize : Endpoint -> Endpoint -> Endpoint x "
          f"Endpoint` is sound for the "
          f"REAL axis-normalizer chain (major-locator `nonsingular` o "
          f"`limit_range_for_scale`). Over {len(MEMBERS)} members of the callee "
          f"family (scale x major locator) and {checks} observations (boundary + "
          f"4000 fuzzed requests each, either sign, either order, degenerate "
          f"included): the chain is TOTAL (never raised; every answer a pair of "
          f"finite endpoints) and is a FUNCTION of its two arguments "
          f"(repeat-stable on the same axis, stable across interleaved unrelated "
          f"requests, and identical on a freshly built identical axis) -- which is "
          f"the entire content of the bare axiom. The reported ORDER is measured, "
          f"not assumed: it differs between members at the same request, so the "
          f"spec conditions on it instead of asserting it, and every conditioning "
          f"hypothesis the falsification battery uses is realised by a named "
          f"member above. No endpoint value is pinned. These two bare function "
          f"types are the only consumed axioms.")
    sys.exit(0)


if __name__ == "__main__":
    main()
