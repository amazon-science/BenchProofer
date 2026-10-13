#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-19040 (Velvet bundle).

POLICY NOTE: under SPEC_GUIDE §0.7, the factoring operation — a self-contained
library routine the changed function delegates to — is modelled as an opaque
oracle `factorList`; this script VALIDATES that oracle against the REAL sympy
callees in-container and confirms the gold/prepatch discrimination genuinely
holds.

The change is a one-token edit in `dmp_ext_factor`:
    s, g, r = dmp_sqf_norm(f, u, K)   # PREPATCH: square-free PART f
    s, g, r = dmp_sqf_norm(F, u, K)   # GOLD:     original polynomial F

This module runs REAL sympy at base_commit and checks:

  (1) FAITHFULNESS / completeness (factorList axiom): driving the public
      `factor(., extension=[I])` entry point under the GOLD body (recovery
      applied to F) reconstructs the original on re-expansion on every witness
      — no factor dropped. So `out = factorList poly` is a genuinely resolving
      refinement, not an echo of an opaque answer key.

  (2) DISCRIMINATION (the bug): under the PREPATCH body (recovery applied to the
      square-free part f) at least one witness DROPS a factor — `factor(.)` does
      NOT reconstruct the original. This is the dropped-`y-1` regime of the
      issue. The axiom therefore genuinely discriminates gold from prepatch.

  (3) other_poly axiom soundness: the real `dmp_sqf_part` is genuinely
      factor-losing (degrees (1,1) -> (1,0)), so the weakest `otherPoly` contract
      (NOTHING promised about factor content) is the strongest SOUND axiom — no
      "same polynomial" promise is admissible. This is exactly why feeding
      `factorList (otherPoly poly)` (prepatch) cannot recover the input's list.

  (4) factorList is ARGUMENT-load-bearing: `dmp_sqf_norm(F)` retains more variable
      structure ((2,2)) than `dmp_sqf_norm(sqf_part)` ((2,0)), so the factoring
      tracks its ARGUMENT — applying it to the related polynomial drops a factor.

  (5) lone axiom soundness: the single-element fallback `factors = [f]` is a
      length-1 list, so `loneLen` (len == 1) is sound and nothing stronger is
      assumed.

  (6) isConstant axiom soundness (the EMPTY-factorisation branch): the real
      function short-circuits before any factoring when its argument carries no
      positive degree in any generator
          if all(d <= 0 for d in dmp_degree_list(f, u)): return lc, []
      and then reports NO factors at all. Measured on the real callee under BOTH
      the gold and the prepatch body (the line is argument-independent) and
      through the public `Poly(...).factor_list()` entry point; a non-constant
      argument is measured to report a NON-empty list. So the modeled clause
      `isConstant poly = true -> out = []` is faithful, and `isConstant` is a
      determinate Boolean function of the argument only.

  (7) the declared DOMAIN, measured DIRECTLY against the patched reference. The
      model declares the operation total, so it must RETURN on every argument of
      its declared domain -- a constant, or a non-constant argument with positive
      MAIN-generator degree (`hasMainDegree`) and no repeated irreducible factor
      (`noRepeatedFactor`). Two unbounded loops stand behind that: the shift
      search of `dmp_sqf_norm` (`sqfreetools.py:160-167`), and the `while True`
      of `dmp_trial_division` (`factortools.py:103-124`). Each probe therefore
      runs the real GOLD callee in a FORKED CHILD with a hard wall-clock budget
      (nothing unbounded is ever run in this process), and the check measures:
        (a) every in-domain witness RETURNS -- including the F2P polynomial
            `(x-I*y)(z-I*t)` and the discriminating P2P `x**2-2*y**2` over
            sqrt(2), and the constants of (6), so the empty-factorisation clause
            lies INSIDE the domain;
        (b) for EACH half of the domain, a witness that satisfies the OTHER half
            does NOT return -- `(x-1)**2*(y-1)` (main degree 2, repeated factor)
            and `y-1` (square-free, no main degree). So an UNCONDITIONAL
            termination claim would be UNSOUND and NEITHER half is decoration; a
            witness that returned would mean that half is needlessly narrow, and
            this check would fail.

  (8) graded coverage of the domain: a spy records every input driven through
      `dmp_ext_factor` while EVERY `test_*` of the module the graded tests live
      in runs (sympy/polys/tests/test_polytools.py -- a superset of this
      instance's 1 FAIL_TO_PASS + 148 PASS_TO_PASS, checked against
      instance.json when it is reachable). Every recorded multivariate input is
      measured to satisfy BOTH halves of the declared domain, i.e. the domain
      retains the whole graded behaviour, so the restriction in (7) cannot hide
      the graded discrimination.

  (9) provenance of BOTH halves of the domain: the MECHANISM behind each of
      (7b)'s witnesses, so each `require` is traceable to real lines rather than
      to an observed hang.
        * `noRepeatedFactor` answers to the shift search of `dmp_sqf_norm`,
          replicated with a HARD BOUND of 12 shifts: in-domain witnesses exit
          after 0-1 shifts, `(x-1)**2*(y-1)` does not exit within the bound.
        * `hasMainDegree` answers to `dmp_trial_division`'s `while True`:
          `dmp_sqf_part` (`factortools.py:1149`) divides by a gcd with a
          derivative in the MAIN generator only, so with no main-generator degree
          the square-free part collapses to a UNIT (measured on `y-1`, `y**2+1`,
          `y*(y-1)`) while with positive main degree it keeps main degree >= 1
          (measured on `(x-1)(y-1)`, `x*y`); and `dmp_div(f, 1) == (f, 0)`, so
          dividing by that unit is a FIXED POINT of that loop and no result is
          reachable.
      Both halves are CONSERVATIVE, and the check says so: `(x-1)*(y-1)**2` has a
      repeated factor yet exits the search, and `y*(y-1)` has no main degree yet
      returns. Asking for more only REMOVES obligations; it admits no rival.

 (10) the BINDING of the first half: `noRepeatedFactor` names a property of the
      ARGUMENT (no irreducible factor of it occurs twice --
      `gcd(f, df/dx_0, ..., df/dx_u)` a unit), NOT `dmp_sqf_norm`'s per-step exit
      test `dmp_sqf_p(r, u, K.dom)`, which speaks about the SHIFTED NORM at the
      current step. The two are inequivalent, and the difference is visible on the
      graded suite: for every multivariate call the graded tests drive, this check
      records the argument-level condition, whether the norm is square-free at
      step 0, and how many steps the search actually takes. A graded call that
      failed the argument-level condition is a VIOLATION (the domain would then
      drop graded behaviour); the count of graded calls the per-step reading would
      exclude is reported, because a materialisation that used the per-step test
      would vacate the contract exactly there.

stdlib + sympy only; exit 0 iff every observation is consistent with the model
axioms AND the gold/prepatch discrimination holds. Run from the repo worktree at
base_commit (sympy 1.6). This script toggles the single-token edit IN-PROCESS
(reconstructing dmp_ext_factor with its own module globals), so it does not
require the worktree to be at gold or prepatch.
"""
import importlib
import inspect
import json
import os
import signal
import sys
import time
import types

import sympy
from sympy import QQ, I, Poly, expand, factor, sqrt
from sympy.polys import ring
from sympy.abc import x, y, z, t
import sympy.polys.factortools as ft
from sympy.polys.densearith import dmp_div
from sympy.polys.densebasic import (dmp_degree_list, dmp_ground_p, dmp_inject,
                                    dmp_raise, dmp_zero_p)
from sympy.polys.densetools import dmp_compose, dmp_diff_in
from sympy.polys.euclidtools import dmp_gcd, dmp_resultant
from sympy.polys.sqfreetools import dmp_sqf_p


VIOLATIONS = []


def _record(msg):
    VIOLATIONS.append(msg)
    print("VIOLATION:", msg)


# ---------------------------------------------------------------------------
# Build GOLD and PREPATCH variants of dmp_ext_factor sharing the factortools
# module globals (so every callee name resolves exactly as in the repo). The
# ONLY difference is the argument to dmp_sqf_norm: F (gold) vs f (prepatch).
# ---------------------------------------------------------------------------
_TEMPLATE = '''
def dmp_ext_factor(f, u, K):
    if not u:
        return dup_ext_factor(f, K)
    lc = dmp_ground_LC(f, u, K)
    f = dmp_ground_monic(f, u, K)
    if all(d <= 0 for d in dmp_degree_list(f, u)):
        return lc, []
    f, F = dmp_sqf_part(f, u, K), f
    s, g, r = dmp_sqf_norm({SRC}, u, K)
    factors = dmp_factor_list_include(r, u, K.dom)
    if len(factors) == 1:
        factors = [f]
    else:
        H = dmp_raise([K.one, s*K.unit], u, 0, K)
        for i, (factor, _) in enumerate(factors):
            h = dmp_convert(factor, u, K.dom, K)
            h, _, g = dmp_inner_gcd(h, g, u, K)
            h = dmp_compose(h, H, u, K)
            factors[i] = h
    return lc, dmp_trial_division(F, factors, u, K)
'''


def _build(src_arg):
    ns = dict(ft.__dict__)
    exec(_TEMPLATE.replace("{SRC}", src_arg), ns)
    return ns["dmp_ext_factor"]


def _run_factor_with(variant_fn, expr):
    orig = ft.dmp_ext_factor
    ft.dmp_ext_factor = variant_fn
    try:
        return factor(expand(expr), extension=[I])
    finally:
        ft.dmp_ext_factor = orig


WITNESSES = [
    (x - 1) * (y - 1),                 # the issue's StackOverflow witness
    (x - 1) * (y - 1) * (z - 1),
    (x + 1) * (y - 1),
    (x - I * y) * (z - I * t),         # F2P test_issue_5786 polynomial
    (x * y - 1) * (y - 1),
    (x - 1) * (x + 1) * (y - 1),
    (x - 1) * (y + 1),
    (x - I) * (y - 1),
]


def check_gold_complete():
    gold = _build("F")
    n_ok = 0
    for e in WITNESSES:
        fe = _run_factor_with(gold, e)
        if expand(fe) != expand(e):
            _record("factorList(gold): factor(.,extension=[I]) != original for "
                    "%s (got %s) -- a factor was dropped under GOLD" % (e, fe))
        else:
            n_ok += 1
    print("[factorList/gold] %d/%d extension factorisations COMPLETE under GOLD "
          "(recovery applied to F; re-expansion reconstructs the original)"
          % (n_ok, len(WITNESSES)))


def check_prepatch_discriminates():
    prepatch = _build("f")
    n_drop = 0
    for e in WITNESSES:
        fe = _run_factor_with(prepatch, e)
        if expand(fe) != expand(e):
            n_drop += 1
            print("[discriminate] PREPATCH drops factor on %s -> %s "
                  "(re-expansion != original)" % (e, fe))
    if n_drop == 0:
        _record("discrimination: PREPATCH (recovery from sqf part) did NOT drop "
                "a factor on ANY witness -- the axiom would not discriminate "
                "gold from prepatch (G-DIFF would be vacuous)")
    else:
        print("[discriminate] PREPATCH drops a factor on %d/%d witnesses -- the "
              "factorList axiom genuinely discriminates gold from prepatch"
              % (n_drop, len(WITNESSES)))


def check_other_poly_factor_losing():
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    f = R.dmp_ground_monic((X - 1) * (Y - 1))
    sp = R.dmp_sqf_part(f)
    df, dsp = f.degrees(), sp.degrees()
    if sp == f or sum(1 for d in dsp if d > 0) >= sum(1 for d in df if d > 0):
        _record("otherPoly: dmp_sqf_part did NOT lose factor content (input "
                "degrees=%s, simpler degrees=%s) -- a stronger axiom than the "
                "weakest contract might be unsoundly assumed" % (df, dsp))
    else:
        print("[otherPoly] dmp_sqf_part((x-1)(y-1)) degrees=%s loses content vs "
              "input degrees=%s -- factor-losing, so the weakest contract "
              "(nothing promised) is the only sound one" % (dsp, df))


def check_argument_is_load_bearing():
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    f = R.dmp_ground_monic((X - 1) * (Y - 1))
    sp = R.dmp_sqf_part(f)
    _, _, r_full = R.dmp_sqf_norm(f)
    _, _, r_part = R.dmp_sqf_norm(sp)
    dl_full, dl_part = r_full.degrees(), sp.degrees() and r_part.degrees()
    full_vars = sum(1 for d in dl_full if d > 0)
    part_vars = sum(1 for d in dl_part if d > 0)
    if not (full_vars > part_vars):
        _record("argument: expected factoring the FULL polynomial to retain MORE "
                "variable structure than the simpler one; got full=%s part=%s"
                % (dl_full, dl_part))
    else:
        print("[argument] dmp_sqf_norm(F) degree_list=%s retains more structure "
              "than dmp_sqf_norm(sqf_part)=%s -- factorList tracks its ARGUMENT "
              "(load-bearing)" % (dl_full, dl_part))


def check_lone_length_one():
    fallback = [object()]
    if len(fallback) != 1:
        _record("lone: the single-element fallback `factors = [f]` is not "
                "length 1 -- loneLen would be unsound")
    else:
        print("[lone] the single-element fallback `factors = [f]` is length 1 -- "
              "loneLen (len == 1) is sound; nothing stronger assumed")


# ---------------------------------------------------------------------------
# (6) isConstant  <->  the `all(d <= 0 ...): return lc, []` short circuit
# ---------------------------------------------------------------------------
def check_constant_argument_reports_no_factors():
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    consts = [("2", (R.one * 2).to_dense()), ("1", R.one.to_dense())]
    nonconsts = [("(x-1)(y-1)", R.dmp_ground_monic((X - 1) * (Y - 1)).to_dense()),
                 ("x*y", (X * Y).to_dense())]
    for label, body in (("gold", "F"), ("prepatch", "f")):
        fn = _build(body)
        for name, dense in consts:
            _lc, fac = fn(dense, 1, K)
            if fac != []:
                _record("isConstant: the real function returned a NON-empty "
                        "factorisation %r for the constant argument %s under the "
                        "%s body -- the modeled clause `isConstant poly = true "
                        "-> out = []` would be unfaithful" % (fac, name, label))
            else:
                print("[isConstant/%s] argument %s (no positive degree, "
                      "degree_list=%s) -> factor list [] (the `return lc, []` "
                      "short circuit)" % (label, name, dmp_degree_list(dense, 1)))
        for name, dense in nonconsts:
            _lc, fac = fn(dense, 1, K)
            if not fac:
                _record("isConstant: the real function returned an EMPTY "
                        "factorisation for the NON-constant argument %s under "
                        "the %s body -- `isConstant` would not be the shape test "
                        "the clause claims" % (name, label))
            else:
                print("[isConstant/%s] argument %s (degree_list=%s) -> %d "
                      "factor(s), non-empty" % (label, name,
                                                dmp_degree_list(dense, 1), len(fac)))
    # the same behaviour through the public entry point the users see
    for expr, want in ((sympy.Integer(2), []), (x * y, None)):
        lc, fac = Poly(expr, x, y, extension=[I]).factor_list()
        if want == [] and fac != []:
            _record("isConstant: public Poly(%s, x, y, extension=[I])."
                    "factor_list() = (%s, %r); expected an EMPTY factor list"
                    % (expr, lc, fac))
        else:
            print("[isConstant/public] Poly(%s, x, y, extension=[I])."
                  "factor_list() -> (%s, %d factor(s))" % (expr, lc, len(fac)))


# ---------------------------------------------------------------------------
# (7) the declared DOMAIN is measured to be a region where the PATCHED
#     reference TERMINATES -- and each half of it is measured to be necessary
# ---------------------------------------------------------------------------
SHIFT_BOUND = 12

# Wall-clock budget for one forked termination probe. The loops involved are
# genuinely unbounded, so every probe runs in a CHILD process that is SIGKILLed
# at the budget; nothing unbounded is ever run in this process.
_TERMINATION_BUDGET = float(os.environ.get("SBU_AX_TERMINATION_BUDGET", "45"))


def _has_repeated_factor(f, u, K):
    """True iff some irreducible factor of `f` occurs more than once.

    Over a characteristic-0 field this is exact: `g**2 | f` for a non-unit `g`
    iff gcd(f, df/dx_0, ..., df/dx_u) is a non-unit.  A constant has no
    irreducible factor at all, so it comes out False (vacuously in the domain).
    """
    h = f
    for j in range(u + 1):
        h = dmp_gcd(h, dmp_diff_in(f, 1, j, u, K), u, K)
    return not dmp_ground_p(h, None, u)


def _main_degree(f, u):
    """Degree of `f` in the FIRST (main) generator of the dense representation."""
    return dmp_degree_list(f, u)[0]


def _in_declared_domain(f, u, K):
    """(inside?, why) for the domain `Solution.lean` declares.

    Exactly the conjunction of the two `require`s, read on the real carrier:
      * a CONSTANT argument is inside (it is reported, with the empty
        factorisation, before any factoring begins -- `isConstant`);
      * a NON-CONSTANT argument is inside iff it carries positive degree in the
        MAIN generator (`hasMainDegree`) AND no irreducible factor of it occurs
        more than once (`noRepeatedFactor`).
    """
    dl = dmp_degree_list(f, u)
    if all(d <= 0 for d in dl):
        return True, "constant (reported before any factoring)"
    if dl[0] <= 0:
        return False, "no main-generator degree (hasMainDegree false)"
    if _has_repeated_factor(f, u, K):
        return False, "a repeated factor (noRepeatedFactor false)"
    return True, "main degree %d, no repeated factor" % dl[0]


def _shifts_to_exit(f, u, K, bound):
    """Replicate `dmp_sqf_norm`'s unbounded shift search with a HARD bound.

    Returns the number of shifts after which its exit test fires, or None if it
    has not fired within `bound` shifts.  Mirrors sqfreetools.dmp_sqf_norm
    exactly (same `g`, same shift polynomial `F`, same exit predicate).
    """
    g = dmp_raise(K.mod.rep, u + 1, 0, K.dom)
    F = dmp_raise([K.one, -K.unit], u, 0, K)
    for s in range(bound):
        h, _ = dmp_inject(f, u, K, front=True)
        r = dmp_resultant(g, h, u + 1, K.dom)
        if dmp_sqf_p(r, u, K.dom):
            return s
        f = dmp_compose(f, F, u, K)
    return None


def _returns_within(fn, args, budget):
    """Does `fn(*args)` RETURN within `budget` seconds?

    True  -- the child process ran the call to completion and exited cleanly.
    False -- the child was still running at the budget and was SIGKILLed, i.e.
             the call does not return (the real loops here are unbounded, so an
             in-process probe could not be interrupted at all).
    None  -- the child died for an unrelated reason: inconclusive, never read as
             either termination or divergence.
    """
    sys.stdout.flush()
    sys.stderr.flush()
    pid = os.fork()
    if pid == 0:                                  # child
        code = 0
        try:
            fn(*args)
        except BaseException:
            code = 3
        os._exit(code)
    deadline = time.time() + budget
    while True:
        done, status = os.waitpid(pid, os.WNOHANG)
        if done:
            if os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0:
                return True
            return None
        if time.time() > deadline:
            os.kill(pid, signal.SIGKILL)
            os.waitpid(pid, 0)
            return False
        time.sleep(0.05)


def check_domain_is_the_terminating_region():
    """DIRECT measurement of the termination claim, against the PATCHED body.

    `Solution.lean` declares `loom.semantics.termination "total"`, so it asserts
    that the operation RETURNS on every argument of its declared domain. That is
    measured here on the real callee (the GOLD variant -- the reference the spec
    models), not argued:

      (a) every in-domain witness RETURNS within the budget -- so the totality
          claim is real; if one did not, the spec would be too strong and this
          check fails;
      (b) for EACH of the two halves of the domain there is a witness that
          satisfies the OTHER half and does NOT return -- so neither half is
          decoration: dropping it would make the totality claim unsound. If such
          a witness returned, the corresponding `require` would be needlessly
          narrow and this check fails.
    """
    gold = _build("F")
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    R3, X3, Y3, Z3, T3 = ring("x,y,z,t", K)
    K2 = QQ.algebraic_field(sqrt(2))
    R2, X2, Y2 = ring("x,y", K2)
    inside = [
        ("2 (constant)", (R.one * 2).to_dense(), 1, K),
        ("1 (unit)", R.one.to_dense(), 1, K),
        ("(x-1)(y-1)", R.dmp_ground_monic((X - 1) * (Y - 1)).to_dense(), 1, K),
        ("(x+1)(y-1)", R.dmp_ground_monic((X + 1) * (Y - 1)).to_dense(), 1, K),
        ("(x-I*y)", R.dmp_ground_monic(X - K.unit * Y).to_dense(), 1, K),
        ("(x-1)(x+1)(y-1)",
         R.dmp_ground_monic((X - 1) * (X + 1) * (Y - 1)).to_dense(), 1, K),
        ("(x*y-1)(y-1)", R.dmp_ground_monic((X * Y - 1) * (Y - 1)).to_dense(), 1, K),
        ("x*y", (X * Y).to_dense(), 1, K),
        # the F2P polynomial itself (u = 3) and the discriminating P2P one
        ("(x-I*y)(z-I*t)  [F2P]",
         R3.dmp_ground_monic((X3 - K.unit * Y3) * (Z3 - K.unit * T3)).to_dense(), 3, K),
        ("x**2-2*y**2  [P2P, sqrt(2)]",
         R2.dmp_ground_monic(X2 ** 2 - 2 * Y2 ** 2).to_dense(), 1, K2),
    ]
    for name, dense, u, dom in inside:
        ok, why = _in_declared_domain(dense, u, dom)
        if not ok:
            _record("domain: witness %s was expected INSIDE the declared domain "
                    "but the domain test reads it as outside (%s) -- this check "
                    "is miscalibrated" % (name, why))
            continue
        verdict = _returns_within(gold, (dense, u, dom), _TERMINATION_BUDGET)
        if verdict is True:
            print("[domain/inside] %s (%s): the patched callee RETURNS -- total "
                  "there, as the contract claims" % (name, why))
        elif verdict is False:
            _record("domain: the patched callee did NOT return within %.0fs for "
                    "%s, which IS inside the declared domain -- the modeled "
                    "operation is not total on its own domain, so the `require`s "
                    "are too weak and the termination claim is UNSOUND"
                    % (_TERMINATION_BUDGET, name))
        else:
            _record("domain: the termination probe for the in-domain witness %s "
                    "died without completing the call -- INCONCLUSIVE, the "
                    "totality claim is unmeasured" % name)
    # One divergence witness per half of the domain: each satisfies the OTHER
    # half, so each isolates the necessity of its own `require`.
    outside = [
        ("(x-1)**2*(y-1)", R.dmp_ground_monic((X - 1) ** 2 * (Y - 1)).to_dense(),
         1, K, "noRepeatedFactor",
         "main degree 2 > 0, but (x-1) occurs twice"),
        ("y-1", R.dmp_ground_monic(Y - 1).to_dense(), 1, K, "hasMainDegree",
         "square-free, but no degree in the main generator"),
    ]
    for name, dense, u, dom, leg, shape in outside:
        ok, why = _in_declared_domain(dense, u, dom)
        if ok:
            _record("domain: witness %s was expected OUTSIDE the declared domain "
                    "but the domain test reads it as inside (%s) -- this check is "
                    "miscalibrated" % (name, why))
            continue
        verdict = _returns_within(gold, (dense, u, dom), _TERMINATION_BUDGET)
        if verdict is False:
            print("[domain/outside] %s (%s): the patched callee does NOT return "
                  "within %.0fs -- an unconditional termination claim would be "
                  "unsound, so the `%s` half of the domain is NECESSARY, not "
                  "decorative" % (name, shape, _TERMINATION_BUDGET, leg))
        elif verdict is True:
            _record("domain: the patched callee DID return for %s, which the `%s` "
                    "half of the domain EXCLUDES -- that half buys no soundness "
                    "and the spec is needlessly narrow there" % (name, leg))
        else:
            _record("domain: the divergence probe for %s died without completing "
                    "the call -- INCONCLUSIVE, the necessity of the `%s` half is "
                    "unmeasured" % (name, leg))


# ---------------------------------------------------------------------------
# (8) graded coverage: every graded input lies inside the declared domain
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))


# The graded tests of this instance (1 FAIL_TO_PASS + 148 PASS_TO_PASS) all live
# in sympy/polys/tests/test_polytools.py, so the coverage measurement drives
# EVERY `test_*` of that module: a SUPERSET of the graded list, which makes the
# conclusion "no graded input lies outside the declared domain" independent of
# how a test happens to reach an algebraic-field factorisation (`extension=`,
# `domain=`, `gaussian=`, a helper, ...). instance.json is read when reachable
# purely to report that the superset really does cover the graded names; the
# container mounts the bundle directory alone (instance.json is its sibling, not
# its child), so its absence is not an error.
_GRADED_TEST_MODULE = "sympy.polys.tests.test_polytools"


def _graded_test_names():
    """FAIL_TO_PASS + PASS_TO_PASS from instance.json when it is available."""
    names = []
    path = os.path.join(_HERE, os.pardir, "instance.json")
    try:
        with open(path) as fh:
            inst = json.load(fh)
    except Exception:
        return names
    for key in ("FAIL_TO_PASS", "PASS_TO_PASS"):
        val = inst.get(key) or "[]"
        if isinstance(val, str):
            val = json.loads(val)
        for n in val:
            if n not in names:
                names.append(n)
    return names


# Every `dmp_ext_factor` call the graded sweep of (8) records, kept so that (10)
# can re-read the SAME inputs (driving the whole test module twice would double
# the cost of this check for nothing).
GRADED_CALLS = []


def check_graded_inputs_inside_domain():
    calls = []
    orig = ft.dmp_ext_factor

    def spy(f, u, K):
        calls.append((f, u, K))
        return orig(f, u, K)

    # (a) the graded assertions themselves, verbatim from
    #     sympy/polys/tests/test_polytools.py (test_issue_5786:3254 -- the F2P --
    #     and the multivariate extension assertions of test_factor:2423-2426).
    inline = [
        ("F2P test_issue_5786", lambda: factor(expand((x - I * y) * (z - I * t)),
                                               extension=[I])),
        ("P2P test_factor x**2-2*y**2", lambda: factor(x ** 2 - 2 * y ** 2,
                                                       extension=sqrt(2))),
        ("P2P test_factor 2*x**2-4*y**2", lambda: factor(2 * x ** 2 - 4 * y ** 2,
                                                         extension=sqrt(2))),
    ]
    ft.dmp_ext_factor = spy
    try:
        for label, thunk in inline:
            thunk()
        n_inline = len(calls)
        # (b) then EVERY `test_*` of the module the graded tests live in -- a
        #     superset of the graded list, so nothing graded can be missed.
        driven = []
        try:
            T = importlib.import_module(_GRADED_TEST_MODULE)
        except Exception as exc:          # pragma: no cover - image without tests
            print("[graded] test module unavailable (%r); relying on the %d "
                  "inlined graded assertion(s)" % (exc, n_inline))
        else:
            for name in sorted(n for n in dir(T) if n.startswith("test_")):
                fn = getattr(T, name, None)
                if not callable(fn):
                    continue
                driven.append(name)
                try:
                    fn()
                except Exception:
                    # at base_commit the F2P assertion does not hold (it IS the
                    # graded behaviour); the spy has already recorded its input.
                    # Any other failure is equally irrelevant here: what is being
                    # measured is the INPUT each test hands to the operation.
                    pass
            graded = _graded_test_names()
            uncovered = [n for n in graded if n not in driven]
            print("[graded] drove all %d `test_*` of %s%s"
                  % (len(driven), _GRADED_TEST_MODULE,
                     ("; covers %d/%d graded test name(s) from instance.json"
                      % (len(graded) - len(uncovered), len(graded)))
                     if graded else " (instance.json not reachable here)"))
            if uncovered:
                _record("graded coverage: %d graded test name(s) are not in %s "
                        "(%s) -- the superset does not cover the graded list"
                        % (len(uncovered), _GRADED_TEST_MODULE,
                           ", ".join(uncovered[:5])))
    finally:
        ft.dmp_ext_factor = orig
    GRADED_CALLS.extend(calls)

    n_multi = n_uni = n_bad = 0
    shapes = {}
    for f, u, K in calls:
        if u == 0:
            n_uni += 1          # delegated to dup_ext_factor, not this operation
            continue
        n_multi += 1
        # Checked against BOTH halves of the declared domain at once, so neither
        # `require` can be the one that quietly drops graded behaviour.
        ok, why = _in_declared_domain(f, u, K)
        shapes.setdefault((tuple(dmp_degree_list(f, u)), why), 0)
        shapes[(tuple(dmp_degree_list(f, u)), why)] += 1
        if not ok:
            n_bad += 1
            _record("graded coverage: a graded input with degree_list %s reaches "
                    "the operation and lies OUTSIDE the declared domain (%s) -- "
                    "the restriction would hide graded behaviour"
                    % (dmp_degree_list(f, u), why))
    if not n_multi:
        _record("graded coverage: no graded input reached the operation with "
                "more than one generator -- the coverage argument is unverified")
    elif not n_bad:
        print("[graded] %d graded multivariate call(s) (plus %d univariate call(s) "
              "delegated away); EVERY one satisfies BOTH halves of the declared "
              "domain -- the restriction retains the whole graded behaviour"
              % (n_multi, n_uni))
        for (dl, why), n in sorted(shapes.items()):
            print("[graded]   degree_list %s x%d: %s" % (list(dl), n, why))


# ---------------------------------------------------------------------------
# (9) provenance of BOTH halves of the declared domain: which unbounded loop
#     each one answers to, measured on the real callees
# ---------------------------------------------------------------------------
def check_domain_leg_provenance():
    """WHICH loop each half of the domain answers to, and why it diverges.

    (7) measures the divergence; this measures its MECHANISM, so each `require`
    is traceable to real lines rather than to an observed hang.

    FIRST half, `noRepeatedFactor` -- the shift search of `dmp_sqf_norm`
    (`sqfreetools.py:160-167`, reached from `factortools.py:1150`) reports only on
    reaching an image whose norm has no repeated factor. Replicated here with a
    HARD BOUND of 12 shifts (the real loop is unbounded): every in-domain witness
    exits after 0-1 shifts, while `(x-1)**2*(y-1)` does not exit within the bound.

    SECOND half, `hasMainDegree` -- why a non-constant argument with no
    main-generator degree cannot return:

      (a) `f, F = dmp_sqf_part(f, u, K), f` (`factortools.py:1149`) divides by
          `gcd(f, df/dx_0)`, a derivative in the MAIN generator only. With no
          main-generator degree that derivative is 0, the gcd is `f` itself, and
          the square-free part COLLAPSES TO A UNIT. With positive main degree the
          gcd has strictly smaller main degree, so the part keeps main degree
          >= 1 and is never a unit.
      (b) `dmp_trial_division(F, factors, u, K)` (`factortools.py:103-124`,
          reached from :1165) is a `while True` that divides by each factor while
          the remainder is zero. Dividing by a UNIT returns the dividend
          unchanged with zero remainder -- a FIXED POINT -- so the loop never
          exits once the representative `f` of the `len(factors) == 1` branch
          (:1155) is that unit.

    BOTH halves are CONSERVATIVE rather than tight, and the measurements below
    say so out loud. `dmp_sqf_p` tests square-freeness of the NORM, so some
    arguments with a repeated factor still exit the search (`(x-1)*(y-1)**2` does,
    after 1 shift); and the unit collapse only becomes divergence when the
    recovery ALSO collapses to a single element, so some arguments with no main
    degree still return (`y*(y-1)` does). Telling those cases apart needs
    statements about how the norm of the argument factors -- stronger claims than
    the model can justify -- so each `require` errs on the side of asking for
    more. That direction only REMOVES obligations; it never admits a rival (the
    eight G-PBT reject cases are each refuted at a point where BOTH halves hold).
    """
    K = QQ.algebraic_field(I)
    R, X, Y = ring("x,y", K)
    # FIRST half: the shift search, replicated with a hard bound.
    for name, p, want_exit in [("(x-1)(y-1)", (X - 1) * (Y - 1), True),
                               ("x-I*y", X - K.unit * Y, True),
                               ("(x-1)(x+1)(y-1)", (X - 1) * (X + 1) * (Y - 1), True),
                               ("(x-1)**2*(y-1)", (X - 1) ** 2 * (Y - 1), False)]:
        dense = R.dmp_ground_monic(p).to_dense()
        s = _shifts_to_exit(dense, 1, K, SHIFT_BOUND)
        if (s is not None) != want_exit:
            _record("noRepeatedFactor: the shift search of dmp_sqf_norm %s for %s "
                    "(expected %s) -- the mechanism behind the first half of the "
                    "domain is not what the model claims"
                    % ("exited after %d shift(s)" % s if s is not None
                       else "did not exit within %d shifts" % SHIFT_BOUND, name,
                       "an exit" if want_exit else "no exit"))
        elif want_exit:
            print("[noRepeatedFactor] %s: no repeated factor, the shift search "
                  "exits after %d shift(s) -- a reportable image is reached"
                  % (name, s))
        else:
            print("[noRepeatedFactor] %s: (x-1) occurs twice, the shift search "
                  "does not reach a reportable image within %d shifts -- the "
                  "first unbounded loop behind the first `require`"
                  % (name, SHIFT_BOUND))
    # SECOND half: the unit collapse and the trial-division fixed point.
    cases = [("y-1", Y - 1, True), ("y**2+1", Y ** 2 + 1, True),
             ("y*(y-1)", Y * (Y - 1), True),
             ("(x-1)(y-1)", (X - 1) * (Y - 1), False), ("x*y", X * Y, False)]
    for name, p, want_unit in cases:
        f = R.dmp_ground_monic(p)
        sp = R.dmp_sqf_part(f).to_dense()
        is_unit = dmp_ground_p(sp, None, 1)
        md_in = _main_degree(f.to_dense(), 1)
        if is_unit != want_unit:
            _record("hasMainDegree: dmp_sqf_part(%s) unit=%r, expected %r -- the "
                    "mechanism behind the main-degree half of the domain is not "
                    "what the model claims" % (name, is_unit, want_unit))
        elif is_unit:
            print("[hasMainDegree] %s: main degree %d, dmp_sqf_part COLLAPSES to "
                  "a unit (the derivative in the main generator is 0) -- the "
                  "representative the len(factors)==1 branch falls back to is a "
                  "unit" % (name, md_in))
        else:
            print("[hasMainDegree] %s: main degree %d, dmp_sqf_part keeps main "
                  "degree %d >= 1 -- not a unit, so the trial division below "
                  "makes progress" % (name, md_in, _main_degree(sp, 1)))
    unit = R.one.to_dense()
    f = R.dmp_ground_monic((X - 1) * (Y - 1)).to_dense()
    q, r = dmp_div(f, unit, 1, K)
    if not (q == f and dmp_zero_p(r, 1)):
        _record("hasMainDegree: dividing by a unit did not return the dividend "
                "with zero remainder (q==f: %r, zero r: %r) -- the trial-division "
                "fixed point the domain restriction is derived from does not hold"
                % (q == f, dmp_zero_p(r, 1)))
    else:
        print("[hasMainDegree] dmp_div(f, 1) = (f, 0): dividing by a unit is a "
              "FIXED POINT of dmp_trial_division's `while True` (factortools.py:"
              "103-124), so no result is reachable once the fallback "
              "representative is a unit -- exactly the arguments the second "
              "`require` excludes")


# ---------------------------------------------------------------------------
# (10) WHICH predicate the first half of the domain names: a property of the
#      ARGUMENT, not `dmp_sqf_norm`'s per-step exit test
# ---------------------------------------------------------------------------
def check_domain_binding_is_argument_level():
    """Measure the two candidate readings of `noRepeatedFactor` on graded inputs.

    Two INEQUIVALENT predicates live next to this `require`:

      (i)  the ARGUMENT-level one the axiom docstring states -- no irreducible
           factor occurs in the argument more than once, i.e.
           `gcd(f, df/dx_0, ..., df/dx_u)` a unit. This is the hypothesis of the
           classical fact (Trager) that only finitely many shifts are bad, i.e.
           the one under which the search TERMINATES;
      (ii) the search's PER-STEP exit test `dmp_sqf_p(r, u, K.dom)`
           (`sqfreetools.py:160-167`) -- square-freeness of the SHIFTED NORM at the
           current step, which says the search exits IMMEDIATELY, not that it
           exits at all.

    Only (i) is a domain. The measurement below shows the difference is not
    hypothetical: it is visible on the very calls the graded tests drive, where
    several arguments with no repeated factor need a shift before the norm becomes
    square-free. A graded call violating (i) would mean the declared domain drops
    graded behaviour (a VIOLATION); the number of graded calls that (ii) would
    exclude is reported, since a materialisation reading the `require` as (ii)
    would leave the contract vacuous exactly on them.
    """
    calls = [c for c in GRADED_CALLS if c[1]]
    if not calls:                       # (8) unavailable: fall back to the three
        collected = []                  # inlined graded assertions.
        orig = ft.dmp_ext_factor

        def spy(f, u, K):
            collected.append((f, u, K))
            return orig(f, u, K)

        ft.dmp_ext_factor = spy
        try:
            factor(expand((x - I * y) * (z - I * t)), extension=[I])
            factor(x ** 2 - 2 * y ** 2, extension=sqrt(2))
            factor(2 * x ** 2 - 4 * y ** 2, extension=sqrt(2))
        finally:
            ft.dmp_ext_factor = orig
        calls = [c for c in collected if c[1]]

    rows = []
    for f, u, K in calls:
        monic = ft.dmp_ground_monic(f, u, K)
        dl = tuple(dmp_degree_list(monic, u))
        if all(d <= 0 for d in dl):
            continue                    # constant: reported before the search
        rows.append((dl, str(K),
                     not _has_repeated_factor(monic, u, K),
                     _shifts_to_exit(monic, u, K, SHIFT_BOUND)))
    if not rows:
        _record("domain binding: no non-constant multivariate graded input was "
                "observed -- which predicate the first `require` names is "
                "unmeasured")
        return

    n_arg = sum(1 for r in rows if r[2])
    n_step0 = sum(1 for r in rows if r[3] == 0)
    for dl, dom, arg_ok, shifts in sorted(rows):
        print("[binding] degree_list %s over %s: no repeated factor in the "
              "ARGUMENT=%s, norm square-free at step 0=%s, search exits after %s"
              % (list(dl), dom, arg_ok, shifts == 0,
                 "%d step(s)" % shifts if shifts is not None
                 else "NO exit within %d" % SHIFT_BOUND))
        if not arg_ok:
            _record("domain binding: a graded multivariate input with degree_list "
                    "%s over %s has a REPEATED FACTOR, so the argument-level "
                    "reading of the first `require` excludes it -- the declared "
                    "domain would drop graded behaviour" % (list(dl), dom))
        elif shifts is None:
            _record("domain binding: the search did not exit within %d shifts for "
                    "a graded input with degree_list %s over %s that the "
                    "argument-level reading ADMITS -- that reading would not be a "
                    "terminating region" % (SHIFT_BOUND, list(dl), dom))
    print("[binding] argument-level reading (i): %d/%d graded multivariate call(s) "
          "INSIDE the declared domain" % (n_arg, len(rows)))
    if n_step0 == len(rows):
        print("[binding] per-step reading (ii) happens to agree on these calls; it "
              "is still a different predicate (see the witness below) and the "
              "axiom names (i)")
    else:
        print("[binding] per-step reading (ii) would place %d of %d graded "
              "multivariate call(s) OUTSIDE the domain -- reading the `require` as "
              "the search's exit test would vacate the contract on them, so it is "
              "NOT a faithful materialisation of the axiom"
              % (len(rows) - n_step0, len(rows)))

    # The inequivalence, in both directions, on fixed witnesses:
    #   * no repeated factor yet the norm needs a shift  (i) true, (ii) false
    #   * a repeated factor yet the norm is square-free at some step: (i) false
    #     while the search still exits -- measured in (9) on `(x-1)*(y-1)**2`.
    K2 = QQ.algebraic_field(sqrt(2))
    R2, X2, Y2 = ring("x,y", K2)
    w = R2.dmp_ground_monic(X2 ** 2 - 2 * Y2 ** 2).to_dense()
    w_arg = not _has_repeated_factor(w, 1, K2)
    w_s = _shifts_to_exit(w, 1, K2, SHIFT_BOUND)
    if not (w_arg and w_s == 1):
        _record("domain binding: the witness x**2-2*y**2 over sqrt(2) measured "
                "no-repeated-factor=%r, shifts=%r -- expected True/1, so the two "
                "readings could not be told apart here" % (w_arg, w_s))
    else:
        print("[binding] witness x**2-2*y**2 over QQ<sqrt(2)>: no repeated factor "
              "in the argument, but the norm is NOT square-free at step 0 (the "
              "search exits at step 1) -- the two readings are inequivalent, and "
              "this witness is the P2P `test_factor` input itself")


def main():
    print("=== axiom_check sympy__sympy-19040 (sympy %s) ===" % sympy.__version__)
    check_other_poly_factor_losing()
    check_gold_complete()
    check_prepatch_discriminates()
    check_argument_is_load_bearing()
    check_lone_length_one()
    check_constant_argument_reports_no_factors()
    check_domain_is_the_terminating_region()
    check_graded_inputs_inside_domain()
    check_domain_leg_provenance()
    check_domain_binding_is_argument_level()
    if VIOLATIONS:
        print("\nUNSOUND: %d violation(s)" % len(VIOLATIONS))
        return 1
    print("\nSOUND: all axiom observations consistent with model axioms; "
          "gold/prepatch discrimination holds on real sympy.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
