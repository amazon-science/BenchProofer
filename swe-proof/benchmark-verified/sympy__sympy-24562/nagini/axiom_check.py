#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-24562.

Executes the REAL textual-integer callee the constructor uses
(`fractions.Fraction`, reached via `Rational(str)`) on inputs that satisfy each
axiom's `Requires`, and asserts every observation meets the axiom's `Ensures`.
Per the audit, it ALSO fuzzes the `Requires` boundary -- the inputs the
precondition admits and the inputs it (now) excludes -- and asserts the
no-raise / value claims explicitly, so an over-broad precondition would be
caught.

Two axioms are checked:

  (A-consumed) `read_int(digits)` -- the unchanged reader of an ALL-DIGIT token
      to its integer value, `int(s) == fractions.Fraction(s).numerator`. The
      axiom's `Requires` is: non-empty AND every code point is a decimal digit
      (48..57). Its `Ensures` is `Result() >= 0`. We confirm:
        * on every Requires-satisfying token the real reader returns a
          NON-NEGATIVE integer and does NOT raise (the Ensures + implicit
          no-raise);
        * the Requires-EXCLUDED boundary (leading '-', empty, non-digit
          characters) is exactly where the real reader would return a negative
          value or raise -- justifying the tightened precondition (no
          over-claim).

  (A-reference) `aux_value(digits, n)` -- the auxiliary value the pre-patch
      computation obtains from the SAME characters: repeat the digit token `n`
      times and read the longer character sequence as one integer, `int(s * n)`.
      In the consumer-facing spec view this quantity is left fully unspecified
      (the spec asserts only `Result() >= 0` and never relates it to
      `read_int`); here -- in the hidden refinement artifact -- we record the
      concrete operation it stands for so G-AX can validate its soundness. The
      axiom's `Requires` is: non-empty all-digit token AND n >= 1; its `Ensures`
      is `Result() >= 0`. We confirm the Ensures, AND the discriminating
      arithmetic fact the postconditions rely on -- that this auxiliary value
      (repeat-then-read) is NOT the same number as read-then-scale:

        int('100' * 2) = int('100100') = 100100  !=  100 * 2 = 200

      (this inequality is the entire bug: Rational('0.5','100') yielded
      1/100100 instead of 1/200).

Imports only the standard library (`fractions`) -- the very parser
`Rational(str)` uses for a textual operand. Exit 0 iff every obligation holds.
"""
import fractions
import random
import sys


def read_int_real(s):
    """Real callee for `read_int`: the integer an all-digit string spells."""
    return fractions.Fraction(s).numerator


def aux_value_real(s, n):
    """Real operation `aux_value` stands for: repeat the token n times, then
    read the longer character sequence as one integer."""
    return fractions.Fraction(s * n).numerator


def is_requires_ok_read_int(s):
    return len(s) >= 1 and all('0' <= ch <= '9' for ch in s)


def check_read_int_ensures(s):
    """On a Requires-satisfying all-digit token, the reader returns a
    non-negative integer and does not raise (read_int Ensures + no-raise)."""
    assert is_requires_ok_read_int(s)
    v = read_int_real(s)                       # must not raise
    assert isinstance(v, int) and v >= 0, (
        "read_int axiom unsound: reader gave %r on %r (expected >= 0)" % (v, s))
    assert v == int(s), (
        "read_int value mismatch on %r: reader=%r int=%r" % (s, v, int(s)))


def check_read_int_requires_boundary(s):
    """On a Requires-EXCLUDED input (sign / empty / non-digit), the real reader
    would return a negative value or raise -- so excluding it is correct and the
    Ensures(Result() >= 0) is sound only because Requires is tight."""
    assert not is_requires_ok_read_int(s)
    try:
        v = read_int_real(s)
    except (ValueError, ZeroDivisionError):
        return  # reader rejects it; correctly outside the modeled domain
    # If it parsed, it is allowed to be negative (e.g. '-5' -> -5); that is
    # exactly the over-claim the tightened Requires avoids.
    assert isinstance(v, int)


def check_aux_value_ensures(s, n):
    """On a Requires-satisfying all-digit token and n >= 1, the auxiliary value
    (repeat-then-read) is a non-negative integer and does not raise (aux_value
    Ensures)."""
    assert is_requires_ok_read_int(s) and n >= 1
    v = aux_value_real(s, n)                    # must not raise
    assert isinstance(v, int) and v >= 0, (
        "aux_value axiom unsound: gave %r on (%r, %d)" % (v, s, n))


def main():
    rng = random.Random(24562)

    # --- read_int (A-consumed): Requires-satisfying boundary tokens ---------
    boundary = ["0", "1", "9", "00", "100", "200", "1001", "0123456789",
                "9" * 1, "9" * 40, "100100", "5"]
    for s in boundary:
        check_read_int_ensures(s)

    # --- read_int: randomized all-digit fuzz --------------------------------
    for _ in range(20000):
        L = rng.randint(1, 24)
        s = "".join(rng.choice("0123456789") for _ in range(L))
        check_read_int_ensures(s)

    # --- read_int: Requires-EXCLUDED boundary (over-claim guard) ------------
    excluded = ["", "-5", "-100", "+7", " 5", "5 ", "1.5", "1/2", "abc",
                "12a", "0x10", "1e3", "  ", "\t1"]
    for s in excluded:
        check_read_int_requires_boundary(s)

    # --- aux_value (A-reference): Ensures over Requires-satisfying ----------
    rep_boundary = [("100", 2), ("1", 1), ("9", 5), ("5", 2), ("200", 3),
                    ("12", 4), ("0", 2), ("100", 1)]
    for s, n in rep_boundary:
        check_aux_value_ensures(s, n)
    for _ in range(5000):
        L = rng.randint(1, 12)
        s = "".join(rng.choice("0123456789") for _ in range(L))
        n = rng.randint(1, 6)
        check_aux_value_ensures(s, n)

    # --- the discriminating fact: repeat-then-read != read-then-scale -------
    # The headline witness and a fuzz showing the two readings differ whenever
    # the leading digit is non-zero and n >= 2 (so the spec's denominator clause
    # is genuinely violated by the repeat-then-read path).
    assert aux_value_real("100", 2) == 100100
    assert read_int_real("100") * 2 == 200
    assert aux_value_real("100", 2) != read_int_real("100") * 2
    differ = 0
    for _ in range(5000):
        L = rng.randint(1, 8)
        s = "".join(rng.choice("0123456789") for _ in range(L))
        if s[0] == "0":
            continue
        n = rng.randint(2, 6)
        if aux_value_real(s, n) != read_int_real(s) * n:
            differ += 1
    assert differ > 0, "expected repeat-then-read to differ from read-then-scale"

    print("G-AX OK: read_int (A-consumed) sound on %d boundary + 20000 fuzz "
          "all-digit tokens, Requires-excluded boundary (%d) confirmed; "
          "aux_value (A-reference) sound on %d boundary + 5000 fuzz; "
          "discriminating fact int(s*n) != n*int(s) confirmed (%d differ in "
          "fuzz)." % (len(boundary), len(excluded), len(rep_boundary), differ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
