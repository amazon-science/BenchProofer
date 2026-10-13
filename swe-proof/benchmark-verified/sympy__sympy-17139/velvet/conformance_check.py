#!/usr/bin/env python3
"""G-CONF differential conformance for sympy__sympy-17139 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of `refinement.md`: the
control-flow decision of `Solution.lean`'s `powerRewriteStep` `do` block —
transliterated to Python over the real sympy types — differential-tested against
`patch.diff`'s behaviour driven through the REAL patched rewrite at
base_commit+gold.

ORACLE — the gold-patched rewrite itself: `_TR56(rv, f, g, h, max, pow)` from the
patched `sympy/simplify/fu.py`. For a single power node `f(x)**exp` (and for
non-power inputs) `bottom_up(rv, _f)` reduces to one application of the nested
`_f`, so `_TR56(rv, ...)` IS the modeled rewrite step on `rv`.

SHADOW — `powerRewriteStep` transliterated (mapping.md §2):
    matchesPow := rv.is_Pow and rv.base.func == f         (unchanged guard, free Bool)
    expIsReal  := bool(rv.exp.is_real) is True             (the new guard's predicate)
    out        := rv                       if (not matchesPow)
                  rv                       if (matchesPow and not expIsReal)   # the fix
                  <the real downstream>    otherwise        (transformed: free, = real callee)
The unchanged downstream (`transformed`) is left as the real callee, so on the
proceed-branch the shadow equals the oracle by construction; the DISCRIMINATING
content is the guard decision — on the two unchanged branches the shadow predicts
`out == rv`, which the oracle must honour. The middle branch is the behaviour at
issue (a non-real exponent must leave `rv` untouched); pre-patch that branch
instead reached `rv.exp < 0`, which raises `TypeError` for a complex exponent —
asserted below to confirm the guard is load-bearing.

SCOPE OF THE CHECK — only the guard DECISION is differential-tested:
  * shadow predicts UNCHANGED (non-targeted node, or targeted power with a
    non-real exponent — the fix): the real `_f` returns `rv` BEFORE any
    downstream computation, so the oracle must neither raise nor alter `rv`.
    Either failure is a genuine refinement disagreement.
  * shadow predicts PROCEED (targeted power, real exponent): the output is the
    downstream rewrite, modeled as the FREE value `transformed` (refinement A4)
    — the spec, under partial-correctness semantics, pins NOTHING here. So a
    downstream that returns `rv` (exp<0/>max/odd), a rewritten value, OR a raise
    are all admissible. In particular `pow=True` with a real *non-integer*
    exponent (e.g. 3/2) drives `_f` into `perfect_power()`, a PRE-EXISTING
    partiality of the function that the gold patch does not touch (issue 17137
    is solely about NON-real exponents); such a raise is NOT a guard
    disagreement and does not refute the modeled step.

For each (rv, f, g, h, max, pow) we check the guard decision. Exit 0 iff zero
disagreements.

sympy only; the fuzz seed is pinned (mapping.md §4).
"""
import random
import sys

from sympy import sin, cos, tan, Symbol, I, sqrt, Rational, Integer, Pow
from sympy.simplify.fu import _TR56

SEED = 17139

x = Symbol('x')
H = (lambda a: 1 - a)


def shadow_unchanged(rv, f):
    """The guard decision of powerRewriteStep: does the rewrite leave rv
    untouched? True iff (not a targeted power) OR (targeted power, non-real
    exponent). Mirrors mapping.md §2 exactly."""
    matches_pow = bool(rv.is_Pow and rv.base.func == f)
    if not matches_pow:
        return True
    exp_is_real = (rv.exp.is_real is True)
    if not exp_is_real:
        return True            # the fix: non-real exponent -> unchanged
    return False               # proceed to the (unchanged) downstream rewrite


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0

    funcs = [sin, cos, tan]
    G = {sin: cos, cos: sin, tan: cos}    # the partner used as g (only the
                                          # downstream uses g; immaterial to the
                                          # guard, exercised for coverage)

    # Real exponents (guard must NOT fire) and non-real exponents (guard MUST
    # fire) — the F2P discriminators I, 2*I+1, plus a broad mix.
    real_exps = [Integer(k) for k in range(-3, 11)] + [
        Rational(3, 2), Rational(-1, 2), sqrt(2)]
    nonreal_exps = [I, 2*I + 1, 3*I, -I, Rational(1, 2) + I, 4 + 5*I, I*sqrt(2)]

    cases = []
    # targeted and non-targeted powers, real & non-real exponents
    for base_f in funcs:
        for tf in funcs:                       # the rewrite target f
            for e in real_exps + nonreal_exps:
                cases.append((Pow(base_f(x), e), tf))
    # non-power inputs (matchesPow False): must always be unchanged
    for tf in funcs:
        cases.append((sin(x) + cos(x), tf))
        cases.append((x, tf))
        cases.append((Integer(7), tf))
        cases.append((tf(x), tf))

    # fuzz: random base func, target func, exponent (real or non-real)
    for _ in range(4000):
        bf = rng.choice(funcs)
        tf = rng.choice(funcs)
        if rng.random() < 0.5:
            e = rng.choice(real_exps)
        else:
            e = rng.choice(nonreal_exps)
        cases.append((Pow(bf(x), e), tf))

    maxes = [4, 6, 10]
    pows = [False, True]

    for rv, f in cases:
        for mx in maxes:
            for pw in pows:
                count += 1
                g = G[f]
                # The discriminating content of the modeled step is the GUARD
                # decision: does the rewrite return rv unchanged, or proceed to
                # the (unchanged) downstream? The shadow computes that decision
                # from the real sympy types.
                sh_unchanged = shadow_unchanged(rv, f)
                try:
                    oracle = _TR56(rv, f, g, H, max=mx, pow=pw)   # patched callee
                    oracle_unchanged = (oracle == rv)
                    oracle_raised = False
                except Exception as exc:                          # noqa: BLE001
                    oracle_raised = True
                    oracle_unchanged = None
                    oracle_exc = exc

                if sh_unchanged:
                    # Shadow predicts the guard returns rv EARLY (a non-targeted
                    # node, or a targeted power with a non-real exponent — the
                    # fix). The real `_f` then returns rv before reaching any
                    # downstream computation, so the oracle must (a) not raise
                    # and (b) return rv. Either failure is a real disagreement.
                    if oracle_raised:
                        disagreements.append(
                            (rv, f, mx, pw,
                             "shadow=unchanged but ORACLE RAISED %r" % oracle_exc,
                             None))
                    elif not oracle_unchanged:
                        disagreements.append((rv, f, mx, pw, sh_unchanged,
                                              oracle_unchanged))
                else:
                    # Shadow predicts "proceed": out == the real downstream,
                    # which the spec models as the FREE value `transformed`
                    # (mapping.md §2, refinement.md A4) — every downstream value
                    # is admitted, including the unchanged result (exp<0 / >max /
                    # odd exp) AND a partial result. Concretely, with pow=True a
                    # real *non-integer* exponent (e.g. 3/2) drives the real `_f`
                    # into perfect_power(), a PRE-EXISTING partiality of the
                    # function unrelated to this fix (issue 17137 concerns only
                    # NON-real exponents; the gold-patched code raises here too).
                    # Under partial-correctness semantics the spec pins nothing
                    # on this branch, so neither a value nor a raise refutes the
                    # guard refinement — only the guard DECISION is checked, and
                    # the shadow already decided "proceed". No-op.
                    pass
                if len(disagreements) >= 8:
                    break
            if len(disagreements) >= 8:
                break
        if len(disagreements) >= 8:
            break

    # --- the guard is load-bearing: the pre-patch comparison crashes ---------
    # For every non-real exponent, the pre-patch code reached `rv.exp < 0`,
    # which raises for a complex number — exactly the bug. Confirm the
    # discriminator the new guard screens out.
    bug_confirmed = 0
    for e in nonreal_exps:
        rv = Pow(cos(x), e)
        assert rv.exp.is_real is not True, (
            "non-real exponent %r unexpectedly is_real" % e)
        raised = False
        try:
            (rv.exp < 0) == True            # the pre-patch comparison
        except TypeError:
            raised = True
        assert raised, ("pre-patch comparison did not raise on %r; the guard "
                        "would not be load-bearing" % e)
        # post-patch: the targeted power with this exponent is returned unchanged
        assert _TR56(rv, cos, sin, H, max=4, pow=True) == rv, (
            "patched _TR56 altered cos(x)**%r" % e)
        bug_confirmed += 1

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for rv, f, mx, pw, sh, orc in disagreements:
            print("  rv=%s f=%s max=%s pow=%s shadow_unchanged=%s "
                  "oracle_unchanged=%s" % (rv, f, mx, pw, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of powerRewriteStep (non-real exponent => "
          "unchanged) agrees with patch.diff behaviour through the real _TR56 "
          "on %d inputs (seed=%d), 0 disagreements; bug discriminator confirmed "
          "on %d non-real exponents." % (count, SEED, bug_confirmed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
