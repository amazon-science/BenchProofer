#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13878 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides and comparing observable outputs:

  * SHADOW  — the R/I-tagged ops of Solution.lean's impl region transliterated
              to the real repo type. The impl builds the closed-form cumulative
              distribution object node-by-node from the operands; each Lean
              `Expr` constructor maps 1:1 to its library term-builder via the
              mapping.md bijection (`Expr.lt x a` ↔ `x < a`, `Expr.div p q` ↔
              `p/q`, `Expr.asin e` ↔ `asin(e)`, `Expr.piecewise3 …` ↔
              `Piecewise((v1,c1),(v2,c2),(v3,c3))`, …). There is NO A-tagged
              callee in the computed output, so the impl region is pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: the real library value
              `cdf(Arcsin(name, a, b))(x)` at base_commit with the gold patch
              applied (the real correctness oracle, G-RESOLVE), which is exactly
              what `test_arcsin` (the sole FAIL_TO_PASS) asserts on.

The observable is the SYMBOLIC OBJECT: SHADOW and ORACLE must be the SAME
expression tree under the library's structural equality (`Basic.__eq__`) — the
very relation the F2P assert uses. The library canonicalises identically on
both sides (relational flip, additive-argument ordering) because both go
through the same unchanged term-builders; G-CONF confirms the constructor
bijection reproduces the canonical object, it does NOT re-implement the
canonicaliser.

Inputs are the distribution's two endpoint operands and the evaluation point —
free symbols. We fuzz over symbol NAMES and assumption sets (the only input
degrees of freedom; there are no numeric input values to vary) to confirm the
constructor bijection is robust, not an artefact of one symbol choice.

Exit 0 iff zero disagreements; any disagreement is a mechanical R/I-fidelity
counterexample. stdlib + sympy only (sympy ships in the testbed env).
"""
import random
import sys

SEED = 13878
N_FUZZ = 100_000


def build_shadow(asin, sqrt, pi, S, Piecewise, a, b, x):
    """SHADOW: arcsinExprCdf transliterated from Solution.lean's Expr
    constructors to library term-builders (the mapping.md R bijection).

      Expr.piecewise3 v1 c1 v2 c2 v3 c3  ->  Piecewise((v1,c1),(v2,c2),(v3,c3))
      Expr.zero -> S.Zero      Expr.one -> S.One      Expr.natLit 2 -> S(2)
      Expr.pi -> pi            Expr.lt x a -> x < a   Expr.le x b -> x <= b
      Expr.top -> True
      Expr.div p q -> p/q      Expr.mul p q -> p*q    Expr.sub p q -> p - q
      Expr.asin e -> asin(e)   Expr.sqrt e -> sqrt(e)

    This mirrors the impl-region `do` block EXACTLY: it constructs the three
    clauses from the operands and assembles a three-branch Piecewise. No
    numeric evaluation, no simplification call — only constructor application.
    """
    on_support = S(2) * asin(sqrt((x - a) / (b - a))) / pi
    return Piecewise(
        (S.Zero, x < a),
        (on_support, x <= b),
        (S.One, True),
    )


def build_oracle(Arcsin, cdf, name, a, b, x):
    """ORACLE: patch.diff behaviour — the real library cumulative distribution
    of the bounded-support two-parameter distribution, evaluated at x. This is
    the object test_arcsin asserts on."""
    X = Arcsin(name, a, b)
    return cdf(X)(x)


def fuzz_cases(n, rng):
    """Yield (a_name, b_name, x_name, assumption_kind) tuples. The first cases
    reproduce test_arcsin exactly (a,b real; x plain), then we fuzz names and
    assumption sets."""
    # exact F2P configuration first
    yield ("a", "b", "x", "f2p")
    yield ("a", "b", "z", "f2p")
    # assumption variants on the endpoints / point
    assum = ["plain", "real", "positive", "f2p"]
    names = ["a", "b", "c", "p", "q", "u", "v", "w", "alpha", "lo", "hi", "t"]
    for _ in range(n):
        an = rng.choice(names)
        bn = rng.choice([m for m in names if m != an])
        xn = rng.choice([m for m in names if m not in (an, bn)])
        yield (an, bn, xn, rng.choice(assum))


def make_symbols(Symbol, an, bn, xn, kind):
    if kind == "real":
        kw = {"real": True}
    elif kind == "positive":
        kw = {"positive": True}
    else:  # plain or f2p — test_arcsin uses real endpoints, plain point
        kw = {}
    if kind == "f2p":
        a = Symbol(an, real=True)
        b = Symbol(bn, real=True)
        x = Symbol(xn)
    else:
        a = Symbol(an, **kw)
        b = Symbol(bn, **kw)
        x = Symbol(xn, **kw)
    return a, b, x


def main():
    from sympy import asin, sqrt, pi, S, Piecewise, Symbol
    from sympy.stats import Arcsin, cdf

    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for an, bn, xn, kind in fuzz_cases(N_FUZZ, rng):
        count += 1
        a, b, x = make_symbols(Symbol, an, bn, xn, kind)
        shadow = build_shadow(asin, sqrt, pi, S, Piecewise, a, b, x)
        oracle = build_oracle(Arcsin, cdf, "rv", a, b, x)
        # structural equality — the exact relation test_arcsin's assert uses
        if shadow != oracle:
            disagreements.append((an, bn, xn, kind, shadow, oracle))
            if len(disagreements) >= 5:
                break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs:"
              % (len(disagreements), count))
        for an, bn, xn, kind, sh, orc in disagreements:
            print("  a=%s b=%s x=%s kind=%s shadow=%r oracle=%r"
                  % (an, bn, xn, kind, sh, orc))
        return 1
    print("G-CONF OK: R/I constructor-bijection shadow of arcsinCdfBuild equals "
          "patch.diff behaviour (structural Basic.__eq__) on %d symbol/assumption "
          "configurations (seed=%d), 0 disagreements." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
