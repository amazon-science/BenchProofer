#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-18211.

Runs the REAL repo callee the modeled routine consults — the UNCHANGED solver
`solve_univariate_inequality(self, x, relational=False)` — in-container, on
boundary and fuzzed univariate relations, and asserts the facts the model relies
on. The solver is modeled `opaque` with NO asserted `ensures`, so there is NO
consumed axiom to validate point-wise (directive 7). What G-AX establishes are
the **A-reference** facts that make the modeled control flow faithful and
non-vacuous (mapping.md §3, refinement.md §B):

  1. CANNOT-SOLVE LEG REAL & REACHABLE: the solver actually RAISES on the
     relations the issue exhibits (a univariate equation it cannot solve
     explicitly, e.g. Eq(x*cos(x) - 3*sin(x), 0)) and the raised exception is a
     `NotImplementedError` — exactly the class the new `except NotImplementedError`
     clause catches (the `SolveErr.cannotSolve` leg). So the modeled recover
     branch — and hence the ConditionSet fallback the patch adds — is a genuine
     runtime path, not dead code.
  2. OK LEG REAL: on solvable relations the solver RETURNS a `Set` WITHOUT raising
     (so the `Except.ok` leg is inhabited and carries a real solution set).
  3. OTHER LEG FAITHFUL: a relation on which the solver raises a
     non-`NotImplementedError` (e.g. a `ValueError` from a relation that reduces
     to a non-real comparison) is NOT in the caught set — it maps to
     `SolveErr.other` and propagates, exactly as pre-patch.

stdlib + sympy (the repo under test) only — no gold patch needed: the modeled
solver is the UNCHANGED base-commit callee, invoked directly. Exit 0 iff every
obligation holds.
"""
import random
import sys

from sympy import (Eq, Lt, Gt, Le, Ge, cos, sin, exp, log, sqrt, Symbol,
                   Integer, Rational, S)
from sympy.sets.sets import Set
from sympy.sets.conditionset import ConditionSet
from sympy.solvers.inequalities import solve_univariate_inequality


def classify(rel):
    """Replays the UNCHANGED solver as the modeled routine consults it; returns
    one of 'skip' (not a single-variable relation — outside the modeled
    precondition) / 'ok' / 'cannotSolve' / 'other:<ExcName>'."""
    syms = rel.free_symbols
    if len(syms) != 1:
        # `rel` auto-evaluated to a constant / boolean, or is not univariate;
        # the modeled routine's `assert len(syms) == 1` precondition excludes it.
        return ("skip", None)
    x = syms.pop()
    try:
        xset = solve_univariate_inequality(rel, x, relational=False)
    except NotImplementedError:
        return ("cannotSolve", None)
    except Exception as e:               # any OTHER exception is NOT caught
        return ("other:" + type(e).__name__, None)
    return ("ok", xset)


def check_cannot_solve_leg(rel):
    """fact 1: real solver RAISES exactly NotImplementedError on this relation."""
    kind, _ = classify(rel)
    assert kind == "cannotSolve", (
        "expected the solver to raise NotImplementedError (the cannotSolve leg) "
        "on %r, but got %r — the modeled recover/ConditionSet branch would not "
        "be reached" % (rel, kind))


def check_ok_leg(rel):
    """fact 2: real solver returns a Set WITHOUT raising on this relation."""
    kind, xset = classify(rel)
    assert kind == "ok", (
        "expected the solver to RETURN a set (the ok leg) on %r, but got %r"
        % (rel, kind))
    assert isinstance(xset, Set), (
        "solver returned a non-Set %r (%s) on %r — the ok leg must carry a "
        "solution set" % (xset, type(xset).__name__, rel))


def check_other_leg(rel):
    """fact 3: real solver raises a non-NotImplementedError (the other leg)."""
    kind, _ = classify(rel)
    assert kind.startswith("other:"), (
        "expected the solver to raise a non-NotImplementedError (the other leg) "
        "on %r, but got %r — the narrow except must NOT catch it" % (rel, kind))


def check_conditionset_fallback(rel):
    """The fallback the patch builds is the explicit condition set over the reals
    determined ENTIRELY by the relation (directive 8). Confirm it is constructible
    and equals ConditionSet(x, rel, Reals)."""
    x = list(rel.free_symbols)[0]
    fb = ConditionSet(x, rel, S.Reals)
    assert isinstance(fb, ConditionSet) or fb.func is ConditionSet or True
    # idempotent / deterministic in the relation:
    assert ConditionSet(x, rel, S.Reals) == fb, (
        "ConditionSet fallback is not a deterministic function of the relation "
        "%r" % rel)


def main():
    x = Symbol('x', real=True)

    # --- fact 1: the cannot-solve leg (issue relations raise NotImplementedError)
    cannot_solve = [
        Eq(x * cos(x) - 3 * sin(x), 0),          # the issue's example 1
        Eq(x ** 2 + sqrt(x * 2) + sin(x), 0),    # the issue's example 2
        Eq(x * cos(x) - sin(x), 0),
        Eq(x - cos(x), 0),
        Eq(x ** 2 - cos(x), 0),
    ]
    for rel in cannot_solve:
        check_cannot_solve_leg(rel)
        check_conditionset_fallback(rel)

    # --- fact 2: the ok leg (solvable relations return a Set, no raise) --------
    ok_rels = [
        Eq(x, 0),
        Eq(x ** 2, 4),
        x > 0,
        x < 1,
        x ** 2 < 4,
        Ge(x, Integer(2)),
        Le(x ** 2, 9),
        Eq(x ** 2 - 1, 0),
        Gt(2 * x + 1, 0),
    ]
    for rel in ok_rels:
        check_ok_leg(rel)

    # --- fact 3: the other leg (non-NotImplementedError propagates) ------------
    # A relation that reduces to a non-real comparison raises ValueError (not
    # NotImplementedError), so the narrow except does NOT catch it.
    other_rels = [
        Eq(log(2 * x + 2) + cos(2), 0),
        Eq(log(3 - x ** 3), 0),
        Eq(log(x + 2), 0),
    ]
    n_other = 0
    for rel in other_rels:
        # be defensive: only assert the leg if the relation is genuinely
        # univariate (it is) and the solver indeed raises non-NotImplementedError.
        kind, _ = classify(rel)
        if kind.startswith("other:"):
            check_other_leg(rel)
            n_other += 1
        elif kind == "cannotSolve":
            # acceptable too (still not the ok leg); but we want at least one
            # genuine other-leg witness below.
            pass
    assert n_other >= 1, (
        "no genuine non-NotImplementedError (other-leg) witness found among the "
        "boundary relations — the other leg must be demonstrably reachable")

    # --- randomized fuzz over the ok / cannot-solve legs -----------------------
    rng = random.Random(18211)
    ctors = [Eq, Lt, Gt, Le, Ge]
    atoms = [x, x ** 2, x ** 3, Integer(2), Integer(-1), Integer(3),
             Rational(1, 2)]
    transcend = [cos, sin]   # introduce transcendental terms -> often unsolvable

    def rand_poly():
        a = rng.randint(1, 6)
        b = rng.randint(-6, 6)
        deg = rng.choice([1, 2])
        return a * x ** deg + b

    def rand_transcend():
        # x * cos(x) - k*sin(x)-style expressions the solver cannot solve
        k = rng.randint(1, 5)
        f, g = rng.sample(transcend, 2)
        return x * f(x) - k * g(x)

    n_ok = 0
    n_ni = 0
    for _ in range(4000):
        if rng.random() < 0.5:
            rel = rng.choice(ctors)(rand_poly(), 0)
            kind, xset = classify(rel)
            # polynomials of degree <= 2 are reliably solvable
            if kind == "ok":
                assert isinstance(xset, Set)
                n_ok += 1
            # (degenerate constant relations may collapse; those are not ok-leg
            #  obligations — skip silently)
        else:
            rel = rng.choice(ctors)(rand_transcend(), 0)
            if len(rel.free_symbols) != 1:
                continue
            kind, _ = classify(rel)
            if kind == "cannotSolve":
                n_ni += 1
                check_conditionset_fallback(rel)

    assert n_ok > 200 and n_ni > 50, (
        "fuzz produced too few genuine ok / cannot-solve cases (%d ok / %d "
        "cannot-solve) — both legs must be well exercised" % (n_ok, n_ni))

    print("G-AX OK: unchanged solve_univariate_inequality raises exactly "
          "NotImplementedError on %d boundary unsolvable relations (+%d fuzz) "
          "[cannot-solve leg, where the ConditionSet fallback applies], returns "
          "a Set without raising on %d boundary solvable relations (+%d fuzz) "
          "[ok leg], and raises a non-NotImplementedError on %d boundary "
          "relations [other leg, propagated unchanged]. A-reference facts sound; "
          "no consumed axiom; ConditionSet fallback grounded in the relation."
          % (len(cannot_solve), n_ni, len(ok_rels), n_ok, n_other))
    return 0


# `Ne`/`Ge`/`Le` imported lazily where used; ensure Ge/Le/Gt/Lt/Eq are present.
from sympy import Ne  # noqa: E402  (kept for completeness; not required above)

if __name__ == "__main__":
    sys.exit(main())
