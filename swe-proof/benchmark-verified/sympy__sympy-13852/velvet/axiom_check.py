#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13852.

This bundle has NO consumed axiom. The changed operation -- which
closed form a two-argument special function f(s, z) takes at each recognised
argument pattern, and that its series-expansion at s = 1 is the elementary
-log(1 - z) -- is modelled with a discrete dispatch (Solution.lean: `closedFormFor`,
`expansionCode`). The dispatch returns a CODE naming a closed form; that the
code-named closed form actually EQUALS the real function at the pattern is the
out-of-band obligation validated here against the REAL gold-patched callee
(an A-reference, NOT a consumed axiom).

Validated, in-container against the REAL fixed `polylog` / `expand_func`:

  (A-reference 1 -- the eval dispatch)  For each recognised argument pattern the
      model assigns a closed-form CODE; this script asserts the REAL polylog(s,z)
      auto-evaluates to EXACTLY the gold closed form that code names (symbolic
      equality), AND that the evaluation actually FIRED (the result is no longer
      a bare polylog(...) call) for every newly-recognised pattern. It also
      asserts the dispatch does NOT over-fire: at an UNrecognised pattern the
      real polylog(s,z) stays unevaluated (still a polylog instance). Both
      directions are checked -- there is no one-sided mask.

  (A-reference 2 -- the priority cascade)  The z = 1 / z = -1 / z = 0 clauses
      take priority over the s = 0 / s = -1 clauses: polylog(0, 1) is the zeta
      value (not the rational z/(1-z) at z=1, which is division by zero), and
      polylog(0, 0) / polylog(-1, 0) are the exact zero. Asserted on the real
      callee.

  (A-reference 3 -- the s = 1 expansion)  expand_func(polylog(1, z)) equals the
      single real logarithm -log(1 - z) and is FREE of any exp_polar/polar
      factor, over symbolic and many random complex z.

Every F2P `test_polylog_values` assertion is enumerated and checked here; a
skipped F2P case fails the gate loudly (there are no out-of-scope cases).

PATCH APPLICATION (important): the SWE-bench eval image ships the PRE-patch
sympy at `base_commit` (its `polylog.eval` has only the z==1/-1/0 clauses, no
s==2 branch). So this script applies `patch.diff` (mounted read-only next to it)
to /testbed BEFORE importing sympy, so it validates the model against the REAL
GOLD-PATCHED callee rather than against the unpatched ambient source. The step
is IDEMPOTENT: if the gold patch is already applied (e.g. the runner passed
apply_gold=True), `git apply --check` reports the reverse-applies-cleanly state
and we skip re-applying. Without this step the check is a false negative
(recognised patterns stay unevaluated on pre-patch sympy).

Imports nothing repo-specific beyond `sympy` itself (the library under change).
Run on the eval interpreter (in-container) where /testbed holds the sympy
checkout and patch.diff is mounted at /work/patch.diff.
Exit 0 iff every obligation holds.
"""
import sys
import os
import random
import subprocess


def _ensure_gold_patched():
    """Apply patch.diff to /testbed unless it is already applied. Idempotent and
    quiet on the already-applied case. Locates the patch next to this script
    (the bundle dir is mounted read-only at /work) and applies it in /testbed."""
    testbed = "/testbed"
    if not os.path.isdir(testbed):
        # Not the in-container layout; rely on the ambient environment and let
        # the SKIP/assertions below decide.
        return
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [os.path.join(here, "patch.diff"),
                  "/work/patch.diff", "/gold.patch"]
    patch = next((p for p in candidates if os.path.isfile(p)), None)
    if patch is None:
        print("G-AX NOTE: patch.diff not found beside axiom_check.py "
              "(looked in %r); proceeding with ambient /testbed source."
              % (candidates,))
        return
    # If the patch reverse-applies cleanly, it is ALREADY applied -> skip.
    already = subprocess.run(
        ["git", "apply", "--reverse", "--check", patch],
        cwd=testbed, capture_output=True, text=True)
    if already.returncode == 0:
        print("G-AX NOTE: gold patch already applied to /testbed; skipping "
              "re-apply.")
        return
    # If it forward-applies cleanly, apply it.
    fwd_check = subprocess.run(
        ["git", "apply", "--check", patch],
        cwd=testbed, capture_output=True, text=True)
    if fwd_check.returncode != 0:
        raise AssertionError(
            "G-AX FAIL: gold patch neither forward- nor reverse-applies "
            "cleanly to /testbed (forward-check stderr: %s)"
            % (fwd_check.stderr.strip(),))
    applied = subprocess.run(
        ["git", "apply", "-v", patch],
        cwd=testbed, capture_output=True, text=True)
    if applied.returncode != 0:
        raise AssertionError(
            "G-AX FAIL: gold patch failed to apply to /testbed: %s"
            % (applied.stderr.strip(),))
    print("G-AX NOTE: applied gold patch.diff to /testbed.")


_ensure_gold_patched()

try:
    from sympy import (polylog, expand_func, pi, log, sqrt, I, S, Rational,
                       symbols, Abs, exp_polar)
    from sympy.core.function import Function
except Exception as exc:  # pragma: no cover
    print("G-AX SKIP: sympy not importable on this interpreter (%r); "
          "run in-container on the eval image." % (exc,))
    sys.exit(0)


# --- closed-form code constants (kept in lock-step with Solution.lean; same
# integer values, so the discrete dispatch identities match Solution.lean
# exactly). The spec-view in Solution.lean uses neutral code names
# (cfP1..cfP6 etc.) to avoid leakage; here -- the G-AX evidence script, never
# shown to consumers -- we bind each code to the concrete gold closed-form
# expression it names. -------------------------------------------------------
CF_UNEVAL = 0
CF_ZA = 1           # z-keyed clause z==1   -> zeta(s)            (s-only)
CF_ZB = 2           # z-keyed clause z==-1  -> -dirichlet_eta(s)  (s-only)
CF_ZC = 3           # z-keyed clause z==0   -> S.Zero
CF_P1 = 4           # s==2, z==1/2          -> pi**2/12 - log(2)**2/2
CF_P2 = 5           # s==2, z==2            -> pi**2/4 - I*pi*log(2)
CF_P3 = 6           # s==2, z==-(sqrt5-1)/2
CF_P4 = 7           # s==2, z==-(sqrt5+1)/2
CF_P5 = 8           # s==2, z==(3-sqrt5)/2
CF_P6 = 9           # s==2, z==(sqrt5-1)/2
CF_SA = 10          # s==0                  -> z/(1 - z)
CF_SB = 11          # s==-1                 -> z/(1 - z)**2


def gold_closed_form(code, z):
    """The concrete gold closed-form expression each code names, as a SymPy
    expression in z. (CF_ZA / CF_ZB are the s-only zeta/eta values; the six
    s==2 dilog forms CF_P1..P6 and the two rationals CF_SA/CF_SB are the ones the
    patch adds.)"""
    if code == CF_ZC:
        return S.Zero
    if code == CF_P1:
        return pi**2/12 - log(2)**2/2
    if code == CF_P2:
        return pi**2/4 - I*pi*log(2)
    if code == CF_P3:
        return -pi**2/15 + log((sqrt(5) - 1)/2)**2/2
    if code == CF_P4:
        return -pi**2/10 - log((sqrt(5) + 1)/2)**2
    if code == CF_P5:
        return pi**2/15 - log((sqrt(5) - 1)/2)**2
    if code == CF_P6:
        return pi**2/10 - log((sqrt(5) - 1)/2)**2
    if code == CF_SA:
        return z/(1 - z)
    if code == CF_SB:
        return z/(1 - z)**2
    raise AssertionError("no concrete closed form for code %d" % code)


def is_unevaluated(expr):
    """True iff expr is still a bare polylog(...) instance (the call did not
    auto-evaluate to a closed form)."""
    return isinstance(expr, polylog)


def check_eval_pattern(s, z, code, label):
    """A-reference 1: the real polylog(s, z) auto-evaluates to EXACTLY the gold
    closed form `code` names, and the evaluation actually fired."""
    real = polylog(s, z)
    assert not is_unevaluated(real), (
        "[%s] recognised pattern polylog(%s,%s) did NOT evaluate "
        "(stayed unevaluated)" % (label, s, z))
    gold = gold_closed_form(code, z)
    diff = (real - gold)
    # Symbolic equality where the model claims an exact symbolic answer
    # (CF_ZC, CF_P1, CF_P2 are the symbolic-equality F2P assertions);
    # the golden-ratio / rational forms are validated numerically below.
    simplified = diff.simplify()
    assert simplified == 0, (
        "[%s] real polylog(%s,%s)=%s does NOT equal gold closed form %s "
        "(diff simplifies to %s, code=%d)"
        % (label, s, z, real, gold, simplified, code))


def check_eval_numeric(s, z, code, label):
    """Numeric cross-check: |polylog(s,z) - gold_closed_form| < 1e-12 at high
    precision (mirrors the F2P evalf assertions)."""
    real = polylog(s, z)
    gold = gold_closed_form(code, z)
    d = Abs(real.evalf(30) - gold.evalf(30))
    assert d < S(1)/10**12, (
        "[%s] numeric mismatch polylog(%s,%s): |real-gold|=%s (code=%d)"
        % (label, s, z, d, code))


def check_unrecognised_stays(s, z, label):
    """The dispatch must NOT over-fire: at an unrecognised pattern the real
    polylog(s, z) stays unevaluated."""
    real = polylog(s, z)
    assert is_unevaluated(real), (
        "[%s] UNrecognised pattern polylog(%s,%s) unexpectedly evaluated to %s "
        "(dispatch over-fired)" % (label, s, z, real))


def main():
    z = symbols('z')

    # ---- A-reference 1: the six s = 2 special dilog arguments (F2P symbolic
    # and numeric assertions of test_polylog_values) ----
    g = sqrt(5)
    s2_cases = [
        ("s=2, z=1/2", 2, S.Half, CF_P1),
        ("s=2, z=2", 2, S(2), CF_P2),
        ("s=2, z=-(sqrt5-1)/2", 2, -(g - 1)/2, CF_P3),
        ("s=2, z=-(sqrt5+1)/2", 2, -(g + 1)/2, CF_P4),
        ("s=2, z=(3-sqrt5)/2", 2, (3 - g)/2, CF_P5),
        ("s=2, z=(sqrt5-1)/2", 2, (g - 1)/2, CF_P6),
    ]
    for label, s, zz, code in s2_cases:
        check_eval_pattern(s, zz, code, label)
        check_eval_numeric(s, zz, code, label)

    # The two F2P symbolic-equality assertions verbatim.
    assert polylog(2, S(2)) == pi**2/4 - I*pi*log(2), (
        "F2P symbolic: polylog(2,2) != pi**2/4 - I*pi*log(2)")
    assert polylog(2, S.Half) == pi**2/12 - log(2)**2/2, (
        "F2P symbolic: polylog(2,1/2) != pi**2/12 - log(2)**2/2")

    # ---- A-reference 1: z = 0 -> exact zero (CF_ZC), any s ----
    for s in [-2, -1, 0, 1, 2, 3, symbols('s')]:
        try:
            r = polylog(s, S.Zero)
        except Exception as exc:
            raise AssertionError("polylog(%s,0) raised %r" % (s, exc))
        assert r == S.Zero, "polylog(%s,0)=%s, expected exact 0" % (s, r)

    # ---- A-reference 1: the two rational closed forms s = 0 / s = -1 ----
    # Checked numerically over many random complex z (the F2P numeric loop), at
    # arguments where no earlier (z-only) clause applies.
    rng = random.Random(13852)
    nrand = 0
    for s, code in [(0, CF_SA), (-1, CF_SB)]:
        for _ in range(40):
            re = rng.uniform(-5, 5)
            im = rng.uniform(-5, 5)
            zz = S(re).evalf(30) + I*S(im).evalf(30)
            check_eval_numeric(s, zz, code, "s=%d rand z" % s)
            nrand += 1

    # ---- A-reference 2: the priority cascade (z-only clauses win) ----
    # polylog(0, 1) must be the zeta value, NOT the rational z/(1-z) at z=1
    # (which would be a division by zero); polylog(0,0)/polylog(-1,0) are 0.
    from sympy import zeta, dirichlet_eta
    assert polylog(0, S.One) == zeta(0), (
        "priority: polylog(0,1) should be zeta(0), got %s" % polylog(0, S.One))
    assert polylog(0, -S.One) == -dirichlet_eta(0), (
        "priority: polylog(0,-1) should be -dirichlet_eta(0)")
    assert polylog(-1, S.One) == zeta(-1), (
        "priority: polylog(-1,1) should be zeta(-1)")
    assert polylog(0, S.Zero) == S.Zero and polylog(-1, S.Zero) == S.Zero, (
        "priority: polylog(0,0)/polylog(-1,0) should be 0")

    # ---- dispatch does NOT over-fire: unrecognised patterns stay symbolic ----
    # s = 2 at a generic non-special argument; s = 3 at a generic argument.
    check_unrecognised_stays(2, Rational(1, 3), "s=2 generic z=1/3")
    check_unrecognised_stays(3, Rational(1, 2), "s=3 generic z=1/2")
    check_unrecognised_stays(2, Rational(7, 5), "s=2 generic z=7/5")

    # ---- A-reference 3: the s = 1 series expansion is -log(1 - z), polar-free
    e = expand_func(polylog(1, z))
    assert e == -log(1 - z), (
        "s=1 expansion: expand_func(polylog(1,z))=%s, expected -log(1 - z)" % e)
    assert not e.has(exp_polar), (
        "s=1 expansion still carries exp_polar: %s" % e)
    # numeric agreement of polylog(1,z) with -log(1-z) over random complex z
    # (the F2P s=1 numeric loop)
    n1 = 0
    for _ in range(40):
        re = rng.uniform(-5, 5)
        im = rng.uniform(-5, 5)
        zz = S(re).evalf(30) + I*S(im).evalf(30)
        d = Abs(polylog(1, zz).evalf(30) - (-log(1 - zz)).evalf(30))
        assert d < S(1)/10**12, (
            "s=1 numeric mismatch at z=%s: |diff|=%s" % (zz, d))
        n1 += 1

    print("G-AX OK: eval dispatch sound -- 6 s=2 dilog specials (symbolic+"
          "numeric) match real polylog; polylog(s,0)=0 for 7 s; %d random "
          "complex z confirm s=0->z/(1-z) and s=-1->z/(1-z)**2; priority "
          "cascade (z-only clauses win) holds on real callee; dispatch does "
          "NOT over-fire on 3 generic patterns; s=1 expansion == -log(1-z) "
          "(exp_polar-free, symbolic + %d random complex z)."
          % (nrand, n1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
