#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-13974 (plan §4.1).

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs. TWO
modeled methods, hence TWO lanes.

LANE 1 — THE PIN (`distributePow`), the whole-expression power:

  * SHADOW  — the R/I-tagged ops of Solution.lean's `distributePow` impl region
              transliterated to Python over the *real* repo types, via the
              mapping.md bijection (`List Factor` ↔ the aggregate's arg tuple,
              position-wise `powF · n` ↔ `b**n`). The backward `while` fold
              computes exactly the left-to-right position-wise raise, so the
              shadow is `TensorProduct(*[ b**n for b in args ])`. There is NO
              A-tagged callee in the computed output — the per-factor `**`
              (powF) is the I-leg's own primitive, run for real on BOTH sides —
              so the shadow is pure R/I (conf_skip=false).
  * ORACLE  — `patch.diff`'s public behavior: the patched `tensor_product_simp`
              applied to the corresponding power node `TP(*args)**n` (the harness
              applies patch.diff at base_commit before this runs). Post-patch the
              `Pow` branch routes a TensorProduct-based power into
              `tensor_product_simp_Pow`, the real correctness oracle (G-RESOLVE).

LANE 2 — THE ROUTE (`simplifyFactor`), a power of an aggregate occupying ONE
FACTOR POSITION of a product. This lane exists because an earlier revision of
this file fuzzed LANE 1 only, and was therefore blind BY CONSTRUCTION to the
product contexts — the exact contexts three of the four F2P assertions live in,
and the contexts the reference patch's `tensor_product_simp_Mul` edits serve. A
conformance check that never builds a `Mul` cannot refute the fidelity of a
routing decision that only a `Mul` reaches.

  * SHADOW  — `simplifyFactor`'s impl region transliterated: the routing flag
              selects either the position-wise raise (`b**n` per position, the
              same I-leg primitive as LANE 1) or the untouched positions. So the
              shadow of a factor position is `factorImage`, and the observable
              shadow of the whole product is that image scaled by the product's
              commutative part — which is the transliteration of the spec's own
              `out`, with no A-tagged callee in it.
  * ORACLE  — the patched `tensor_product_simp` applied to `c * TP(*args)**n`
              (raise arm) and to `c * TP(*args)` (passthrough arm), where `c` is
              a commutative scalar. Both shapes are `Mul`s, so they enter
              `tensor_product_simp_Mul`; both have a single non-commutative
              factor, so they reach the single-factor routing site the patch
              adds, where a `Pow`-of-aggregate factor is routed to the
              per-position raise and any other factor is handed back untouched.

  SCOPE, stated rather than implied. LANE 2 fuzzes the factor positions whose
  IMAGE IS OBSERVABLE IN ISOLATION — a product with one non-commutative factor.
  Products with SEVERAL non-commutative factors reach the same routing decision
  (mapping.md §2 names that site too), but their observable output is the modeled
  factor image after it has been COMBINED position-wise with the other factors'
  positions by machinery this bundle does not model and the reference patch does
  not change. A disagreement there could not be attributed to the modeled
  routing, which is precisely what the A-leg rule excludes, so those shapes are
  deliberately out of this lane rather than silently absent from it.

Both lanes must agree on every input. Exit 0 iff zero disagreements in EITHER
lane; any disagreement is a mechanical R/I-fidelity counterexample.

Runs in-container (the prebuilt SWE-Bench instance image), `sympy` only. The fuzz
seed is pinned (mapping.md §4) for a deterministic verdict.
"""
import random
import sys

from sympy import symbols, Symbol, Integer, Mul, Rational, Pow
from sympy.physics.quantum import TensorProduct as TP
from sympy.physics.quantum import tensor_product_simp

SEED = 13974
N_FUZZ = 100_000
# LANE 2 runs the same number of product-context inputs as LANE 1 runs
# whole-expression ones, so neither lane is a token gesture.
N_FUZZ_ROUTE = 100_000


def shadow_pow(args, n):
    """distributePow transliterated: position-wise raise, aggregate rebuilt.
    This is the R/I shadow of the impl (powAll n factors)."""
    return TP(*[b ** n for b in args])


def oracle_pow(args, n):
    """patch.diff's public behavior: tensor_product_simp on the power node."""
    return tensor_product_simp(TP(*args) ** n)


def is_modeled_node(args, n):
    """True iff TP(*args)**n is a genuine Pow whose base is a TensorProduct —
    the exact domain distributePow models. Inputs sympy auto-collapses upstream
    (n in {0,1}; commutative-scalar aggregates) never reach the patched branch,
    so they are out of scope for the R/I leg."""
    expr = TP(*args) ** n
    return isinstance(expr, Pow) and isinstance(expr.base, TP)


def gen_inputs(n_fuzz, rng):
    A, B, C, D, E = symbols('A B C D E', commutative=False)
    a = Symbol('a', commutative=False)
    x, y = symbols('x y')           # commutative — used ONLY as exponents
    factors = [A, B, C, D, E, a]
    pool = factors + [Integer(1)]
    # exponents that keep TP**n a genuine Pow node (exclude 0 and 1)
    exps = [x, y, Integer(2), Integer(3), Integer(-1), Integer(-2),
            Rational(1, 2), x + y, x + 1]

    # boundary cases first (plan §4.1 step 4)
    boundary = [
        ((A,), x), ((A, B), x), ((A, B, C), x),
        ((A, B), Integer(2)), ((A, B, C, D), Integer(3)),
        ((A, A), Integer(2)), ((A, B, A), x),
        ((Integer(1), Integer(1)), Integer(2)),
        ((Integer(1), a), x),
    ]
    for args, n in boundary:
        yield args, n

    for _ in range(n_fuzz):
        k = rng.randint(1, 5)
        args = tuple(rng.choice(pool) for _ in range(k))
        n = rng.choice(exps)
        yield args, n


# ---------------------------------------------------------------------------
# LANE 2 — THE ROUTE: one factor position of a product.
# ---------------------------------------------------------------------------

def shadow_factor(is_pow_of_aggregate, args, n, c):
    """simplifyFactor transliterated, then scaled by the product's scalar part.

    `factorImage`: the raise arm applies the same per-position `**` primitive as
    LANE 1; the passthrough arm hands the positions back untouched. The `c *` is
    the commutative part travelling alongside the factor, which the routing
    decision does not touch — so this is the transliteration of the spec's `out`
    and nothing else.
    """
    image = [b ** n for b in args] if is_pow_of_aggregate else list(args)
    return c * TP(*image)


def oracle_factor(is_pow_of_aggregate, args, n, c):
    """patch.diff's public behaviour on the corresponding product node."""
    factor = TP(*args) ** n if is_pow_of_aggregate else TP(*args)
    return tensor_product_simp(c * factor)


def is_modeled_factor(is_pow_of_aggregate, args, n, c):
    """True iff the product really is a Mul with ONE non-commutative factor and
    that factor really is the modeled shape.

    The raise arm needs the factor to be a genuine `Pow` over a TensorProduct
    base (sympy collapses n in {0, 1} and commutative-scalar aggregates
    upstream, so those never reach the routing site); the passthrough arm needs
    it to be a bare TensorProduct. Anything sympy restructures on construction is
    outside the modeled domain rather than a disagreement.
    """
    factor = TP(*args) ** n if is_pow_of_aggregate else TP(*args)
    if is_pow_of_aggregate:
        if not (isinstance(factor, Pow) and isinstance(factor.base, TP)):
            return False
    elif not isinstance(factor, TP):
        return False
    expr = c * factor
    if not isinstance(expr, Mul):
        return False
    _c_part, nc_part = expr.args_cnc()
    return len(nc_part) == 1 and nc_part[0] == factor


def gen_route_inputs(n_fuzz, rng):
    A, B, C, D, E = symbols('A B C D E', commutative=False)
    a = Symbol('a', commutative=False)
    x, y = symbols('x y')           # commutative — exponents and scalars
    pool = [A, B, C, D, E, a, Integer(1)]
    exps = [x, y, Integer(2), Integer(3), Integer(-1), Integer(-2),
            Rational(1, 2), x + y, x + 1]
    # scalars: the commutative part travelling with the factor. Integer(1) is
    # included so the degenerate scalar is probed too, and a symbolic one so the
    # lane does not depend on numeric folding.
    scalars = [Integer(2), Integer(-1), Rational(1, 3), x, y, x * y, Integer(1)]

    # boundary cases first, BOTH arms, so the flag is exercised at the same
    # aggregates rather than only at whichever ones the fuzz happens to pair
    # with it.
    boundary = [
        (True, (A,), x, Integer(2)), (True, (A, B), x, Integer(2)),
        (True, (A, B, C), x, x), (True, (A, B), Integer(2), Integer(-1)),
        (True, (A, A), Integer(2), Rational(1, 3)),
        (True, (A, B, C, D), Integer(3), Integer(2)),
        (False, (A,), None, Integer(2)), (False, (A, B), None, x),
        (False, (A, B, C), None, Integer(-1)),
        (False, (A, A), None, Rational(1, 3)),
    ]
    for item in boundary:
        yield item

    for _ in range(n_fuzz):
        flag = rng.random() < 0.5
        k = rng.randint(1, 5)
        args = tuple(rng.choice(pool) for _ in range(k))
        n = rng.choice(exps) if flag else None
        yield flag, args, n, rng.choice(scalars)


def main():
    rng = random.Random(SEED)
    disagreements = []
    count = 0
    for args, n in gen_inputs(N_FUZZ, rng):
        if not is_modeled_node(args, n):
            continue              # out of the modeled domain (sympy collapses it)
        count += 1
        shadow = shadow_pow(args, n)
        oracle = oracle_pow(args, n)
        if shadow != oracle:
            disagreements.append(("PIN", args, n, shadow, oracle))
            if len(disagreements) >= 5:
                break
    route_count = 0
    route_raise = 0
    route_pass = 0
    if not disagreements:
        rng_route = random.Random(SEED)
        for flag, args, n, c in gen_route_inputs(N_FUZZ_ROUTE, rng_route):
            if not is_modeled_factor(flag, args, n, c):
                continue          # sympy restructured it; outside the domain
            route_count += 1
            if flag:
                route_raise += 1
            else:
                route_pass += 1
            shadow = shadow_factor(flag, args, n, c)
            oracle = oracle_factor(flag, args, n, c)
            if shadow != oracle:
                disagreements.append(("ROUTE", (flag, args, c), n,
                                      shadow, oracle))
                if len(disagreements) >= 5:
                    break
    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d PIN + %d ROUTE "
              "inputs:" % (len(disagreements), count, route_count))
        for lane, args, n, sh, orc in disagreements:
            print("  lane=%s args=%r exp=%r shadow=%r oracle=%r"
                  % (lane, args, n, sh, orc))
        return 1
    # Both arms of THE ROUTE must actually have been reached, or the lane
    # attests to nothing: a domain filter that silently excluded one arm would
    # otherwise read as agreement on it.
    if not route_raise or not route_pass:
        print("G-CONF FAIL: ROUTE lane reached raise=%d passthrough=%d — an arm "
              "was never exercised, so its fidelity is untested"
              % (route_raise, route_pass))
        return 1
    print("G-CONF OK: R/I shadows agree with patch.diff behaviour — "
          "distributePow on %d whole-expression inputs, simplifyFactor on %d "
          "factor-position inputs (%d raise arm, %d passthrough arm) "
          "(seed=%d), 0 disagreements."
          % (count, route_count, route_raise, route_pass, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
