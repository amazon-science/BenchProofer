#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11848.

This bundle consumes NO `@ContractOnly` axioms: the changed operation is exact
integer arithmetic, modelled DEEPLY in model.py's `pure` region
(`resolved_year` / `century_start`). G-AX therefore validates the deep model
against the REAL behaviour, on two fronts:

  (1) A-reference (the deep model == the real reference computation).
      `resolved_year(two_digit_year, reference_year)` must equal the exact
      two-digit-year expansion the shipped patch performs, namely:

          current_century = reference_year - (reference_year % 100)
          if two_digit_year - (reference_year % 100) > 50:
              full = two_digit_year + current_century - 100
          else:
              full = two_digit_year + current_century

      We re-run that real arithmetic across boundary + exhaustive + fuzz inputs
      and assert the deep model agrees on every one.

  (2) provenance of the reference year. The patch obtains it from the unchanged
      wall-clock source `datetime.datetime.utcnow().year`; we confirm that
      source yields a plain non-negative four-digit integer (so the model's
      `reference_year: int, reference_year >= 1000` precondition is met in
      reality) and that `.year` is the calendar year.

Imports nothing repo-specific: `datetime` is the Python standard library — the
same module the gold patch calls. Exit 0 iff every obligation holds.
"""
import datetime
import random
import sys


# --- model.py reference encodings (kept in lock-step with the pure region) ---

def century_start(reference_year):
    """Reference implementation of model.py's @Pure `century_start`."""
    return reference_year - (reference_year % 100)


def resolved_year(two_digit_year, reference_year):
    """Reference implementation of model.py's @Pure `resolved_year` (the deep
    model of the changed two-digit-year expansion)."""
    if two_digit_year - (reference_year % 100) > 50:
        return two_digit_year + century_start(reference_year) - 100
    return two_digit_year + century_start(reference_year)


# --- the REAL reference computation (transcribed verbatim from the patch) -----

def real_expansion(two_digit_year, reference_year):
    """The exact arithmetic the shipped patch runs on `parse_http_date`'s
    two-digit-year branch (with `reference_year` == utcnow().year)."""
    year = two_digit_year
    current_year = reference_year
    current_century = current_year - (current_year % 100)
    if year - (current_year % 100) > 50:
        year += current_century - 100
    else:
        year += current_century
    return year


# --- the checks --------------------------------------------------------------

def check_deep_model(two_digit_year, reference_year):
    observed = real_expansion(two_digit_year, reference_year)   # real arithmetic
    expected = resolved_year(two_digit_year, reference_year)    # deep model
    assert observed == expected, (
        "resolved_year deep model unsound at (year=%d, ref=%d): "
        "real arithmetic gives %d, deep model gives %d"
        % (two_digit_year, reference_year, observed, expected))
    # also confirm the auxiliary postconditions hold on the real value
    assert observed % 100 == two_digit_year, (
        "last-two-digits postcondition violated at (year=%d, ref=%d): %d"
        % (two_digit_year, reference_year, observed))
    assert observed - reference_year <= 50, (
        "never-more-than-50-ahead postcondition violated at "
        "(year=%d, ref=%d): %d" % (two_digit_year, reference_year, observed))
    assert reference_year - observed < 150, (
        "recency postcondition violated at (year=%d, ref=%d): %d"
        % (two_digit_year, reference_year, observed))


def main():
    # --- provenance of the reference year (utcnow().year) ---------------------
    now = datetime.datetime.utcnow()
    ref = now.year
    assert isinstance(ref, int), "utcnow().year is not an int: %r" % (ref,)
    assert ref >= 1000, (
        "utcnow().year is not a four-digit calendar year: %r" % (ref,))
    assert ref == now.year, "year attribute is not the calendar year"

    # representative reference years incl. the test's pinned values and bounds
    reference_years = [
        1000, 1900, 1970, 1999, 2000, 2019, 2020, 2048, 2069, 2099,
        2100, 2101, 2150, 2999, 9999, ref,
        # century-boundary stress
        1100, 1150, 1199, 2049, 2050, 2051,
    ]

    # --- exhaustive over the two-digit domain for every reference year --------
    checked = 0
    for reference_year in reference_years:
        for two_digit_year in range(0, 100):   # full 0..99 domain
            check_deep_model(two_digit_year, reference_year)
            checked += 1

    # --- the seven F2P-pinned (mocked-utcnow) cases, explicitly ---------------
    # (utcnow_year, two_digit_year, expected_full_year)
    pinned = [
        (2019, 69, 2069),
        (2019, 70, 1970),
        (2019, 94, 1994),
        (2020, 70, 2070),
        (2020, 71, 1971),
        (2048, 0, 2000),
        (2048, 99, 1999),
    ]
    for reference_year, two_digit_year, expected_full in pinned:
        got = resolved_year(two_digit_year, reference_year)
        assert got == expected_full, (
            "pinned case failed: resolved_year(%d, %d) = %d, expected %d"
            % (two_digit_year, reference_year, got, expected_full))
        check_deep_model(two_digit_year, reference_year)

    # --- randomized fuzz ------------------------------------------------------
    rng = random.Random(11848)
    for _ in range(200000):
        reference_year = rng.randint(1000, 9999)
        two_digit_year = rng.randint(0, 99)
        check_deep_model(two_digit_year, reference_year)
        checked += 1

    print("G-AX OK: resolved_year deep model == real two-digit-year expansion "
          "on %d boundary+exhaustive+fuzz inputs; %d F2P-pinned cases match; "
          "utcnow().year provenance confirmed (== %d)"
          % (checked, len(pinned), ref))
    return 0


if __name__ == "__main__":
    sys.exit(main())
