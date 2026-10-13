#!/usr/bin/env python3
"""G-CONF for sympy__sympy-13878.

Differential test: the shadow of `implementation_arcsinCdf` (built here in
Python, transliterating the Lean impl) vs. the REAL patched
`ArcsinDistribution._cdf`, over >=1e5 fuzzed operand triples. Runs inside the
instance container with the gold patch applied.

WHAT IS COMPARED, and why it is not a single float.

The Lean impl returns `CdfObject.caseSplit cs` — an ORDERED list of
(value, guard) cases. That is an abstract denotation one level above the value
the real method hands back, because the real method submits its ordered case
list to sympy's `Piecewise` constructor and returns whatever that constructor
makes of it. `Piecewise.eval` is entitled to simplify: it drops a case whose
guard decides False, stops at the first case whose guard decides True, and
returns a single bare expression when one case with a True guard is all that is
left. So on free symbolic operands the whole three-case analysis survives, while
on ground numeric operands every guard decides and a single value comes back.

The bridge (mapping.md §2) is therefore the COMPOSITION

    real `_cdf(x)`  ==  Piecewise(*[(case.value, case.guard) for case in cs])

with `cs` the shadow's ordered case list. This script checks exactly that
equality, structurally (sympy `==`, i.e. expression-tree identity, not numeric
agreement), so the relation STRICTNESS of each cutoff and the ORDER of the cases
are both observed — the things a float comparison silently loses. Where the
composition leaves a `Piecewise` standing, the surviving `.args` are also
checked pairwise against the shadow's own cases so the guard's relation class is
compared and not just the printed form. Exceptions are part of the contract too:
where the real method raises, the shadow's composition must raise the same way.

Exit 0 iff zero disagreements.
"""
import random
import sys

SEED = 13878          # pinned in mapping.md
N = 100_000


def shadow_cases(a, b, x):
    """Transliteration of `implementation_arcsinCdf`: the ORDERED case list.

    Mirrors the Lean impl line for line —
      case 0: value 0 under a strict cutoff at the lower endpoint,
      case 1: the inverse-sine profile under a non-strict cutoff at the upper one,
      case 2: value 1 under the catch-all guard.
    `arcsinProfile a b x` is spelled out, matching the Lean `pure` helper.
    """
    from sympy import S, asin, sqrt, pi
    profile = 2 * asin(sqrt((x - a) / (b - a))) / pi
    return [(S.Zero, x < a),
            (profile, x <= b),
            (S.One, True)]


def shadow(a, b, x):
    """The bridge: the shadow's ordered case list, composed with the algebra
    layer's case-split constructor (mapping.md §2)."""
    from sympy import Piecewise
    return Piecewise(*shadow_cases(a, b, x))


def reference(a, b, x):
    """The real patched method, called directly."""
    from sympy.stats.crv_types import ArcsinDistribution
    return ArcsinDistribution(a, b)._cdf(x)


def _call(f, *args):
    """(kind, payload): a value, or the exception class+message."""
    try:
        return ("value", f(*args))
    except Exception as e:            # noqa: BLE001 - the contract includes raising
        return ("raise", "%s: %s" % (type(e).__name__, e))


def _structural_eq(p, q):
    """sympy expression-tree identity, tolerant of unhashable/odd comparisons."""
    try:
        if p == q:
            return True
    except Exception:                 # noqa: BLE001
        pass
    return str(p) == str(q)


def _args_agree(real, shad):
    """When a Piecewise survives, compare surviving cases pairwise: value, guard,
    and the guard's RELATION CLASS (so `<` is never accepted for `<=`)."""
    from sympy import Piecewise
    if not (isinstance(real, Piecewise) and isinstance(shad, Piecewise)):
        return isinstance(real, Piecewise) == isinstance(shad, Piecewise), "kind"
    if len(real.args) != len(shad.args):
        return False, "ncases %d vs %d" % (len(real.args), len(shad.args))
    for i, ((rv, rc), (sv, sc)) in enumerate(zip(real.args, shad.args)):
        if not _structural_eq(rv, sv):
            return False, "case %d value" % i
        if not _structural_eq(rc, sc):
            return False, "case %d guard" % i
        if type(rc) is not type(sc):
            return False, "case %d guard class %s vs %s" % (
                i, type(rc).__name__, type(sc).__name__)
    return True, ""


def operand_pool():
    """Operands of every kind the carrier can denote: FREE (a `Term.sym`, which
    settles no order comparison, so the whole analysis survives) and GROUND
    (literals, the circle constant, rationals, radicals, nested inverse sines —
    which settle guards and let the constructor prune)."""
    from sympy import S, Symbol, Rational, sqrt, pi, asin
    free = [Symbol("a", real=True), Symbol("b", real=True),
            Symbol("x", real=True), Symbol("u", real=True),
            Symbol("a"), Symbol("b"), Symbol("x")]
    ground = [S(0), S(1), S(2), S(3), S(-1), S(-5), S(9), S(4),
              Rational(1, 2), Rational(1, 3), Rational(22, 28), Rational(-7, 3),
              pi, pi / 4, sqrt(2), sqrt(pi), 2 * pi,
              asin(S(1)), asin(S(1)) / 2, S(1) / sqrt(2)]
    return free, ground


def main():
    try:
        from sympy import Symbol, Piecewise
        from sympy.stats.crv_types import ArcsinDistribution
        a_s, b_s, x_s = (Symbol("a", real=True), Symbol("b", real=True),
                         Symbol("x", real=True))
        probe = ArcsinDistribution(a_s, b_s)._cdf(x_s)   # raises if not patched
        assert isinstance(probe, Piecewise), "expected a case split on free operands"
        assert len(probe.args) == 3, "expected three surviving cases on free operands"
    except Exception as e:                                # noqa: BLE001
        print("FAIL: real ArcsinDistribution._cdf unavailable/unexpected: %s" % e)
        return 1

    free, ground = operand_pool()
    pool = free + ground

    rng = random.Random(SEED)
    mismatches = 0
    checked = 0
    saw_three = saw_pruned = saw_bare = saw_raise = 0

    # Deterministic head: every operand-kind combination that matters, so the
    # branch structure of the constructor is exercised on purpose and not only
    # by luck — all-free (the case where the whole analysis survives), each
    # single ground operand, each pair, all ground, and aliasing (x IS a, x IS b).
    A, B, X, U = free[0], free[1], free[2], free[3]
    fixed = [
        (A, B, X), (A, B, U), (free[4], free[5], free[6]),
        (ground[0], B, X), (A, ground[1], X), (A, B, ground[1]),
        (ground[0], ground[1], X), (ground[0], B, ground[1]),
        (A, ground[1], ground[2]), (A, ground[1], ground[0]),
        (ground[0], B, ground[4]), (A, B, A), (A, B, B),
        (ground[0], ground[1], ground[0]), (ground[0], ground[1], ground[1]),
        (ground[0], ground[1], ground[2]), (ground[0], ground[1], ground[4]),
        (ground[4], ground[6], ground[0]), (ground[1], ground[1], ground[1]),
        (ground[2], ground[1], ground[0]), (ground[0], ground[12], ground[1]),
        (ground[0], ground[14], ground[1]), (ground[0], ground[15], ground[1]),
        (ground[0], ground[10], ground[13]), (ground[12], B, X),
    ]

    for i in range(N):
        if i < len(fixed):
            a, b, x = fixed[i]
        else:
            a, b, x = rng.choice(pool), rng.choice(pool), rng.choice(pool)
        rk, rv = _call(reference, a, b, x)
        sk, sv = _call(shadow, a, b, x)
        checked += 1

        if rk == "raise" or sk == "raise":
            if rk != sk or rv != sv:
                mismatches += 1
                if mismatches <= 5:
                    print("  mismatch a=%s b=%s x=%s: real=(%s,%s) shadow=(%s,%s)"
                          % (a, b, x, rk, rv, sk, sv))
            else:
                saw_raise += 1
            continue

        ok = _structural_eq(rv, sv)
        why = "" if ok else "expression"
        if ok:
            agree, why2 = _args_agree(rv, sv)
            if not agree:
                ok, why = False, why2
        if not ok:
            mismatches += 1
            if mismatches <= 5:
                print("  mismatch (%s) a=%s b=%s x=%s: real=%s shadow=%s"
                      % (why, a, b, x, rv, sv))
            continue

        from sympy import Piecewise as _PW
        if isinstance(rv, _PW):
            if len(rv.args) == 3:
                saw_three += 1
            else:
                saw_pruned += 1
        else:
            saw_bare += 1

    # Coverage assertions: a run that never saw the surviving three-case analysis,
    # never saw the constructor prune, and never saw it collapse to a single bare
    # value would not have tested the bridge at all.
    if not (saw_three and saw_pruned and saw_bare):
        print("FAIL: coverage — three-case=%d pruned=%d bare=%d (need all > 0)"
              % (saw_three, saw_pruned, saw_bare))
        return 1
    if mismatches:
        print("FAIL: %d/%d disagreements" % (mismatches, checked))
        return 1
    print("OK: %d inputs, zero disagreements (seed=%d); "
          "three-case=%d pruned=%d bare=%d raise-agree=%d"
          % (checked, SEED, saw_three, saw_pruned, saw_bare, saw_raise))
    return 0


if __name__ == "__main__":
    sys.exit(main())
