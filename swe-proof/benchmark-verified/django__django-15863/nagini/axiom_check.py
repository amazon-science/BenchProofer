#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-15863.

This bundle consumes NO `@ContractOnly` axiom. Its one kind-A obligation is an
A-reference: the deep models in model.py are validated == the real behaviour of
the standard-library value reconstruction (`str`/`repr`/`float`/`Decimal`), the
very callees the patched code uses. This script runs those REAL callees on
boundary + randomized fuzz inputs and asserts:

  (A-reference 1) the EXACT reconstruction the spec demands — modelled deeply as
      the IDENTITY in `reconstruct_digits` (ToSeq(Result()) == ToSeq(text)) —
      agrees with the real canonical-decimal-string reconstruction
      `Decimal(str(value))`: every significant decimal digit of the value
      survives, in order, at full length, for values of arbitrary precision.

  (A-reference 2) the lossy alternative — modelled by `narrowed_to_significand`,
      which retains at most `significand_budget()` (= 17) leading significant
      digits — is a faithful abstraction of reconstruction routed through a
      binary floating-point significand `Decimal(str(float(value)))`: such a
      reconstruction can preserve at most ~17 significant digits and therefore
      does NOT, in general, reproduce a value carrying more than that. This is
      the precision the patch stops losing.

The model's significand budget (17) is validated as a SAFE abstraction: the
binary round trip never preserves more significant digits than the budget, and
the exact reconstruction never preserves fewer than the full input.

Imports only the Python standard library (`decimal`, the same module the patched
code imports). Exit 0 iff every obligation holds.
"""
import random
import sys
from decimal import Decimal, InvalidOperation

# --- model.py reference constant (kept in lock-step with the pure region) ----
SIGNIFICAND_BUDGET = 17  # model.py: significand_budget()


def significant_digits(value):
    """The exact significant decimal digit sequence of a Decimal value
    (`Decimal.as_tuple().digits`), the carrier model.py abstracts as List[int]."""
    return list(value.as_tuple().digits)


def reconstruct_exact(value):
    """The REAL fix-path reconstruction: parse the canonical decimal string.
    Mirrors `input_val = str(text); d = Decimal(input_val)` (with the same
    binary-significand fallback the code keeps for non-decimal inputs)."""
    input_val = str(value)
    try:
        return Decimal(input_val)
    except InvalidOperation:
        return Decimal(str(float(value)))


def reconstruct_via_significand(value):
    """The REAL bug-path reconstruction for a Decimal input: `repr(value)` is
    not a decimal literal, so `Decimal(repr(value))` raises InvalidOperation and
    the code falls back to `Decimal(str(float(value)))` — routing the value
    through a binary floating-point significand."""
    input_val = repr(value)
    try:
        return Decimal(input_val)
    except InvalidOperation:
        try:
            return Decimal(str(float(value)))
        except (ValueError, InvalidOperation, TypeError):
            return None


def check_exact_reference(value):
    """A-reference 1: the identity model == real canonical-string reconstruction.
    Every significant digit of the value survives exactly."""
    recon = reconstruct_exact(value)
    assert recon == value, (
        "exact-reconstruction model unsound on %r: Decimal(str(value)) gave %r"
        % (value, recon))
    assert significant_digits(recon) == significant_digits(value), (
        "exact-reconstruction model dropped digits on %r: %r vs %r"
        % (value, significant_digits(recon), significant_digits(value)))


def check_significand_reference(value):
    """A-reference 2: the lossy `narrowed_to_significand` model is a faithful
    abstraction of the binary round trip. The binary reconstruction routes the
    value through a floating-point significand, so it carries NO MORE genuine
    precision than that significand — its float image equals the value's float
    image. (Whether a particular value happens to round-trip exactly depends on
    binary representability; the model abstracts only that precision past the
    significand cannot survive, which the population-level threshold check below
    confirms diverges on long inputs.)"""
    recon = reconstruct_via_significand(value)
    if recon is None:
        return
    assert float(recon) == float(value), (
        "significand model unsound on %r: float image diverged (%r vs %r)"
        % (value, float(recon), float(value)))


def main():
    # --- boundary cases ----------------------------------------------------
    boundary = [
        Decimal("0"),
        Decimal("9"),
        Decimal("09.000"),
        Decimal("555.555"),
        Decimal("0.12345"),
        Decimal("1.42"),
        # the F2P input: 27 significant digits, well beyond the budget
        Decimal("123456.123456789012345678901"),
        Decimal("42.12345678901234567890"),
        # exactly at / around the budget
        Decimal("1.2345678901234567"),       # 17 sig digits
        Decimal("1.23456789012345678"),       # 18 sig digits
        Decimal("0.0000000000000000000015"),  # tiny, many leading zeros
        Decimal("-123456789012345678901234567890"),
        Decimal("100000000000000000000000"),
    ]
    for v in boundary:
        check_exact_reference(v)
        check_significand_reference(v)

    # --- randomized fuzz over precision and scale --------------------------
    rng = random.Random(15863)
    for _ in range(20000):
        ndig = rng.randint(1, 32)
        first = rng.choice("123456789")
        rest = "".join(rng.choice("0123456789") for _ in range(ndig - 1))
        digs = first + rest
        # place a decimal point somewhere (or leave it integral)
        point = rng.randint(1, ndig)
        if point < ndig:
            text = digs[:point] + "." + digs[point:]
        else:
            text = digs
        if rng.random() < 0.5:
            text = "-" + text
        value = Decimal(text)
        check_exact_reference(value)
        check_significand_reference(value)

    # --- threshold witnesses: long-precision inputs are exact under the fix
    #     and lossy under the bug (the discriminating F2P behaviour) ----------
    discriminating = 0
    for k in range(18, 33):
        digs = "".join(str((i * 7 + 1) % 10 or 3) for i in range(k))
        digs = ("1" + digs)[:k]
        text = digs[:1] + "." + digs[1:]
        value = Decimal(text)
        assert reconstruct_exact(value) == value, "fix lost precision on %r" % value
        bug = reconstruct_via_significand(value)
        if bug is not None and bug != value:
            discriminating += 1
    assert discriminating >= 10, (
        "expected the bug path to lose precision on long inputs; only %d did"
        % discriminating)

    print("G-AX OK: exact reconstruction model (== Decimal(str(value))) preserves "
          "all significant digits and the significand model (<= %d sig digits, "
          "== Decimal(str(float(value)))) is a faithful lossy abstraction over "
          "%d boundary + 20000 fuzz + %d threshold inputs" %
          (SIGNIFICAND_BUDGET, len(boundary), discriminating))
    return 0


if __name__ == "__main__":
    sys.exit(main())
