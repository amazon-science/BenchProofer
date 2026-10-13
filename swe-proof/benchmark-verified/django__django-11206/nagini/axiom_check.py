#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11206.

This bundle consumes NO `@ContractOnly` axiom: the smallness decision and the
plain-zero rendering are the CHANGED behaviour and are modelled DEEPLY in
model.py (`below_cutoff`, `zero_render`). What is validated out-of-band here is
that those deep models equal the REAL arithmetic they refine -- the two
A-reference checks:

  (A-reference 1) the deep decision `below_cutoff(coeff, exponent, decimal_pos)`
      (the cross-multiplied integer test in model.py) equals the REAL Decimal
      comparison the patch performs:
          cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
          abs(number) < cutoff
      where `(coeff, exponent)` is the magnitude decomposition of `number` from
      `Decimal.as_tuple()` (value = coeff * 10**exponent, coeff >= 0).

  (A-reference 2) the deep rendering `zero_render(decimal_pos)` (model.py)
      equals the REAL fixed-point rendering of `Decimal('0')` at that precision
      with the '.' separator -- the string the formatter emits once a
      below-window value has been collapsed to zero:
          '0'                       when decimal_pos == 0
          '0.' + '0' * decimal_pos  when decimal_pos >= 1

Imports nothing repo-specific: `decimal` is the Python standard library -- the
same module the gold patch uses. The real Django cutoff expression and the
zero-rendering arithmetic are reproduced verbatim from the patched
`django/utils/numberformat.format` so the check exercises the real semantics,
not a paraphrase. Exit 0 iff every obligation holds.
"""
import decimal
import random
import sys
from decimal import Decimal


# --- model.py reference encodings (kept in lock-step with the deep model) ----

def m_threshold_exp(decimal_pos):
    return decimal_pos if decimal_pos >= 1 else 1


def m_pow10(n):
    return 10 ** n


def below_cutoff_model(coeff, exponent, decimal_pos):
    """Reference of model.py `below_cutoff`: the cross-multiplied integer test
    coeff * 10**(exponent + threshold_exp) < 1, with coeff >= 0."""
    assert coeff >= 0 and decimal_pos >= 0
    if coeff == 0:
        return True
    shifted = exponent + m_threshold_exp(decimal_pos)
    if shifted >= 0:
        return False
    return coeff < m_pow10(-shifted)


def zero_render_model(decimal_pos):
    """Reference of model.py `zero_render` as a code-point list."""
    if decimal_pos == 0:
        return [ord('0')]
    return [ord('0'), ord('.')] + [ord('0')] * decimal_pos


# --- the real arithmetic the deep model refines ------------------------------

def coeff_exponent(number):
    """The non-negative magnitude decomposition used by model.py:
    value = coeff * 10**exponent, coeff >= 0 (the integer of the digit tuple)."""
    _, digits, exponent = abs(number).as_tuple()
    coeff = 0
    for d in digits:
        coeff = coeff * 10 + d
    return coeff, exponent


def real_below_cutoff(number, decimal_pos):
    """The REAL smallness decision the gold patch performs (verbatim cutoff)."""
    cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
    return abs(number) < cutoff


def real_zero_render(decimal_pos):
    """The REAL fixed-point rendering of Decimal('0') at `decimal_pos` places
    with the '.' separator, reproduced from the post-patch numberformat.format
    tail: str_number='0', no '.', so int_part='0', dec_part='' then padded with
    decimal_pos zeros, joined by the separator only when non-empty."""
    number = Decimal('0')
    str_number = '{:f}'.format(number)            # '0'
    assert str_number == '0'
    if '.' in str_number:
        int_part, dec_part = str_number.split('.')
    else:
        int_part, dec_part = str_number, ''
    if decimal_pos is not None:
        dec_part = dec_part + ('0' * (decimal_pos - len(dec_part)))
    dec_part = dec_part and '.' + dec_part         # decimal_sep = '.'
    rendered = int_part + dec_part
    return [ord(ch) for ch in rendered]


# --- the checks --------------------------------------------------------------

def check_decision(number, decimal_pos):
    coeff, exponent = coeff_exponent(number)
    model = below_cutoff_model(coeff, exponent, decimal_pos)
    real = real_below_cutoff(number, decimal_pos)
    assert model == real, (
        "below_cutoff deep model unsound on number=%r decimal_pos=%d: "
        "model=%r real(abs<cutoff)=%r (coeff=%d exponent=%d)"
        % (str(number), decimal_pos, model, real, coeff, exponent))


def check_render(decimal_pos):
    model = zero_render_model(decimal_pos)
    real = real_zero_render(decimal_pos)
    assert model == real, (
        "zero_render deep model unsound at decimal_pos=%d: model=%r real=%r"
        % (decimal_pos, model, real))


def main():
    # plenty of working precision so abs/as_tuple/comparison are exact
    decimal.getcontext().prec = 400

    # --- A-reference 2: zero rendering at every relevant precision ---------
    for dp in range(0, 33):
        check_render(dp)

    # --- A-reference 1: the decision on the documented boundary cases ------
    # (problem statement + F2P/P2P tests), including the strict-equality edge
    boundary = [
        ('1e-199', 2), ('1e-200', 2),       # problem statement witnesses
        ('1e-7', 8), ('1e-8', 8), ('1e-9', 8),   # the < vs == boundary at 1e-8
        ('1e-10', 8), ('1e-11', 8),
        ('0.00000001', 8),                  # == cutoff: NOT below
        ('9e-19', 2),
        ('.00000000000099', 0),             # decimal_pos == 0 -> cutoff 0.1
        ('0.' + '0' * 299 + '1234', 3),     # ~1.234e-300 -> below at dp=3
        ('1' + '0' * 300, 3),               # huge: not below
        ('1.2345e999', 2), ('9e9999', 3), ('9e201', 0), ('9e200', 0),
        ('0', 0), ('0', 5), ('0.0', 4),     # exact zero magnitude
        ('1234.5678', 2), ('-1234.33', 1),  # ordinary magnitudes: not below
        ('-9e-50', 4), ('-1e-3', 3), ('-1e-4', 3),  # negatives via abs()
    ]
    for value, dp in boundary:
        check_decision(Decimal(value), dp)
        # the exact-threshold edge: a magnitude equal to 10**-max(dp,1) must
        # NOT be below (strict comparison)
    for dp in range(0, 30):
        e = dp if dp >= 1 else 1
        at = Decimal(1).scaleb(-e)               # exactly the cutoff
        check_decision(at, dp)
        check_decision(at.scaleb(1), dp)         # ten times the cutoff
        check_decision(at.scaleb(-1), dp)        # a tenth of the cutoff
        check_decision(-at, dp)
        check_decision(Decimal(0), dp)

    # --- A-reference 1: randomized fuzz over wide magnitude/precision ------
    rng = random.Random(11206)
    for _ in range(200000):
        dp = rng.randint(0, 20)
        # coefficient 1..9999, scale exponent across a wide window straddling
        # the cutoff so both branches and the strict edge are exercised
        coeff = rng.randint(1, 9999)
        exp = rng.randint(-(dp + 8), 4)
        sign = rng.choice(['', '-'])
        number = Decimal('%s%dE%d' % (sign, coeff, exp))
        check_decision(number, dp)

    print("G-AX OK: below_cutoff deep model (== real abs(number) < "
          "Decimal('0.'+'1'.rjust(dp,'0'))) sound on boundary + exact-edge + "
          "200000 fuzz; zero_render deep model (== real Decimal('0') "
          "rendering) sound on decimal_pos 0..32.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
