#!/usr/bin/env python3
"""G-CONF differential conformance check for sympy__sympy-24562 (nagini).

SHADOW: the impl region of model.py's `combine_ratio`, copied verbatim below
with the contract calls stripped. `ToSeq` becomes a plain tuple shim; the
@ContractOnly callee `read_int` calls the REAL repo reader (per mapping.md the
integer value a whole-number digit token resolves to when the constructor
parses it -- computed here by resolving the token through the patched
constructor itself and reading the resulting numerator).

ORACLE: the REAL patched repo function the model models per mapping.md --
the integer-combination block of `Rational.__new__` in
/testbed/sympy/core/numbers.py, exercised through `Rational(dividend,
divisor)`. The gate applies the diff to /testbed before this script runs
(PYTHONPATH=/testbed); this script never applies any diff itself.

Type bridge (mapping.md section 2):
  p_num, p_den (p_den >= 1)  <->  the dividend operand resolved to an exact
      ratio: passed either as a plain int (p_den == 1) or as a pre-built
      exact ratio `Rational(p_num, p_den, 1)` (the third argument preserves a
      non-coprime pair, so the resolved numerator/denominator are exactly
      p_num/p_den), or as text that resolves to that ratio.
  q_digits: List[int] of decimal code points  <->  the divisor's numerator,
      value read_int(q_digits); q_den >= 1 the divisor's denominator. The
      divisor operand is passed as the digit token itself (q_den == 1, the
      textual shape), as a plain int, as `Rational(value, q_den, 1)`, or as
      "token/q_den" text when that text resolves to exactly (value, q_den).
  Result() = (out_num, out_den)  <->  the constructed ratio BEFORE
      common-factor reduction. The real constructor's observable is the
      reduced object; the reduction step is unchanged and ratio-preserving
      (mapping.md section 2 / refinement.md A7), so the comparison is by
      ratio: Fraction(out_num, out_den) == Fraction(r.p, r.q). A zero
      denominator maps to the constructor's special values (NaN when the
      numerator is also zero, ComplexInfinity otherwise).

>= 1e5 Requires-satisfying inputs: structured boundary cases (the F2P grid
shapes, zero/leading-zero tokens, non-coprime pairs, negative dividends,
large magnitudes) plus 100000 fuzz inputs. Pinned fuzz seed: 245620.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only (random, fractions, math).
"""
import json
import math
import random
import sys
from fractions import Fraction

SEED = 245620
N_FUZZ = 100_000


# --- shims for the model's carriers -------------------------------------------

def ToSeq(xs):
    """PSeq view of a list: a plain tuple."""
    return tuple(xs)


def _make_read_int(Rational):
    """The @ContractOnly callee `read_int`: the REAL repo reader of a
    whole-number digit token -- resolve the token through the patched
    constructor and take the numerator of the resulting exact integer."""
    def read_int(digits):
        s = "".join(chr(c) for c in digits)
        return int(Rational(s).p)
    return read_int


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def _make_combine_ratio(read_int):
    def combine_ratio(p_num, p_den, q_digits, q_den):
        # The integer value of the divisor's textual numerator.
        q_value = read_int(ToSeq(q_digits))  # type: int
        # The numerator picks up the divisor's denominator; the denominator picks
        # up the dividend's denominator and the divisor's integer value.
        out_num = p_num * q_den  # type: int
        out_den = p_den * q_value  # type: int
        return (out_num, out_den)
    return combine_ratio


# --- bridge helpers ------------------------------------------------------------

def digits_of(s):
    """Model carrier for a digit token: the list of its code points."""
    return [ord(c) for c in s]


def requires_ok(p_num, p_den, q_digits, q_den):
    return (p_den >= 1 and q_den >= 1 and len(q_digits) >= 1
            and all(48 <= d <= 57 for d in q_digits))


def real_outcome(Rational, nan, zoo, p_input, q_input):
    """Run the REAL constructor on the two operands and map the observable to
    a comparable form: ('ratio', Fraction) for an exact result, ('nan',) /
    ('zoo',) for the zero-denominator special values."""
    r = Rational(p_input, q_input)
    if r is nan:
        return ("nan",)
    if r is zoo:
        return ("zoo",)
    return ("ratio", Fraction(int(r.p), int(r.q)))


def shadow_outcome(pair):
    """Map the shadow's pre-reduction pair to the same comparable form."""
    out_num, out_den = pair
    if out_den == 0:
        return ("nan",) if out_num == 0 else ("zoo",)
    return ("ratio", Fraction(out_num, out_den))


def check_one(env, p_input, q_input, p_num, p_den, q_digits, q_den):
    Rational, nan, zoo, combine_ratio = env
    assert requires_ok(p_num, p_den, q_digits, q_den)
    shadow = shadow_outcome(combine_ratio(p_num, p_den, q_digits, q_den))
    real = real_outcome(Rational, nan, zoo, p_input, q_input)
    if shadow != real:
        return ("DISAGREEMENT\n"
                "  real call: Rational(%r, %r)\n"
                "  model input: p_num=%r p_den=%r q_digits=%r (token %r) "
                "q_den=%r\n"
                "  shadow=%r  real=%r"
                % (p_input, q_input, p_num, p_den, q_digits,
                   "".join(chr(c) for c in q_digits), q_den, shadow, real))
    return None


def resolved(Rational, x):
    """Resolve an operand to its exact (numerator, denominator) pair, the
    model's view of it (mapping.md section 2)."""
    r = Rational(x)
    return int(r.p), int(r.q)


def boundary_cases(Rational):
    """Structured cases: each yields (p_input, q_input, p_num, p_den,
    q_digits, q_den). Covers the F2P grid shapes (textual/float/int operands),
    zero and leading-zero tokens, non-coprime pairs, negative dividends."""
    cases = []

    def text_case(p_text, q_text):
        # both operands textual/native; the divisor text resolves to
        # (value, den) with the token spelled by the value's decimal digits
        p_num, p_den = resolved(Rational, p_text)
        qv, qd = resolved(Rational, q_text)
        cases.append((p_text, q_text, p_num, p_den, digits_of(str(qv)), qd))

    # the F2P 3x3 grid: ('1.5', 1.5, 2) x ('1.5', 1.5, 2)
    for p in ("1.5", 1.5, 2):
        for q in ("1.5", 1.5, 2):
            text_case(p, q)
    # the headline shape and near variants
    text_case("0.5", "100")
    text_case("2", "100")
    text_case(2, "100")
    text_case("0.25", "8")
    # pure digit-token divisors incl. leading zeros and zero value
    for tok in ("0", "1", "9", "007", "0100", "100100", "000",
                "12345678901234567890123"):
        for p_pair in ((1, 1), (1, 2), (-3, 4), (0, 7), (10**20, 3)):
            p_num, p_den = p_pair
            p_input = Rational(p_num, p_den, 1)
            cases.append((p_input, tok, p_num, p_den, digits_of(tok), 1))
            cases.append((p_input, int(tok), p_num, p_den, digits_of(tok), 1))
    # "token/den" text where the text resolves to exactly (value, den)
    for tok, den in (("007", 5), ("1", 2), ("100", 3), ("9", 4),
                     ("13", 1000000)):
        assert math.gcd(int(tok), den) == 1
        for p_pair in ((1, 1), (3, 2), (-7, 6), (0, 1)):
            p_num, p_den = p_pair
            p_input = Rational(p_num, p_den, 1)
            cases.append((p_input, "%s/%d" % (tok, den),
                          p_num, p_den, digits_of(tok), den))
    # non-coprime pairs on both sides, passed as pre-built exact ratios
    for p_num, p_den, tok, den in ((4, 6, "10", 15), (-8, 4, "6", 9),
                                   (0, 5, "0", 3), (100, 100, "100", 100)):
        p_input = Rational(p_num, p_den, 1)
        q_input = Rational(int(tok), den, 1)
        cases.append((p_input, q_input, p_num, p_den, digits_of(tok), den))
    return cases


def main():
    # REAL repo symbols (the module the model models, per mapping.md):
    from sympy import Rational, nan, zoo

    read_int = _make_read_int(Rational)
    combine_ratio = _make_combine_ratio(read_int)
    env = (Rational, nan, zoo, combine_ratio)

    checked = 0
    n_boundary = 0
    for case in boundary_cases(Rational):
        err = check_one(env, *case)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        # dividend: any exact ratio with positive denominator
        p_num = rng.randint(-10 ** rng.randint(1, 12), 10 ** rng.randint(1, 12))
        p_den = rng.randint(1, 10 ** rng.randint(1, 12))
        # divisor numerator: a random digit token (occasionally all zeros or
        # with leading zeros); divisor denominator positive
        L = rng.randint(1, 20)
        roll = rng.random()
        if roll < 0.05:
            tok = "0" * L
        elif roll < 0.15:
            tok = "0" * rng.randint(1, 3) + "".join(
                rng.choice("0123456789") for _ in range(L))
        else:
            tok = "".join(rng.choice("0123456789") for _ in range(L))
        q_den = 1 if rng.random() < 0.4 else rng.randint(1, 10 ** rng.randint(1, 9))
        qv = int(tok)

        # dividend operand form
        if p_den == 1 and rng.random() < 0.5:
            p_input = p_num
        else:
            p_input = Rational(p_num, p_den, 1)

        # divisor operand form
        if q_den == 1:
            form = rng.random()
            if form < 0.4:
                q_input = tok                      # the textual shape
            elif form < 0.7:
                q_input = qv
            else:
                q_input = Rational(qv, 1, 1)
        elif math.gcd(qv, q_den) == 1 and rng.random() < 0.3:
            q_input = "%s/%d" % (tok, q_den)       # text resolving to (qv, q_den)
        else:
            q_input = Rational(qv, q_den, 1)

        err = check_one(env, p_input, q_input,
                        p_num, p_den, digits_of(tok), q_den)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real patched constructor on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
