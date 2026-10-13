#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13757 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing the observable each pins:
whether the product of an ordinary expression (left) and a polynomial (right) is
CARRIED OUT (evaluated into a single value) or left as a FORMAL, unevaluated
product of the two factors.

  * SHADOW  — the R/I-tagged ops of Solution.lean's `formExpressionTimesPolynomial`
              impl region, transliterated to Python over the real repo carrier.
              The impl branches on the single boolean
              `factorsCombineIntoPolynomial` (mapping.md §2, refinement.md row 1):
              true ⇒ carriedOut, false ⇒ formalProduct. That boolean is whether
              the two factors actually combine into a single polynomial value —
              i.e. whether the left operand can be cast into the polynomial's
              ring. We recompute it here on the real objects via the unchanged
              combination machinery the gold-patched handler reaches
              (`Poly(left_operand, *poly.gens)` succeeds vs. raises
              `PolynomialError`), so the shadow's verdict is driven by the SAME
              datum the carried-out/formal outcome depends on — NOT by the
              precedence comparison the gold patch flips (which, post-gold, is
              True for EVERY `expr * Poly` and so cannot discriminate the formal
              cases).

  * ORACLE  — patch.diff's behaviour: the gold-patched repo at base_commit (the
              harness applies patch.diff before this runs in-container). For each
              left operand `e` and right polynomial `p`, we observe the real
              `e * p` and classify it as carried-out (the product collapsed to a
              single evaluated polynomial value — `result.is_Poly is True`) or
              formal (it is still a standing product `Mul` of the two factors).

They must agree on the verdict for every input. Exit 0 iff zero disagreements;
any disagreement is a mechanical R/I-fidelity counterexample. The fuzz corpus
deliberately includes BOTH polynomial-convertible left operands (numbers,
symbols, powers, linear forms — carried out post-gold) AND non-convertible
transcendental left operands (`sin(x)`, `exp(x)`, … — left FORMAL post-gold even
though the precedence comparison is True), so the check exercises both branches
of the modeled boolean.

Runs in-container (the prebuilt SWE-Bench instance image), sympy + stdlib only.
The fuzz seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

SEED = 13757
N_FUZZ = 100_000


def shadow_verdict(left_operand, poly, PolynomialError):
    """formExpressionTimesPolynomial transliterated: branch on the single boolean
    `factorsCombineIntoPolynomial` (refinement.md row 1). That boolean is whether
    the two factors combine into a single polynomial value — recomputed here on
    the real objects via the unchanged combination machinery the polynomial
    handler reaches (`Poly(left_operand, *poly.gens)` succeeds vs. raises
    `PolynomialError`). true ⇒ 'carriedOut', false ⇒ 'formalProduct'."""
    from sympy import Poly
    try:
        Poly(left_operand, *poly.gens)
        factors_combine = True
    except PolynomialError:
        factors_combine = False
    except Exception:
        # any other failure to cast into the ring ⇒ factors do not combine
        factors_combine = False
    if factors_combine:
        return 'carriedOut'
    return 'formalProduct'


def oracle_verdict(result, e, p):
    """patch.diff's behaviour: classify the real product `e * p`. Carried out iff
    the product collapsed to a single evaluated polynomial value; formal iff it
    is still a standing (unevaluated) product of the two factors."""
    from sympy import Mul
    if getattr(result, 'is_Poly', False) is True:
        return 'carriedOut'
    if isinstance(result, Mul):
        # still a standing product of the operands ⇒ not carried out
        return 'formalProduct'
    # any other evaluated scalar/number value also counts as carried out
    return 'carriedOut'


def left_operands(rng, S, Integer, Rational, symbols, sin, exp, sqrt, pi, I):
    """Yield (label, builder) for ordinary left-hand expressions whose product
    with a polynomial is what the change affects. These are the operands the F2P
    `test_issue_13079` exercises (all polynomial-convertible ⇒ carried out) PLUS
    transcendental / non-convertible operands (left FORMAL post-gold even though
    precedence dominates) PLUS randomized numbers/symbols of both kinds."""
    x = symbols('x')
    # boundary cases first (plan §4.1 step 4): the exact F2P fixture rows
    # (convertible ⇒ carried out) ...
    yield ('symbol-x', x)
    yield ('int-(-2)', -2)
    yield ('S(-2)', S(-2))
    yield ('Integer-3', Integer(3))
    yield ('Rational-1/2', Rational(1, 2))
    yield ('S(0)', S(0))
    yield ('S(1)', S(1))
    yield ('x**2', x**2)
    yield ('I', I)
    yield ('sqrt(2)', sqrt(2))
    yield ('pi', pi)
    yield ('lin-2x+3', 2 * x + 3)
    # ... and NON-convertible transcendental operands (must stay FORMAL):
    yield ('sin(x)', sin(x))
    yield ('exp(x)', exp(x))
    yield ('sin(x)+1', sin(x) + 1)
    yield ('x*exp(x)', x * exp(x))
    yield ('cos-like', sin(x) * exp(x))
    for _ in range(N_FUZZ):
        kind = rng.randint(0, 6)
        if kind == 0:
            yield ('fuzz-int', S(rng.randint(-50, 50)))
        elif kind == 1:
            yield ('fuzz-rat', Rational(rng.randint(-20, 20), rng.randint(1, 9)))
        elif kind == 2:
            yield ('fuzz-symbol', x)
        elif kind == 3:
            yield ('fuzz-pow', x ** rng.randint(0, 4))
        elif kind == 4:
            yield ('fuzz-lin', S(rng.randint(-9, 9)) * x + S(rng.randint(-9, 9)))
        elif kind == 5:
            # non-convertible: a transcendental of the generator
            yield ('fuzz-sin', sin(x) * S(rng.randint(-5, 5) or 1))
        else:
            yield ('fuzz-exp', exp(x) + S(rng.randint(-5, 5)))


def main():
    from sympy import Poly, S, Integer, Rational, symbols, sin, exp, sqrt, pi, I
    from sympy.polys.polyerrors import PolynomialError

    x = symbols('x')

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    n_carried = 0
    n_formal = 0
    for label, e in left_operands(rng, S, Integer, Rational, symbols,
                                  sin, exp, sqrt, pi, I):
        count += 1
        p = Poly(x, x)
        result = e * p
        shadow = shadow_verdict(e, p, PolynomialError)
        oracle = oracle_verdict(result, e, p)
        if oracle == 'carriedOut':
            n_carried += 1
        else:
            n_formal += 1
        if shadow != oracle:
            disagreements.append((label, repr(e), repr(result), shadow, oracle))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for label, ee, rr, sh, orc in disagreements:
            print("  input=%s(%s) result=%s shadow=%r oracle=%r"
                  % (label, ee, rr, sh, orc))
        return 1
    print("G-CONF OK: R/I shadow of formExpressionTimesPolynomial agrees with "
          "patch.diff (gold-patched expr*Poly dispatch) carried-out/formal "
          "verdict over %d inputs (seed=%d), 0 disagreements. "
          "Both branches exercised: %d carried-out (factors combine), "
          "%d formal (factors do not combine, e.g. sin(x)/exp(x))."
          % (count, SEED, n_carried, n_formal))
    return 0


if __name__ == "__main__":
    sys.exit(main())
