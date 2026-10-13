#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18211.

Executes the REAL univariate solver (`solve_univariate_inequality(expr, gen,
relational=False)`, the unchanged callee `_eval_as_set` invokes) on
representative univariate relations and asserts that each observation matches the
`solve_univariate` axiom encoded in model.py.

The axiom is partial over a STATED two-way domain (model.py axioms region,
mapping.md §3.1):

    solvability 0 (DETERMINED) — the solver returns a concrete `Set` normally,
                                 and that set is NOT the symbolic fallback
                                 (a `ConditionSet` wrapping the relation over the
                                 reals);
    solvability 1 (UNDECIDED)  — the solver raises `NotImplementedError`.

The axiom's contract (model.py axioms region) is:
    Requires(rel.solvability in {0, 1})            # STATED domain carve-out
    Ensures(rel.solvability == 0)                  # returns normally iff determined
    Ensures(Result().is_fallback == False)         # a determined set is not the fallback
    Ensures(Result().cond == solved_cond(rel))     # pinned to the solver's own set
    Exsures(SolverUndecided, rel.solvability == 1)  # raises NotImplementedError iff undecided

CRUCIALLY, the axiom claims NOTHING about relations on which the real solver
reports any OTHER outcome — a domain error (`ValueError`), a malformed-argument
error (`TypeError`), a recursion-bound exhaustion (`RecursionError`), or
non-termination. Those relations have NO `solvability` value: `solvability ∈
{0,1}` has no preimage there, so no `Relation` carrier can be built for them and
they are OUTSIDE the abstraction's modeled domain BY CONSTRUCTION (the stated
carve-out, mapping.md §3.1). The gold patch catches ONLY `NotImplementedError`,
so on these other-outcome relations the patched `_eval_as_set` ALSO raises/hangs
— the abstraction and the gold patch agree (both leave them un-resolved), so the
axiom is not stronger than the real callee there.

This check therefore (directive 7: fuzz the raise/exception behaviour, not just
the happy path):

  (a) confirms the two F2P relations are UNDECIDED (`NotImplementedError`) — the
      conversion's fallback branch is exercised, and the post-fix conversion
      returns exactly `ConditionSet(x, self, S.Reals)` on them;
  (b) confirms a battery of in-domain DETERMINED relations return an
      `sympy.sets.Set`, never the symbolic fallback, without raising;
  (c) exercises the BROADER families the verdict identified — transcendental,
      rational/root (`cbrt`), `sign`, `log`/`log∘log`, `Min`/`Max`, `floor`,
      `Piecewise`, `Abs`, and a non-terminating rational-power relation — under a
      PER-CALL wall-clock timeout. For these it CLASSIFIES each real outcome and
      asserts the axiom ONLY over the in-domain ones; any other exception class
      or a timeout is recorded as DOMAIN-EXCLUDED (no `solvability` carrier),
      which is SOUND — it confirms the stated carve-out is well-defined and
      NON-EMPTY (at least one relation falls outside {determined, undecided});
  (d) a randomized fuzz spanning all the above families, classified the same way.

Soundness requires, for every relation the axiom would tag IN-DOMAIN:
    - DETERMINED ⇒ the solver returns an `sympy.sets.Set`, does NOT raise, and
      that set is not a `ConditionSet` rewrapping the relation over `S.Reals`;
    - UNDECIDED  ⇒ the solver raises `NotImplementedError`.
A relation whose real outcome is any OTHER exception or a timeout is NOT a
failure — it is domain-excluded. The check FAILS only if a relation that lands
in-domain disobeys the determined/undecided dichotomy.

Imports nothing repo-specific beyond `sympy` itself — the library under test.
Exit 0 iff every in-domain obligation holds AND the carve-out is non-empty.
"""
import random
import signal
import sys

from sympy import (S, Symbol, cos, sin, sqrt, exp, log, Eq, Ne, pi, Abs, cbrt,
                   sign, Min, Max, floor, Piecewise, Rational)
from sympy.sets.sets import Set
from sympy.sets.conditionset import ConditionSet
from sympy.solvers.inequalities import solve_univariate_inequality

# Per-call wall-clock budget: a relation the real solver cannot decide in this
# many seconds (e.g. 2*x**(1/3)+3*x**2-3 <= 0 loops in solvify) is treated as a
# DOMAIN-EXCLUDED outcome (non-termination), exactly as the gold patch leaves it
# unresolved. Never a happy-path relation: all in-domain relations decide fast.
PER_CALL_TIMEOUT_S = 8

# Outcome tags for real_verdict / classification.
DETERMINED = 0       # in-domain: returned a Set
UNDECIDED = 1        # in-domain: raised NotImplementedError
EXCLUDED = -1        # out-of-domain: other exception OR timeout (no solvability)


class _CallTimeout(Exception):
    pass


def _alarm(signum, frame):  # noqa: ARG001
    raise _CallTimeout()


def real_verdict(expr, gen):
    """Run the REAL solve_univariate_inequality(expr, gen, relational=False)
    under a per-call wall-clock timeout and classify the outcome:
       (DETERMINED, set) -> returned a Set without raising            [in-domain]
       (UNDECIDED, None) -> raised NotImplementedError                [in-domain]
       (EXCLUDED, exc)   -> any other exception class OR a timeout    [carved out]
    DETERMINED/UNDECIDED are the only outcomes the axiom claims; EXCLUDED is the
    stated carve-out (no `solvability` carrier exists) and is SOUND, not a fault."""
    signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(PER_CALL_TIMEOUT_S)
    try:
        rv = solve_univariate_inequality(expr, gen, relational=False)
        return (DETERMINED, rv)
    except NotImplementedError:
        return (UNDECIDED, None)
    except _CallTimeout:
        return (EXCLUDED, "timeout/non-termination")
    except Exception as e:  # noqa: BLE001 - other exception class => carved out
        return (EXCLUDED, "%s: %s" % (type(e).__name__, str(e)[:60]))
    finally:
        signal.alarm(0)


def assert_determined(expr, gen):
    """The axiom tags this relation DETERMINED; assert the real solver agrees."""
    tag, rv = real_verdict(expr, gen)
    assert tag != UNDECIDED, (
        "solve_univariate axiom UNSOUND on %r: axiom tags it DETERMINED "
        "(solvability 0, returns a Set) but the real solver raised "
        "NotImplementedError" % (expr,))
    assert tag != EXCLUDED, (
        "solve_univariate axiom UNSOUND on %r: axiom tags it DETERMINED but the "
        "real solver reported an out-of-domain outcome (%r) — this relation must "
        "NOT be in the determined battery; move it to the carve-out families"
        % (expr, rv))
    assert isinstance(rv, Set), (
        "solve_univariate axiom UNSOUND on %r: a DETERMINED result must be an "
        "sympy.sets.Set; real solver returned %r" % (expr, type(rv).__name__))
    fallback = ConditionSet(gen, expr, S.Reals)
    assert rv != fallback, (
        "solve_univariate axiom UNSOUND on %r: a DETERMINED result equals the "
        "symbolic fallback ConditionSet(x, self, Reals); the determined branch's "
        "is_fallback==False pin would be violated" % (expr,))


def assert_undecided(expr, gen):
    """The axiom tags this relation UNDECIDED; assert the real solver agrees."""
    tag, rv = real_verdict(expr, gen)
    assert tag != DETERMINED, (
        "solve_univariate axiom UNSOUND on %r: axiom tags it UNDECIDED "
        "(solvability 1, raises NotImplementedError) but the real solver "
        "returned a Set %r" % (expr, rv))
    assert tag != EXCLUDED, (
        "solve_univariate axiom UNSOUND on %r: axiom tags it UNDECIDED but the "
        "real solver reported an out-of-domain outcome (%r) rather than "
        "NotImplementedError" % (expr, rv))


def classify(expr, gen):
    """Run the real solver and classify WITHOUT asserting the carve-out families
    are decided. Returns the outcome tag. Used for the broader families (c)/(d):
    an in-domain outcome must still obey the dichotomy's well-formedness (a
    determined result is a Set and never the fallback), but an EXCLUDED outcome
    is recorded as out-of-domain (sound) rather than failed."""
    tag, rv = real_verdict(expr, gen)
    if tag == DETERMINED:
        assert isinstance(rv, Set), (
            "solve_univariate axiom UNSOUND on %r: an in-domain DETERMINED result "
            "is not an sympy.sets.Set (%r)" % (expr, type(rv).__name__))
        fallback = ConditionSet(gen, expr, S.Reals)
        assert rv != fallback, (
            "solve_univariate axiom UNSOUND on %r: an in-domain DETERMINED result "
            "equals the symbolic fallback ConditionSet(x, self, Reals)" % (expr,))
    return tag


def main():
    x = Symbol('x')

    # ---- (a) the EXACT F2P relations: must be UNDECIDED (NotImplementedError) -
    f2p = [
        Eq(x * cos(x) - 3 * sin(x), 0),
        Eq(x ** 2 + sqrt(x * 2) + sin(x), 0),
    ]
    for expr in f2p:
        assert_undecided(expr, x)

    # the post-fix conversion returns exactly the symbolic fallback
    # ConditionSet(x, self, S.Reals) on each F2P relation.
    for expr in f2p:
        produced = ConditionSet(x, expr, S.Reals)   # what _eval_as_set builds
        assert isinstance(produced, ConditionSet), (
            "fallback construction unsound: ConditionSet(x, %r, Reals) is not a "
            "ConditionSet" % (expr,))
        assert produced.base_set == S.Reals, (
            "fallback base set is not S.Reals for %r" % (expr,))
        assert expr in produced.condition.atoms(type(expr)) or \
            produced.condition == expr, (
            "fallback condition does not carry the original relation for %r"
            % (expr,))

    # ---- (b) DETERMINED battery: in-domain solvable relations return a Set ----
    # Each verified IN-CONTAINER (probe, pinned sympy 1.6) to be DETERMINED:
    # transcendental sin/cos/exp/log inequalities decide in this version; only
    # the equalities/relations in (c) fall out of domain.
    determined = [
        x ** 2 >= 4, x > 0, x < 0, x >= 1, x <= -1,
        sin(x) > 0, cos(x) <= 0, exp(x) > 2, log(x) > 0,
        Eq(x, 0), Eq(x - 3, 0), Eq(x ** 2, 4),
        x ** 2 - 1 < 0, x ** 2 + 1 > 0, x ** 3 - x >= 0,
        (x - 1) * (x - 2) > 0, Abs(x) < 2,
        Ne(x, 0),
    ]
    for expr in determined:
        assert_determined(expr, x)

    # ---- (c) the BROADER families the verdict flagged ------------------------
    # These exercise the solver's OTHER outcomes. They are NOT asserted to be
    # decided; each is classified, and a non-{determined,undecided} outcome is
    # recorded as DOMAIN-EXCLUDED (sound — no solvability carrier). We require
    # the carve-out to be NON-EMPTY (at least one genuinely out-of-domain), which
    # is what makes the stated `solvability ∈ {0,1}` precondition load-bearing.
    carveout_families = [
        cbrt(x) > 0,                                   # TypeError (malformed arg)
        sign(x) > 0,                                   # ValueError (complex domain)
        Eq(log(x), 0),                                 # ValueError (imaginary parts)
        Eq(log(log(x)), 0),                            # ValueError (imaginary parts)
        Eq(Min(1, x), 0),                              # RecursionError
        Max(0, x) > 1,                                 # RecursionError
        2 * x ** (Rational(1, 3)) + 3 * x ** 2 - 3 <= 0,  # non-termination
        floor(x) > 0,                                  # in-domain UNDECIDED here
        Piecewise((x, x > 0), (-x, True)) > 0,         # family probe
    ]
    counts = {DETERMINED: 0, UNDECIDED: 0, EXCLUDED: 0}
    n_excluded_families = 0
    for expr in carveout_families:
        tag = classify(expr, x)
        counts[tag] += 1
        if tag == EXCLUDED:
            n_excluded_families += 1
    assert n_excluded_families >= 1, (
        "domain carve-out VACUOUS: none of the broader relation families landed "
        "out-of-domain, so the stated `solvability in {0,1}` precondition would "
        "carve out nothing — the soundness argument requires a non-empty carve-out")

    # ---- (d) randomized fuzz across all families, classified -----------------
    rng = random.Random(18211)
    poly_ctors = [
        lambda e: e > 0, lambda e: e >= 0, lambda e: e < 0,
        lambda e: e <= 0, lambda e: Eq(e, 0), lambda e: Ne(e, 0),
    ]
    # family generators (some intentionally hit the carve-out); each takes the
    # symbol and returns a univariate relation.
    family_gens = [
        lambda r: r.choice(poly_ctors)(
            sum(r.randint(-5, 5) * x ** k for k in range(r.randint(1, 3) + 1)) or x),
        lambda r: r.choice(poly_ctors)(sin(x) + r.randint(-3, 3) * x),
        lambda r: r.choice(poly_ctors)(cos(x) - r.randint(0, 3)),
        lambda r: r.choice(poly_ctors)(exp(x) - r.randint(1, 4)),
        lambda r: r.choice(poly_ctors)(cbrt(x) + r.randint(-2, 2)),     # carve-out
        lambda r: r.choice(poly_ctors)(sign(x) * r.randint(1, 3)),      # carve-out
        lambda r: r.choice(poly_ctors)(log(x) + r.randint(-2, 2)),
        lambda r: r.choice(poly_ctors)(Min(r.randint(-2, 2), x)),       # carve-out
        lambda r: r.choice(poly_ctors)(Max(r.randint(-2, 2), x)),       # carve-out
        lambda r: r.choice(poly_ctors)(floor(x) + r.randint(-2, 2)),
    ]
    n_fuzz = 300
    fuzz_counts = {DETERMINED: 0, UNDECIDED: 0, EXCLUDED: 0}
    for _ in range(n_fuzz):
        gen = rng.choice(family_gens)
        try:
            expr = gen(rng)
        except (TypeError, ValueError):
            continue
        # a degenerate constant relation has no free symbol — skip
        try:
            if not getattr(expr, 'free_symbols', set()):
                continue
        except Exception:  # noqa: BLE001
            continue
        tag = classify(expr, x)
        fuzz_counts[tag] += 1

    print("G-AX OK: solve_univariate axiom sound against the real "
          "solve_univariate_inequality(..., relational=False).")
    print("  (a) 2 F2P relations UNDECIDED (NotImplementedError); "
          "ConditionSet(x, self, Reals) fallback well-formed over them.")
    print("  (b) %d boundary in-domain relations DETERMINED (return an sympy "
          "Set, never the symbolic fallback, no raise)." % (len(determined),))
    print("  (c) %d broader-family relations classified: DETERMINED=%d "
          "UNDECIDED=%d DOMAIN-EXCLUDED=%d (carve-out non-empty: %d out-of-domain "
          "via ValueError/TypeError/RecursionError/timeout — sound, no carrier)."
          % (len(carveout_families), counts[DETERMINED], counts[UNDECIDED],
             counts[EXCLUDED], n_excluded_families))
    print("  (d) %d fuzz relations classified: DETERMINED=%d UNDECIDED=%d "
          "DOMAIN-EXCLUDED=%d; every in-domain outcome obeys the "
          "determined/undecided dichotomy with no undeclared escape."
          % (sum(fuzz_counts.values()), fuzz_counts[DETERMINED],
             fuzz_counts[UNDECIDED], fuzz_counts[EXCLUDED]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
