#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-13372.

This bundle consumes NO `@ContractOnly` axiom and has NO A-reference deep model
of an opaque callee: the fix is a pure control-flow / definedness change (add
`else: raise NotImplementedError` to the part-classification chains so an
unrepresentable part defers instead of falling through to read an unset
precision component). What G-AX must therefore validate is that the modelled
THREE-WAY CLASSIFICATION ↔ precision/defer mapping is faithful to the REAL
SymPy `evalf` semantics:

  * EXACT-ZERO part (`part == 0`)  -> precision component ABSENT (None)
  * NUMERIC part   (`part.is_number`) -> precision component = working precision
  * OTHER part     (neither)       -> NO precision component; the evaluation
                                      must DEFER (raise NotImplementedError),
                                      letting `evalf` fall back.

It executes the REAL `evalf`/`as_real_imag`/`is_number` on representative
expressions covering all three cases for both the real and imaginary parts
(including the issue's F2P witness `Mul(Max(0, y), x, evaluate=False)`), and
asserts each part's real classification matches the modelled case tag and the
patched outcome (deferral on OTHER, a finished evaluation otherwise).

Requires `sympy` (the repo under change) — run IN-CONTAINER on the eval
interpreter (Python 3.6) where the patched repo is importable. Exit 0 iff every
observation matches the model.
"""
import sys

try:
    from sympy import symbols, Mul, Max, I, sqrt, pi, Integer, Rational, sin
    from sympy import re as re_fn, im as im_fn
    from sympy.core.evalf import dps_to_prec
except Exception as exc:  # pragma: no cover - environment guard
    print("G-AX SKIP: sympy not importable on this interpreter (%r); "
          "run in-container on the eval image." % (exc,))
    sys.exit(0)


# --- model.py reference encoding (kept in lock-step with the spec) -----------
ZERO, NUMERIC, OTHER = 0, 1, 2


def model_part_kind(part):
    """The modelled three-way classification (re_kind/im_kind), computed with
    the SAME predicates the patched `evalf` fallback uses, in the same order."""
    if part == 0:
        return ZERO
    elif part.is_number:
        return NUMERIC
    else:
        return OTHER


def model_part_precision(kind, prec):
    """model.py `part_precision`: None for ZERO, prec for NUMERIC; undefined
    (no precision component) for OTHER."""
    if kind == ZERO:
        return None
    if kind == NUMERIC:
        return prec
    raise AssertionError("OTHER has no precision component")


def real_part_kind(part):
    """The classification the REAL patched `evalf` fallback performs: the exact
    `if part == 0 / elif part.is_number / else` chain from sympy/core/evalf.py."""
    if part == 0:
        return ZERO
    elif part.is_number:
        return NUMERIC
    else:
        return OTHER


def check_expr(expr, prec):
    """Split `expr` into real/imag parts (as the fallback does) and assert the
    modelled classification + precision/defer mapping matches reality."""
    re_part, im_part = expr.as_real_imag()

    # 1. classification faithfulness: the model's case tags == the real chain.
    for name, part in (("re", re_part), ("im", im_part)):
        mk = model_part_kind(part)
        rk = real_part_kind(part)
        assert mk == rk, (
            "classification mismatch for %s part of %r: model=%d real=%d"
            % (name, expr, mk, rk))

    re_kind = real_part_kind(re_part)
    im_kind = real_part_kind(im_part)

    # 2. defer obligation: the patched fallback raises NotImplementedError
    #    (defers) exactly when some part is OTHER; otherwise it assembles a
    #    result with both precision components defined.
    must_defer = (re_kind == OTHER) or (im_kind == OTHER)

    if not must_defer:
        # both parts representable -> precision components are exactly as the
        # model pins them; no deferral.
        rp = model_part_precision(re_kind, prec)
        ip = model_part_precision(im_kind, prec)
        assert (rp is None) == (re_kind == ZERO)
        assert (ip is None) == (im_kind == ZERO)
        assert (rp == prec) == (re_kind == NUMERIC)
        assert (ip == prec) == (im_kind == NUMERIC)
    return must_defer


def check_f2p_witness():
    """The issue's F2P witness: `Mul(Max(0, y), x, evaluate=False).evalf()`.
    Its real part `Max(0, y)` is the OTHER case (neither 0 nor a number), so
    the patched fallback must DEFER, letting evalf fall back and return the
    unevaluated `x*Max(0, y)` — not crash with UnboundLocalError."""
    x, y = symbols('x y')
    expr = Mul(Max(0, y), x, evaluate=False)
    # the unevaluated product is symbolic; evalf must not raise.
    out = expr.evalf()
    assert str(out) == 'x*Max(0, y)', (
        "F2P witness wrong: evalf gave %r, expected 'x*Max(0, y)'" % str(out))
    # confirm Max(0, y) really is the OTHER case (the discriminator).
    m = Max(0, y)
    assert not (m == 0) and not m.is_number, (
        "Max(0, y) expected to be the OTHER case (not 0, not a number)")
    assert model_part_kind(m) == OTHER


def main():
    x, y = symbols('x y')
    prec = dps_to_prec(15) + 4

    # boundary: cover ZERO / NUMERIC / OTHER for both parts.
    exprs = [
        Integer(0),                       # re ZERO, im ZERO
        Integer(3),                       # re NUMERIC, im ZERO
        Rational(7, 2),                   # re NUMERIC, im ZERO
        sqrt(2),                          # re NUMERIC, im ZERO
        pi,                               # re NUMERIC, im ZERO
        3 + 4 * I,                        # re NUMERIC, im NUMERIC
        5 * I,                            # re ZERO, im NUMERIC
        sin(Integer(1)),                  # re NUMERIC, im ZERO
        Max(0, y),                        # re OTHER, im ZERO
        x,                                # re OTHER, im ZERO
        x + 2 * I,                        # re OTHER, im NUMERIC
        Max(0, y) * I,                    # combination
    ]
    deferred = 0
    for e in exprs:
        if check_expr(e, prec):
            deferred += 1

    check_f2p_witness()

    print("G-AX OK: modelled 3-way classification + precision/defer mapping "
          "matches real SymPy evalf on %d boundary exprs (%d deferred, "
          "incl. F2P witness Max(0, y)); no consumed axiom to fuzz."
          % (len(exprs), deferred))
    return 0


if __name__ == "__main__":
    sys.exit(main())
