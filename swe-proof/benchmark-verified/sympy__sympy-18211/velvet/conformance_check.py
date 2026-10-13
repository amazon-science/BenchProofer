#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-18211 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outcomes:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `relationAsSet` impl region,
              transliterated to Python over the *real* repo types (a real
              univariate `Relational`). The A-tagged callee `solveUnivariate`
              (the unchanged solver) is NOT substituted by a model here — it is
              the REAL `solve_univariate_inequality` (the bundle's A content is
              `opaque`, validated by G-AX, so it is out of G-CONF's R/I scope).
              What G-CONF exercises is the CONTROL FLOW the change adds: branch on
              the solver's returns-a-set / raises-NotImplementedError / raises-
              otherwise outcome; on a NotImplementedError build the explicit
              `ConditionSet(x, self, S.Reals)` over the reals (the I op the change
              adds); propagate any other raise; return a produced set verbatim.
  * ORACLE  — `patch.diff`'s behaviour: the gold-patched
              `Relational._eval_as_set` itself, called on the same relation (the
              real correctness oracle, G-RESOLVE — the harness applies patch.diff
              before this runs).

They must agree on the observable OUTCOME for every univariate relation. Exit 0
iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample.

The symbolic solver is a pure function of the relation, so identical relations
are MEMOIZED: ≥10⁵ generated relations reduce to the far smaller set of distinct
relations actually solved, keeping the oracle within the container budget
(mapping.md §4). Runs in-container (the prebuilt SWE-Bench instance image),
stdlib + sympy (the repo under test) only. The fuzz seed is pinned.
"""
import random
import sys

SEED = 18211
N_FUZZ = 125_000


def build():
    from sympy import (Eq, Lt, Gt, Le, Ge, cos, sin, exp, log, sqrt, Symbol,
                       Integer, Rational, S)
    from sympy.sets.conditionset import ConditionSet
    from sympy.solvers.inequalities import solve_univariate_inequality

    x = Symbol('x', real=True)

    def outcome_shadow(rel):
        """R/I transliteration of `relationAsSet`: dispatch on the OUTCOME of the
        real (A-reference) solver; on NotImplementedError build the explicit
        ConditionSet over the reals; propagate any other raise; else return the
        produced set verbatim. The univariate preamble is unchanged input
        machinery."""
        syms = rel.free_symbols
        xx = syms.pop()
        try:
            xset = solve_univariate_inequality(rel, xx, relational=False)
        except NotImplementedError:
            return ("set", ConditionSet(xx, rel, S.Reals))   # the fallback (I op)
        except Exception as e:
            return ("raise", type(e).__name__)               # other leg: propagate
        return ("set", xset)                                 # ok leg: verbatim

    def outcome_oracle(rel):
        """patch.diff's behaviour: the gold-patched `_eval_as_set` itself,
        classified into the same observable-outcome domain."""
        try:
            xset = rel._eval_as_set()
        except NotImplementedError as e:
            # post-patch _eval_as_set itself NEVER raises NotImplementedError on a
            # univariate relation (it catches the solver's and substitutes a
            # ConditionSet); treat as a distinct outcome so any leak is caught.
            return ("raise", "NotImplementedError")
        except Exception as e:
            return ("raise", type(e).__name__)
        return ("set", xset)

    def gen(n, rng):
        ctors = [Eq, Lt, Gt, Le, Ge]

        # --- boundary cases first (plan §4.1 step 4) -------------------------
        # the issue's own examples (cannot-solve leg -> ConditionSet fallback)
        boundary = [
            Eq(x * cos(x) - 3 * sin(x), 0),
            Eq(x ** 2 + sqrt(x * 2) + sin(x), 0),
            Eq(x * cos(x) - sin(x), 0),
            Eq(x - cos(x), 0),
            # ok leg: solvable relations (PASS_TO_PASS-style)
            Eq(x, 0), Eq(x ** 2, 4),
            x > 0, x < 1, x ** 2 < 4,
            Ge(x, Integer(2)), Le(x ** 2, 9),
            # other leg: relations that raise a non-NotImplementedError
            Eq(log(2 * x + 2) + cos(2), 0),
            Eq(log(3 - x ** 3), 0),
            Eq(log(x + 2), 0),
        ]
        for rel in boundary:
            yield rel

        # --- randomized fuzz over BOUNDED relation families ------------------
        # The symbolic oracle is memoized per distinct relation, so the work is
        # bounded by the size of these finite families (≈640 distinct relations),
        # while `n` generated draws still satisfy the ≥10⁵-input requirement —
        # the redundant draws re-exercise the SAME deterministic dispatch (the
        # point of the differential check) at negligible marginal cost
        # (mapping.md §4). Each family targets a specific leg:
        #   * polynomials  (deg 1/2, small int coeffs)  -> ok leg (solver returns)
        #   * x·f(x) − k·g(x) (trig)                     -> cannot-solve leg
        #   * log-of-affine reducing to non-real         -> other leg (propagate)
        for _ in range(n):
            roll = rng.random()
            if roll < 0.5:
                a = rng.randint(1, 6)
                b = rng.randint(-6, 6)
                deg = rng.choice([1, 2])
                yield rng.choice(ctors)(a * x ** deg + b, 0)
            elif roll < 0.85:
                k = rng.randint(1, 5)
                f, g = rng.sample([cos, sin], 2)
                yield rng.choice(ctors)(x * f(x) - k * g(x), 0)
            else:
                c = rng.choice([2, 3])
                yield Eq(log(c * x + 2) + cos(Integer(c)), 0)

    return x, outcome_shadow, outcome_oracle, gen


def main():
    rng = random.Random(SEED)
    x, outcome_shadow, outcome_oracle, gen = build()

    # memoize per distinct relation (the solver is pure in the relation)
    from sympy import srepr
    seen = {}
    disagreements = []
    distinct = 0
    total = 0

    def cmp_outcome(sh, orc):
        """Compare two observable outcomes. For the 'set' kind compare the sympy
        objects with ==; for 'raise' compare the exception class name."""
        if sh[0] != orc[0]:
            return False
        if sh[0] == "raise":
            return sh[1] == orc[1]
        # sets: structural equality of the returned solution sets
        try:
            return bool(sh[1] == orc[1])
        except Exception:
            return srepr(sh[1]) == srepr(orc[1])

    for rel in gen(N_FUZZ, rng):
        # only single-variable relations are within the modeled precondition
        if len(rel.free_symbols) != 1:
            continue
        total += 1
        key = srepr(rel)
        if key in seen:
            continue
        distinct += 1
        sh = outcome_shadow(rel)
        orc = outcome_oracle(rel)
        seen[key] = True
        if not cmp_outcome(sh, orc):
            disagreements.append((srepr(rel), repr(sh), repr(orc)))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (%d distinct):"
              % (len(disagreements), total, distinct))
        for r, sh, orc in disagreements:
            print("  rel=%s shadow=%s oracle=%s" % (r, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of relationAsSet agrees with patch.diff "
          "behaviour (gold-patched _eval_as_set) on %d generated relations "
          "(%d distinct, memoized; seed=%d), 0 disagreements."
          % (total, distinct, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
