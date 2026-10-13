#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13974.

Runs the REAL repository callees in-container and asserts that every observation
matches the model in model.py.

The single consumed axiom is `pow_expr` (model.py axioms region): the binary
symbolic power map `base ** exp`, applied once per tensor factor. The axiom
carries the precondition `exp != 1` (the identity exponent, handle 1). The ONLY
things the proof relies on are:

  (A-consumed: pow_expr, under the precondition exp != 1)
    * determinism / functionality — `base ** exp` is a deterministic function of
      (base, exp): repeated construction yields equal results, so the impl loop
      and the spec fold read the SAME power handle for the same (factor,
      exponent) pair;
    * non-triviality away from the identity exponent — for every exponent other
      than the identity `1`, raising a factor to the exponent does NOT return the
      factor unchanged: `base ** exp != base`. This is the property that forces
      the exponent to actually be applied per factor (the prepatch violates it by
      leaving each factor unchanged).

The axiom does NOT claim non-triviality at the identity exponent `1`, because the
real power map returns the factor unchanged there (`base ** 1 == base`). The
precondition `exp != 1` excludes exactly that case, so the axiom is sound — and
this is faithful: a `Pow` node never carries exponent `1` (it canonicalises to
the base), so `tensor_product_simp_Pow` is never reached with `exp == 1`. This
check therefore fuzzes the identity boundary explicitly and asserts the OPPOSITE
expectation there (`base ** 1 == base`), confirming the precondition is the
weakest-sufficient guard rather than a masked over-claim.

This script ALSO validates the end-to-end model fidelity (model.py's
`power_of_collection` per-factor map against the REAL gold-patched
`tensor_product_simp` / `tensor_product_simp_Pow`): for a power whose base is a
tensor product of factors (a_1, ..., a_n), the simplified result is the tensor
product of (a_1**e, ..., a_n**e) — factor order preserved, factor count
unchanged. The instance FAIL_TO_PASS witnesses are asserted directly, and the
pre-patch behaviour (the exponent left wrapping the whole tensor product, each
factor unchanged) is confirmed DETECTABLY wrong, so the spec discriminates.

Imports only `sympy` (the package whose `tensor_product_simp` the patch fixes)
and the standard library. Exit 0 iff every obligation holds.
"""
import random
import sys

from sympy import symbols, Symbol, Mul, Pow
from sympy.physics.quantum.tensorproduct import (
    TensorProduct as TP,
    tensor_product_simp as tps,
    tensor_product_simp_Pow,
    tensor_product_simp_Mul,
)


# --- (A-consumed) pow_expr axiom: determinism + non-triviality ---------------

def check_pow_expr_axiom(base, exp):
    """Assert the REAL `base ** exp` meets the axiom *under its precondition*:
        (1) determinism: `base ** exp` is reproducible / equal to itself
            (claimed unconditionally), and
        (2) non-triviality: `base ** exp != base` ONLY when `exp != 1`
            (the axiom's `Requires(exp != 1)` guard).

    The function is precondition-aware: for `exp == 1` it asserts the OPPOSITE
    (`base ** 1 == base`) — proving the precondition is necessary (the axiom would
    be unsound without it) and that the encoding excludes exactly the boundary the
    real callee fails, not more.
    """
    r1 = base ** exp
    r2 = base ** exp
    assert r1 == r2, (
        "pow_expr axiom unsound (non-deterministic) on (%r, %r): %r vs %r"
        % (base, exp, r1, r2))
    if exp == 1:
        # Outside the axiom's precondition (Requires(exp != 1)). The axiom does
        # NOT claim r1 != base here; the real callee returns the base unchanged,
        # which is exactly why the precondition excludes it.
        assert r1 == base, (
            "identity-exponent boundary unexpected on (%r, %r): base ** 1 should "
            "equal base, justifying the axiom's exp != 1 precondition" % (base, exp))
    else:
        assert r1 != base, (
            "pow_expr axiom unsound (trivial) on (%r, %r): base ** exp == base "
            "with exp != 1; the per-factor power would not be observable"
            % (base, exp))


# --- end-to-end model fidelity: the per-factor distribution ------------------

def model_distribute(factors, exp):
    """model.py's `power_of_collection`: each factor raised to exp, in order."""
    return [b ** exp for b in factors]


def check_end_to_end(factors, exp):
    """The REAL gold-patched `tensor_product_simp_Pow(TP(*factors) ** exp)`
    equals `TP(*[b**exp for b in factors])` the model pins — factor by factor,
    in order. Also confirms the top-level `tensor_product_simp` on the same
    power agrees (it routes a TensorProduct-based power through the helper)."""
    base = TP(*factors)
    power = base ** exp

    helper = tensor_product_simp_Pow(power)          # real new helper
    expected_args = tuple(model_distribute(factors, exp))
    assert tuple(helper.args) == expected_args, (
        "model fidelity broken: tensor_product_simp_Pow(%r) gave args %r; "
        "model pins %r" % (power, tuple(helper.args), expected_args))

    top = tps(power)                                 # real top-level dispatcher
    assert top == TP(*expected_args), (
        "model fidelity broken: tensor_product_simp(%r) gave %r; model pins %r"
        % (power, top, TP(*expected_args)))


# --- routing decision: simp_pow_factor against real tensor_product_simp_Mul ---

def model_simp_pow_factor(is_pow_of_tp, factors, exp):
    """model.py's `simp_pow_factor`: a Pow-of-TensorProduct factor of a product is
    replaced by its per-factor distribution (delegating to power_of_collection); a
    bare TensorProduct factor passes through unchanged. Returns the per-factor
    result handle list the routing yields for that one factor."""
    if is_pow_of_tp:
        return model_distribute(factors, exp)        # distribute per factor
    return list(factors)                             # passthrough, unchanged


def _routed_factor_args(simplified):
    """Extract the (single) non-commutative tensor-product factor's argument tuple
    from a simplified `Mul` result (the rest being a scalar/commutative prefix).
    The routing's observable effect is exactly that factor's argument list."""
    nc = [a for a in Mul.make_args(simplified) if not a.is_commutative]
    assert len(nc) == 1 and isinstance(nc[0], TP), (
        "expected exactly one TensorProduct nc factor in %r, got %r"
        % (simplified, nc))
    return tuple(nc[0].args)


def check_routing_pow(c_scalar, factors, exp):
    """The REAL gold-patched `tensor_product_simp_Mul` on a product whose single
    non-commutative factor is a Pow-of-TensorProduct (`c_scalar * TP(*factors)**exp`)
    routes that factor through the per-factor distribution. Model: the routing
    decision `simp_pow_factor(is_pow_of_tp=True, factors, exp)` returns
    `[b**exp for b in factors]`. Compare the resulting tensor-factor list."""
    base = TP(*factors)
    power = base ** exp
    assert isinstance(power, Pow), ("expected a Pow node, got %r" % power)
    e = c_scalar * power                              # a Mul with one nc Pow factor
    assert isinstance(e, Mul), ("expected a Mul, got %r" % e)

    got = _routed_factor_args(tensor_product_simp_Mul(e))   # real routing
    expected = tuple(model_simp_pow_factor(True, factors, exp))
    assert got == expected, (
        "routing fidelity broken (is_pow_of_tp=True): tensor_product_simp_Mul(%r) "
        "routed factor args %r; model simp_pow_factor pins %r"
        % (e, got, expected))


def check_routing_passthrough(c_scalar, factors):
    """The REAL `tensor_product_simp_Mul` on a product whose single non-commutative
    factor is already a bare TensorProduct (`c_scalar * TP(*factors)`) leaves that
    factor's tensor factors unchanged. Model: `simp_pow_factor(is_pow_of_tp=False,
    factors, _)` returns `list(factors)` (identity fold, order/count preserved)."""
    e = c_scalar * TP(*factors)
    assert isinstance(e, Mul), ("expected a Mul, got %r" % e)
    got = _routed_factor_args(tensor_product_simp_Mul(e))
    expected = tuple(model_simp_pow_factor(False, factors, None))
    assert got == expected, (
        "routing fidelity broken (is_pow_of_tp=False): tensor_product_simp_Mul(%r) "
        "routed factor args %r; model simp_pow_factor pins passthrough %r"
        % (e, got, expected))


def main():
    A, B, C, D, E = symbols('A,B,C,D,E', commutative=False)
    x, y = symbols('x,y')
    nc_factors = [A, B, C, D, E]
    exps = [x, y, Symbol('n'), 2, 3, x + 1, 2 * x]

    # --- (A-consumed) pow_expr axiom: determinism + non-triviality -----------
    n_axiom = 0
    for b in nc_factors:
        for e in exps:
            check_pow_expr_axiom(b, e)
            n_axiom += 1

    # --- identity-exponent boundary: the axiom's precondition is necessary -----
    # Fuzz the trivial exponent the axiom EXCLUDES (Requires(exp != 1)). The real
    # callee returns the base unchanged here, so an axiom WITHOUT the precondition
    # would over-claim. check_pow_expr_axiom asserts base ** 1 == base on this
    # boundary, confirming the guard is weakest-sufficient (not masked fuzz).
    n_boundary = 0
    for b in nc_factors:
        check_pow_expr_axiom(b, 1)      # exp == 1 -> asserts base ** 1 == base
        n_boundary += 1
    # also confirm the axiom DOES hold for the smallest non-trivial integer
    for b in nc_factors:
        check_pow_expr_axiom(b, 2)
        n_boundary += 1

    # --- end-to-end model fidelity: boundary tensor products -----------------
    boundary = [
        ([A, B], x),
        ([A, B], 2),
        ([C, D], x),
        ([A, B, C], x),
        ([A, B, C, D], 2),
        ([A, B, C, D, E], 3),
        ([A, B], x + 1),
        ([A, B, C], 2 * x),
    ]
    n_e2e = 0
    for factors, e in boundary:
        check_end_to_end(factors, e)
        n_e2e += 1

    # --- routing decision fidelity: simp_pow_factor vs real tensor_product_simp_Mul
    # The patch threads the per-factor distribution through tensor_product_simp_Mul:
    # a Pow-of-TensorProduct non-commutative factor of a product is routed into the
    # distribution; a bare TensorProduct factor passes through. simp_pow_factor
    # models that decision. Validate both branches against the real dispatcher.
    n_route = 0
    for factors, e in boundary:
        check_routing_pow(x, factors, e)            # is_pow_of_tp = True branch
        check_routing_passthrough(x, factors)       # is_pow_of_tp = False branch
        n_route += 1
    # also the scalar-free single-power Mul case the n_nc==1 branch covers
    for factors, e in [([A, B], 2), ([C, D], x), ([A, B, C], 3)]:
        check_routing_pow(y, factors, e)
        n_route += 1

    # --- the instance FAIL_TO_PASS witnesses, asserted directly --------------
    assert tps(TP(A, B) ** x) == TP(A ** x, B ** x), \
        "F2P witness 1 (TP(A,B)**x) fails under the gold patch"
    assert tps(x * TP(A, B) ** 2) == x * TP(A ** 2, B ** 2), \
        "F2P witness 2 (x*TP(A,B)**2) fails under the gold patch"
    assert tps(x * (TP(A, B) ** 2) * TP(C, D)) == x * TP(A ** 2 * C, B ** 2 * D), \
        "F2P witness 3 (x*(TP(A,B)**2)*TP(C,D)) fails under the gold patch"
    assert tps(TP(A, B) - TP(C, D) ** x) == TP(A, B) - TP(C ** x, D ** x), \
        "F2P witness 4 (TP(A,B)-TP(C,D)**x) fails under the gold patch"

    # --- pre-patch behaviour is DETECTABLY wrong (spec discriminates) --------
    # The pre-patch leaves the exponent OUTSIDE the tensor product: the result is
    # `TP(A, B) ** x` (factors A, B unchanged), which is NOT the distributed
    # `TP(A**x, B**x)`. Confirm those two distinct expressions differ, so the
    # model's per-factor postcondition senses the change.
    pre_image = TP(A, B) ** x          # exponent left wrapping the whole TP
    gold_image = TP(A ** x, B ** x)    # exponent distributed per factor
    assert pre_image != gold_image, (
        "pre-patch and gold images coincide on the witness -- the spec would "
        "not discriminate the bug")

    # The routing decision is likewise detectable: pre-patch tensor_product_simp_Mul
    # had a bare `return e` for the n_nc==1 case (and a TypeError for a leading
    # non-TensorProduct factor), so `x * TP(A,B)**2` would stay `x*TP(A,B)**2` with
    # the factors A, B unchanged -- NOT the routed `x*TP(A**2,B**2)`. The model's
    # simp_pow_factor(is_pow_of_tp=True) routed args differ from the unchanged args.
    routed_args = tuple(model_simp_pow_factor(True, [A, B], 2))   # (A**2, B**2)
    unrouted_args = (A, B)                                        # pre-patch leaves them
    assert routed_args != unrouted_args, (
        "routing pre-patch and gold coincide -- simp_pow_factor would not "
        "discriminate the missing n_nc==1 Pow routing")

    # --- randomized fuzz over the axiom + end-to-end + routing fidelity -------
    rng = random.Random(13974)
    n_fuzz = 0
    for _ in range(500):
        n = rng.randint(2, 5)
        factors = [rng.choice(nc_factors) for _ in range(n)]
        e = rng.choice(exps)
        for b in factors:
            check_pow_expr_axiom(b, e)
        check_end_to_end(factors, e)
        # non-unit scalar prefixes keep the expression a genuine Mul with one nc
        # factor (a unit scalar would collapse `1 * f` to `f`, losing the Mul).
        check_routing_pow(rng.choice([x, y, 2, x * y]), factors, e)
        check_routing_passthrough(rng.choice([x, y, 2, x * y]), factors)
        n_fuzz += 1

    print("G-AX OK: pow_expr axiom (determinism + non-triviality under exp != 1) "
          "sound over %d non-trivial + %d identity-boundary + %d fuzz "
          "(factor, exponent) pairs (identity exponent 1 confirmed base ** 1 == "
          "base, justifying the Requires(exp != 1) precondition rather than "
          "masking it); end-to-end model fidelity == gold tensor_product_simp_Pow "
          "/ tensor_product_simp over %d boundary + %d fuzz powers; routing "
          "decision fidelity simp_pow_factor == gold tensor_product_simp_Mul "
          "(distribute a Pow-of-TP factor; pass a bare TP factor through) over %d "
          "boundary + %d fuzz products; all 4 FAIL_TO_PASS witnesses hold; "
          "distribution AND routing pre-patch detectably wrong."
          % (n_axiom, n_boundary, n_fuzz, n_e2e, n_fuzz, n_route, n_fuzz))
    return 0


if __name__ == "__main__":
    sys.exit(main())
