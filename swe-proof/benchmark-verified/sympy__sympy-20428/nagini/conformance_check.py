#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-20428 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/MustTerminate) stripped. The model is plain Python over
a two-field record class, so no PSeq shim is needed. There are no @ContractOnly
callees and no @Pure helpers in this bundle (the pure region is empty).

ORACLES: the REAL repo functions the model models per mapping.md —
  * `coeff_truthy(c)`      <-> `ExpressionDomain.Expression.__bool__` — i.e.
                               `bool(coeff)` on a real EX ground-domain
                               coefficient;
  * `strip_constant_len(c)` <-> `sympy.polys.densebasic.dup_strip([coeff])`
                               on a length-1 constant coefficient list; the
                               model carries only the resulting list LENGTH
                               (0 = the canonical zero polynomial, 1 = a
                               retained constant).
The gate applies the diff to /testbed before this script runs and sets
PYTHONPATH=/testbed; this script never applies any diff itself.

Type bridge (mapping.md section 2): for one real coefficient `coeff` wrapping
the SymPy expression `coeff.ex`, the model's two input facets are
  mzero = 1  iff  coeff.ex.is_zero is True   (denotes zero mathematically)
  lit0  = 1  iff  the canonical form IS the bare integer-zero literal
               (coeff.ex == 0, is_zero True, is_Integer)
The Requires hold by construction: both facets are 0/1, and a bare-zero-literal
shape necessarily denotes zero (lit0 == 1 implies mzero == 1), which is a
SymPy fact of the literal itself. The realizable abstract states are exactly
(1,1) bare literal, (0,1) structurally non-trivial but denoting zero, and
(0,0) not (known) zero; the excluded state (1,0) never arises from a real
expression, matching the constructor precondition.

>= 1e5 Requires-satisfying inputs: a structured boundary battery (bare zero
forms, ordinary non-zero atoms, structurally non-trivial denoting-zero
expressions including the exact large radical coefficient from the issue
report, and undecidable-zero symbolic expressions) plus 100000 fuzz
coefficients drawn from cheap constructors that populate all three realizable
states. Pinned fuzz seed: 20428.

Exit 0 iff zero disagreements; on disagreement prints the input expression and
both outcomes and exits 1. stdlib only (random; hypothesis not needed).
"""
import json
import random
import sys

SEED = 20428
N_FUZZ = 100_000


# --- the impl region of model.py, verbatim, contract calls stripped -----------

class Coeff:
    def __init__(self, lit0, mzero):
        self.lit0 = lit0
        self.mzero = mzero


def coeff_truthy(c):
    return c.mzero == 0


def strip_constant_len(c):
    if coeff_truthy(c):
        return 1
    else:
        return 0


# --- bridge: real EX coefficient -> model input facets -------------------------

def facets(coeff):
    """Read the two modeled facets off a real coefficient's stored expression,
    exactly as mapping.md section 2 defines the bijection."""
    ex = coeff.ex
    mzero = 1 if (ex.is_zero is True) else 0
    lit0 = 1 if (ex == 0 and ex.is_zero is True and ex.is_Integer) else 0
    return lit0, mzero


def check_one(dup_strip, coeff, ex_label):
    """Diff the shadow against BOTH real oracles for one coefficient.
    Returns an error string on any disagreement, else None."""
    lit0, mzero = facets(coeff)
    # Requires hold by construction for facets read off a real coefficient:
    assert lit0 in (0, 1) and mzero in (0, 1)
    assert not (lit0 == 1 and mzero == 0)
    c = Coeff(lit0, mzero)

    # oracle 1: the coefficient's truthiness
    real_truthy = bool(coeff)
    shadow_truthy = coeff_truthy(c)
    if real_truthy is not shadow_truthy:
        return ("DISAGREEMENT (truthiness)\n  ex=%s\n  facets lit0=%d mzero=%d\n"
                "  shadow=%r  real=%r"
                % (ex_label, lit0, mzero, shadow_truthy, real_truthy))

    # oracle 2: the stored length after stripping a constant coefficient list
    real_len = len(dup_strip([coeff]))
    shadow_len = strip_constant_len(c)
    if real_len != shadow_len:
        return ("DISAGREEMENT (strip length)\n  ex=%s\n  facets lit0=%d "
                "mzero=%d\n  shadow=%r  real=%r"
                % (ex_label, lit0, mzero, shadow_len, real_len))
    return None


def boundary_exprs():
    """Structured battery covering the three realizable facet states."""
    from sympy import (S, sqrt, sympify, symbols, Integer, Rational, Float,
                       cos, sin, pi, exp, log, I, E, Add, Mul)
    x, y = symbols("x y")
    p = symbols("p", positive=True)

    exprs = []
    # bare-literal zero forms (lit0 == 1, mzero == 1)
    exprs += [Integer(0), S.Zero, sympify("0")]
    # ordinary non-zero atoms and combinations (mzero == 0)
    exprs += [Integer(1), Integer(-3), Rational(2, 7), Float(2.5), sqrt(2),
              x, x + 1, y - 3, cos(x), exp(1), pi, E, I, p,
              sympify("a + b"), sympify("2*sqrt(3) - 1"), 3 * pi - 1]
    # structurally non-trivial expressions that denote zero (lit0==0, mzero==1)
    exprs += [
        Float(0.0),                          # zero value, non-Integer node
        Add(Integer(3), Integer(-3), evaluate=False),
        Mul(Integer(0), x, evaluate=False),
        Add(sqrt(2), -sqrt(2), evaluate=False),
        sympify("1/2 + 1/2 - 1", evaluate=False),
        (sqrt(2) + 1) * (sqrt(2) - 1) - 1,
        log(exp(3)) - 3,
    ]
    # zero-undecidable symbolic expressions (is_zero is None -> mzero == 0)
    exprs += [x - y, x * y, cos(x) ** 2 + sin(x) ** 2 - 1, x + pi]
    # the exact large radical coefficient reported in the issue
    big = sympify(
        "-117968192370600*18**(S(1)/3)/(217603955769048*(24201 + "
        "253*sqrt(9165))**(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + "
        "253*sqrt(9165))**(S(1)/3)) - 15720318185*2**(S(2)/3)*3**(S(1)/3)*"
        "(24201 + 253*sqrt(9165))**(S(2)/3)/(217603955769048*(24201 + "
        "253*sqrt(9165))**(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + "
        "253*sqrt(9165))**(S(1)/3)) + 15720318185*12**(S(1)/3)*(24201 + "
        "253*sqrt(9165))**(S(2)/3)/(217603955769048*(24201 + 253*sqrt(9165))**"
        "(S(1)/3) + 2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**"
        "(S(1)/3)) + 117968192370600*2**(S(1)/3)*3**(S(2)/3)/"
        "(217603955769048*(24201 + 253*sqrt(9165))**(S(1)/3) + "
        "2273005839412*sqrt(9165)*(24201 + 253*sqrt(9165))**(S(1)/3))",
        {"S": S})
    exprs.append(big)
    return exprs


def fuzz_exprs(rng, n):
    """Generator of n cheap random expressions populating all three realizable
    facet states (bare zero, non-trivial zero shapes, non-zero, undecidable)."""
    from sympy import Integer, Rational, Float, sqrt, symbols, Add, Mul, pi
    x = symbols("x")
    for _ in range(n):
        k = rng.randrange(10)
        if k == 0:
            # integers, with 0 over-represented (the bare-literal state)
            yield Integer(rng.choice([0, 0, 0, rng.randint(-10 ** 6, 10 ** 6)]))
        elif k == 1:
            a = rng.choice([0, 0, rng.randint(-999, 999)])
            yield Rational(a, rng.randint(1, 999))
        elif k == 2:
            yield Float(rng.choice([0.0, 0.0, rng.uniform(-1e3, 1e3)]))
        elif k == 3:
            # unevaluated sum that often cancels: a non-trivial zero shape
            a = rng.randint(-50, 50)
            b = rng.choice([-a, -a, rng.randint(-50, 50)])
            yield Add(Integer(a), Integer(b), evaluate=False)
        elif k == 4:
            # unevaluated product with an occasional zero factor
            a = rng.choice([0, 0, rng.randint(-20, 20)])
            yield Mul(Integer(a), x, evaluate=False)
        elif k == 5:
            yield sqrt(rng.randint(0, 500))
        elif k == 6:
            a, b = rng.randint(-20, 20), rng.randint(-20, 20)
            yield a + b * sqrt(2)
        elif k == 7:
            yield rng.randint(-20, 20) * x + rng.randint(-20, 20)
        elif k == 8:
            yield rng.randint(-9, 9) * pi + rng.randint(-9, 9)
        else:
            # unevaluated radical sum that often cancels
            r = sqrt(rng.randint(2, 9))
            c = rng.randint(-5, 5)
            d = rng.choice([-c, -c, rng.randint(-5, 5)])
            yield Add(Mul(Integer(c), r, evaluate=False),
                      Mul(Integer(d), r, evaluate=False), evaluate=False)


def main():
    # REAL repo symbols (the ones the model models, per mapping.md):
    from sympy.polys.domains import EX
    from sympy.polys.densebasic import dup_strip

    checked = 0
    state_seen = {(1, 1): 0, (0, 1): 0, (0, 0): 0}

    n_boundary = 0
    for ex in boundary_exprs():
        coeff = EX.Expression(ex)
        err = check_one(dup_strip, coeff, repr(ex))
        if err:
            print(err)
            return 1
        state_seen[facets(coeff)] += 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for ex in fuzz_exprs(rng, N_FUZZ):
        coeff = EX.Expression(ex)
        err = check_one(dup_strip, coeff, repr(ex))
        if err:
            print(err)
            return 1
        state_seen[facets(coeff)] += 1
        checked += 1

    # sanity: every realizable abstract state was actually exercised
    for st, n in state_seen.items():
        assert n > 0, "facet state %r never exercised" % (st,)

    print("G-CONF OK: shadow impl (coeff_truthy, strip_constant_len) == real "
          "coefficient truthiness + constant-list strip on %d coefficients "
          "(%d boundary + %d fuzz, seed %d); facet-state coverage "
          "(lit0,mzero): %s"
          % (checked, n_boundary, N_FUZZ, SEED,
             {str(k): v for k, v in sorted(state_seen.items())}))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
