#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13551.

The changed product-of-a-sum operation is modelled DEEPLY in model.py (the
`@Pure` front-recursive fold `prod_of_totals` plus the verified loop), not
behind a consumed `@ContractOnly` axiom. There is therefore exactly one kind-A
obligation, an A-reference: the deep model must equal the real callee.

  (A-reference)  deep model  prod_of_totals(base, comp)  ==  real callee
      `exp(Sum(log(p), (k, a, n)))`  (the patched `_eval_product` is_Add /
      `q.is_Number` branch), where over the index range k = a .. n the
      multiplicand `p` is the per-index TOTAL `base[k] + comp[k]`.

  The deep model multiplies the per-index totals:
        prod_of_totals(base, comp) = product over k of (base[k] + comp[k]).
  The real fixed callee `exp(Sum(log(p)))` is the genuine product of `p` over
  the range, i.e. the same number. This script runs the REAL sympy callee and
  asserts equality.

The patched is_Add branch fires only for a NON-polynomial Add multiplicand with
SYMBOLIC limits (a polynomial Add takes the roots branch; concrete limits take
the finite-range branch). We therefore use exponential multiplicands of the
shape `c*2**k + d` -- exactly the F2P term `n + 1/2**k`, whose numerator is
`2**k*n + 1` (a leading constant part 1 + a remaining exponential part) -- and
assert (a) the patched `exp(Sum(log(...)))` form actually fired, and (b) the
deep model equals it after substituting a concrete bound.

Domain boundary (matches model.py's precondition): every per-index total
`d + c*2**k` must be NONZERO. When some total vanishes, `log(0) = zoo` makes
the real reduction `exp(Sum(log(p)))` evaluate to the undefined `exp(zoo)`,
not the integer 0 -- so zero-total inputs lie OUTSIDE the modeled domain and
model.py's Requires excludes them
(`Forall i: base[i] + comp[i] != 0`). The fuzz below spans NEGATIVE and
positive constant parts (so sign coverage is real), skips exactly the
zero-total inputs, and separately CONFIRMS the boundary: on a zero-total
input the real callee yields a non-numeric `exp(zoo)` in both the
`Product.doit` and direct `exp(Sum(log))` forms.

It ALSO confirms the discriminator is real (the pre-patch identity is wrong):
the pre-patch operation `sum([_eval_product(part) for part in p.as_coeff_Add()])`
equals `prod_one(base) + prod_one(comp)` (the total of the two part-products),
which differs from `prod_of_totals` on the witness inputs -- exactly what the
F2P test observes (15/2 correct vs 9/2 pre-patch).

Imports only sympy (the repo under test, whose `_eval_product`/`exp`/`Sum`/`log`
ARE the real callee) and the standard library. Exit 0 iff every obligation
holds.
"""
import random
import sys

from sympy import Symbol, Product, Sum, exp, log, S, Integer, sympify


# --- model.py deep-model reference encodings (kept in lock-step) -------------

def prod_of_totals(base, comp):
    """Reference reimplementation of model.py's deep model `prod_of_totals`:
    the product, over every index, of the per-index total base[i] + comp[i]."""
    assert len(base) == len(comp)
    out = 1
    for bi, ci in zip(base, comp):
        out *= (bi + ci)
    return out


def prod_one(xs):
    """Reference reimplementation of model.py's `prod_one`: the product of a
    single part's contributions (used to state the WRONG pre-patch identity)."""
    out = 1
    for x in xs:
        out *= x
    return out


# --- the A-reference check: deep model == real callee ------------------------

def real_doit_symbolic(p_fn):
    """`Product(p, (k, 0, n-1)).doit()` with SYMBOLIC n, so the patched is_Add
    branch fires. Returns the (still symbolic in n) doit expression and n."""
    k = Symbol('k')
    n = Symbol('n')
    p = p_fn(k)
    return Product(p, (k, 0, n - 1)).doit(), n


def has_zero_total(part_const, part_exp_coeff, N):
    """True iff some per-index total part_const + part_exp_coeff*2**i vanishes
    on 0 <= i < N -- the domain boundary model.py's Requires excludes."""
    return any(part_const + part_exp_coeff * (2 ** i) == 0 for i in range(N))


def check_reference(part_const, part_exp_coeff, N, label):
    """Multiplicand p = part_const + part_exp_coeff * 2**k  (a non-polynomial
    Add: a constant part + an exponential part -- the F2P numerator shape).

    base[i] = part_const (the leading constant part);
    comp[i] = part_exp_coeff * 2**i (the remaining part).

    Caller guarantees no per-index total is zero (model.py's Requires); the
    zero-total boundary is checked separately by check_boundary_zero_total.
    """
    assert part_const != 0, "d=0 makes p a pure power, not an Add"
    assert not has_zero_total(part_const, part_exp_coeff, N)
    k = Symbol('k')
    p_fn = lambda kk: part_const + part_exp_coeff * 2 ** kk

    doit_expr, n = real_doit_symbolic(p_fn)

    # (a) the patched form must actually have fired
    assert doit_expr.has(exp) and doit_expr.has(Sum) and doit_expr.has(log), (
        "patched is_Add branch did not fire for %s: doit=%s"
        % (label, doit_expr))

    real_val = doit_expr.subs(n, N).doit()

    # deep model on the concrete per-index part values
    base = [part_const for _ in range(N)]
    comp = [part_exp_coeff * (2 ** i) for i in range(N)]
    model_val = prod_of_totals(base, comp)

    # also the direct patched form exp(Sum(log(p), (k, 0, N-1)))
    real_exp = exp(Sum(log(p_fn(k)), (k, 0, N - 1))).doit()

    assert Integer(model_val) == sympify(real_val), (
        "A-reference unsound (%s, N=%d): deep model prod_of_totals=%s, "
        "real Product.doit=%s" % (label, N, model_val, real_val))
    assert Integer(model_val) == sympify(real_exp), (
        "A-reference unsound (%s, N=%d): deep model prod_of_totals=%s, "
        "real exp(Sum(log))=%s" % (label, N, model_val, real_exp))

    bug_val = prod_one(base) + prod_one(comp)
    return model_val, bug_val


def check_boundary_zero_total():
    """Domain-boundary confirmation: on an input where some per-index total is
    ZERO (excluded by model.py's Requires), the real callee does NOT produce
    the integer 0 -- `log(0) = zoo` makes both the routed `Product.doit` and
    the direct `exp(Sum(log(p)))` evaluate to the undefined `exp(zoo)`. This
    is exactly why the precondition excludes zero totals."""
    from sympy import zoo
    k = Symbol('k')
    n = Symbol('n')
    confirmed = 0
    for d, c, N in ((-1, 1, 1), (-1, 1, 4), (-2, 1, 4), (-4, 1, 3)):
        assert has_zero_total(d, c, N)
        p = d + c * 2 ** k
        direct = exp(Sum(log(p), (k, 0, N - 1))).doit()
        assert direct.has(zoo), (
            "zero-total boundary broke: exp(Sum(log)) gave %s for (d=%d,c=%d,"
            "N=%d), expected an undefined exp(zoo)" % (direct, d, c, N))
        routed = Product(p, (k, 0, n - 1)).doit().subs(n, N).doit()
        assert routed.has(zoo), (
            "zero-total boundary broke: Product.doit gave %s for (d=%d,c=%d,"
            "N=%d), expected an undefined exp(zoo)" % (routed, d, c, N))
        confirmed += 1
    return confirmed


def main():
    # constant part `d`, exponential coefficient `c`: multiplicand d + c*2**k.
    # (c, d) = (n, 1) is exactly the F2P numerator 2**k*n + 1 with n concrete.
    # Negative constant parts included: nonzero-total negative inputs are IN
    # the modeled domain and must also match the deep model.
    cases = [
        ("F2P shape n=const: 1 + 2*2^k", 1, 2),
        ("F2P shape n=const: 1 + 3*2^k", 1, 3),
        ("F2P shape n=const: 1 + 5*2^k", 1, 5),
        ("2 + 1*2^k", 2, 1),
        ("3 + 4*2^k", 3, 4),
        ("1 + 1*2^k", 1, 1),
        ("7 + 2*2^k", 7, 2),
        ("-3 + 1*2^k", -3, 1),
        ("-9 + 2*2^k", -9, 2),
        ("-5 + 3*2^k", -5, 3),
    ]

    checked = 0
    n_discriminating = 0
    for label, d, c in cases:
        for N in range(1, 7):          # range length 1 .. 6 (>=1)
            if has_zero_total(d, c, N):
                continue               # outside the modeled domain (Requires)
            model_val, bug_val = check_reference(d, c, N, label)
            checked += 1
            if N >= 2 and model_val != bug_val:
                n_discriminating += 1

    # randomized fuzz over (const part d, exp coeff c, range length N).
    # d spans NEGATIVE and positive values; d == 0 is excluded because then p
    # is a pure power (not an Add) and the modeled branch cannot fire; inputs
    # with a zero per-index total are excluded by model.py's Requires.
    rng = random.Random(13551)
    for _ in range(300):
        d = rng.randint(-9, 9)
        c = rng.randint(1, 9)
        N = rng.randint(1, 6)
        if d == 0 or has_zero_total(d, c, N):
            continue
        model_val, bug_val = check_reference(d, c, N, "fuzz")
        checked += 1
        if N >= 2 and model_val != bug_val:
            n_discriminating += 1

    assert n_discriminating > 0, (
        "no discriminating witness found -- the bug would be invisible")

    n_boundary = check_boundary_zero_total()

    print("G-AX OK: deep model prod_of_totals == real exp(Sum(log(p))) / "
          "Product.doit (patched is_Add branch) on %d in-domain inputs (incl. "
          "negative totals); the pre-patch sum-of-part-products differs on %d "
          "of them (the discriminator the F2P test observes); %d zero-total "
          "boundary inputs confirmed undefined (exp(zoo)) in the real callee, "
          "matching the Requires exclusion."
          % (checked, n_discriminating, n_boundary))
    return 0


if __name__ == "__main__":
    sys.exit(main())
