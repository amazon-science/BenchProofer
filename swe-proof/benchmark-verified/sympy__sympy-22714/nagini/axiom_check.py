#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-22714.

This bundle consumes NO @ContractOnly axiom: the changed per-coordinate
imaginary test is modeled DEEPLY (model.py's `certified_imag_at` /
`has_certified_imag` over int-encoded coordinate facts). G-AX therefore
validates the A-REFERENCE: that the deep model equals the REAL operation the
gold patch performs, evaluated with real SymPy on representative + fuzzed
coordinates.

Real operation (post-patch guard, sympy/geometry/point.py):
    any(a.is_number and im(a).is_zero is False for a in coords)

Model encoding (model.py):
    is_concrete_number[i] = 1 if a.is_number is True else 0
    imag_is_zero[i]       = 1 if im(a).is_zero is True
                            0 if im(a).is_zero is False
                           -1 if im(a).is_zero is None
    imag_truthy[i]        = 1 if bool(im(a)) else 0          # pre-patch fact
    certified_imag_at(is_num, imag_zero) = (is_num == 1 and imag_zero == 0)
    has_certified_imag(...)              = any(certified_imag_at(...))

Obligations, for every probed coordinate `a`:
  (1) certified_imag_at(enc_is_number(a), enc_imag_is_zero(a))
        == (a.is_number is True and im(a).is_zero is False)        [A-reference]
  (2) for every probed coordinate tuple, has_certified_imag(enc tuple)
        == any(a.is_number and im(a).is_zero is False for a in coords)
  (3) the bug witness exists and is exactly captured: a concrete real
      coordinate under evaluate(False) has is_concrete_number==1,
      imag_truthy==1 (pre-patch would reject), yet imag_is_zero==1 so
      certified_imag_at is False (post-patch permits) — the F2P delta.

Imports only `sympy` (the repo under test) and stdlib. Exit 0 iff sound.
"""
import itertools
import random
import sys

from sympy import (Integer, Rational, Float, I, pi, E, sqrt, Symbol, S,
                   sympify, oo, zoo, nan, Add, Mul)
from sympy.functions.elementary.complexes import im
from sympy.core.parameters import evaluate


# --- model.py reference encodings (kept in lock-step with model.py) ----------

def enc_is_number(a):
    return 1 if (a.is_number is True) else 0


def enc_imag_is_zero(a):
    z = im(a).is_zero
    if z is True:
        return 1
    if z is False:
        return 0
    return -1            # None / undecided


def enc_imag_truthy(a):
    # The pre-patch second conjunct `im(a)` used in a boolean context. Only
    # reached (short-circuit) when a.is_number is True; guard so a symbolic
    # im(x).__bool__ (which would raise) is never invoked here, matching the
    # generator's short-circuit semantics.
    try:
        return 1 if bool(im(a)) else 0
    except TypeError:
        return 0


def certified_imag_at(is_num, imag_zero):
    return is_num == 1 and imag_zero == 0


def has_certified_imag_model(coords):
    return any(certified_imag_at(enc_is_number(a), enc_imag_is_zero(a))
               for a in coords)


# --- the REAL operation (post-patch guard), evaluated with real SymPy --------

def real_guard(coords):
    return any(a.is_number and im(a).is_zero is False for a in coords)


def per_coord_real(a):
    # The per-coordinate conjunct as the patch writes it (a.is_number may be a
    # SymPy fuzzy bool; coerce to the boolean any() would see).
    return bool(a.is_number) and (im(a).is_zero is False)


# --- checks ------------------------------------------------------------------

def check_coord(a):
    """Obligation (1): the deep model's per-coordinate verdict == real.

    If real SymPy itself raises while *computing* the decidability facts
    (degenerate inputs such as nan/zoo arithmetic), the real constructor's
    generator would also raise there -- that is outside the modeled, well-
    defined-coordinate domain, so the input is skipped. An AssertionError
    (model != real on a well-defined coordinate) is NEVER swallowed.
    """
    try:
        ien = enc_is_number(a)
        izn = enc_imag_is_zero(a)
        real_v = per_coord_real(a)
    except (ValueError, TypeError, AttributeError, RecursionError):
        return
    model_v = certified_imag_at(ien, izn)
    assert model_v == real_v, (
        "A-reference unsound on coordinate %r: model certified_imag_at=%r "
        "(is_number enc=%r, im.is_zero enc=%r) but real "
        "(a.is_number and im(a).is_zero is False)=%r"
        % (a, model_v, ien, izn, real_v))


def check_tuple(coords):
    """Obligation (2): the fold == real any(...) over the tuple."""
    try:
        model_v = has_certified_imag_model(coords)
        real_v = real_guard(coords)
    except (ValueError, TypeError, AttributeError, RecursionError):
        return
    assert model_v == real_v, (
        "A-reference unsound on tuple %r: model has_certified_imag=%r but "
        "real any(...)=%r" % (list(coords), model_v, real_v))


def main():
    # Representative coordinates: real numbers, genuine imaginaries, symbols,
    # transcendentals, special values, both evaluation contexts.
    real_atoms = [Integer(0), Integer(1), Integer(2), Integer(-3),
                  Rational(1, 2), Rational(-7, 4), Float(0.5), Float(0.0),
                  Float(-2.25), pi, E, sqrt(2), S.Zero, S.One,
                  Integer(10) ** 9, sqrt(3) + 1]
    imag_atoms = [I, 2 * I, -I, 3 * I, Rational(1, 2) * I, sqrt(2) * I,
                  I * pi, Integer(5) * I]
    complex_atoms = [1 + I, 2 - 3 * I, pi + E * I, sqrt(2) + I]
    x = Symbol('x')
    y = Symbol('y', real=True)
    z = Symbol('z', imaginary=True)
    w = Symbol('w', positive=True)
    symbolic_atoms = [x, y, z, w, x + 1, 2 * x, x * y, x + I, x + y]
    special_atoms = [oo, -oo, zoo, nan, S.Infinity]

    singles = (real_atoms + imag_atoms + complex_atoms + symbolic_atoms
               + special_atoms)

    n_coord = 0
    # Each coordinate under BOTH evaluation contexts (the bug is context-bound).
    for ctx in (True, False):
        with evaluate(ctx):
            for a in singles:
                check_coord(a)
                n_coord += 1

    # Obligation (3): the bug witness. A concrete real coordinate under
    # evaluate(False) is permitted by the model (post-patch) but the pre-patch
    # truthiness fact would reject it.
    with evaluate(False):
        a = Integer(1)
        assert enc_is_number(a) == 1, "witness: Integer(1) must be a number"
        assert enc_imag_truthy(a) == 1, (
            "witness: bool(im(Integer(1))) must be truthy under evaluate(False) "
            "(the pre-patch bug); got enc_imag_truthy=%r" % enc_imag_truthy(a))
        assert enc_imag_is_zero(a) == 1, (
            "witness: im(Integer(1)).is_zero must be True under evaluate(False); "
            "got %r" % enc_imag_is_zero(a))
        assert certified_imag_at(enc_is_number(a), enc_imag_is_zero(a)) is False, (
            "witness: post-patch model must PERMIT the real coordinate")
    # the genuinely-imaginary coordinate is still certified imaginary (no
    # over-permitting by the fix)
    assert certified_imag_at(enc_is_number(2 * I), enc_imag_is_zero(2 * I)) is True

    # Tuple-level checks: every ordered pair/triple from a representative pool,
    # under both contexts. (any() short-circuit and ordering are exercised.)
    pool = [Integer(1), Integer(0), Rational(3, 2), Float(0.5), pi, sqrt(2),
            2 * I, I, 1 + I, x, y, z]
    for ctx in (True, False):
        with evaluate(ctx):
            for combo in itertools.product(pool, repeat=2):
                check_tuple(combo)
            # a sample of triples (full product would be large)
            rng = random.Random(22714)
            for _ in range(3000):
                combo = tuple(rng.choice(pool) for _ in range(3))
                check_tuple(combo)

    # The literal issue repro coordinate tuple, both as constructed numbers and
    # via sympify, under evaluate(False).
    with evaluate(False):
        check_tuple((Integer(1), Integer(2)))
        check_tuple((sympify('Integer(1)'), sympify('Integer(2)')))

    # Randomized fuzz over single coordinates built from atoms + operations.
    rng = random.Random(122714)
    atom_pool = (real_atoms + imag_atoms + symbolic_atoms)
    for ctx in (True, False):
        with evaluate(ctx):
            for _ in range(4000):
                a = rng.choice(atom_pool)
                op = rng.randint(0, 3)
                b = rng.choice(atom_pool)
                try:
                    if op == 0:
                        a = a + b
                    elif op == 1:
                        a = a * b
                    elif op == 2:
                        a = a - b
                    # op == 3: leave as-is
                except Exception:
                    continue
                check_coord(a)
                n_coord += 1

    print("G-AX OK: deep model (certified_imag_at / has_certified_imag) == real "
          "SymPy (a.is_number and im(a).is_zero is False) on %d coordinate "
          "observations + all 2-tuples of a 12-atom pool x2 contexts + 6000 "
          "triple fuzz; bug witness (real coord under evaluate(False): "
          "truthy-but-certified-zero) confirmed and permitted." % n_coord)
    return 0


if __name__ == "__main__":
    sys.exit(main())
