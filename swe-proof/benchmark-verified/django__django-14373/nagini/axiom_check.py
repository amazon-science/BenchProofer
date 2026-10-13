#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-14373.

This bundle consumes NO axiom: the changed operation — rendering a year as a
fixed four-character zero-padded decimal field — is modelled DEEPLY in model.py
(the place-value digit decomposition `four_field` / `render_year`). G-AX
therefore validates that deep model against the REAL operation the gold patch
performs, `'%04d' % year`, on the full supported year range (the only kind-A
obligation here is this A-reference: deep model == real rendering).

The model encodes, for a supported year (1..9999):

    four_field(year) = [ '0'+thousands, '0'+hundreds, '0'+tens, '0'+units ]

as ASCII code points, always length 4, leading zeros retained. The real
operation is Python's `'%04d' % year`, which is exactly what `DateFormat.Y`
returns after the patch. We assert equality over every supported year (an
exhaustive sweep of 1..9999) plus explicit boundary witnesses, comparing on
code points so the comparison is byte-for-byte.

Imports nothing repo-specific: `'%04d' % n` is a Python built-in formatting
operation — the same operation the gold patch calls. Exit 0 iff every
observation matches the deep model.
"""
import sys

# --- model.py deep-model reference encoding (kept in lock-step) --------------


def four_field(year):
    """Reference of model.py's deep model `four_field` as a list of ASCII code
    points: the place-value digits thousands/hundreds/tens/units, MS first,
    always four code points with leading zeros retained."""
    thousands = year // 1000
    hundreds = (year // 100) % 10
    tens = (year // 10) % 10
    units = year % 10
    return [48 + thousands, 48 + hundreds, 48 + tens, 48 + units]


def check_year(year):
    """Assert the deep model four_field(year) == the REAL '%04d' % year."""
    observed = [ord(ch) for ch in ('%04d' % year)]   # real operation (the patch)
    expected = four_field(year)                       # deep model
    assert observed == expected, (
        "four_field deep model unsound on year %d: '%%04d' gave %r, "
        "deep model gives %r" % (year, observed, expected))


def main():
    # Explicit boundary witnesses the F2P test pins:
    #   datetime(1, 1, 1)   -> 'Y' == '0001'
    #   datetime(999, 1, 1) -> 'Y' == '0999'
    for year, want in [(1, "0001"), (999, "0999"), (476, "0476"),
                       (42, "0042"), (4, "0004"), (1000, "1000"),
                       (1999, "1999"), (9999, "9999"), (10, "0010"),
                       (100, "0100")]:
        rendered = "%04d" % year
        assert rendered == want, (
            "real rendering wrong on year %d: got %r want %r"
            % (year, rendered, want))
        check_year(year)

    # Exhaustive sweep of the full supported datetime year range.
    for year in range(1, 10000):
        check_year(year)

    print("G-AX OK: four_field deep model (== '%04d' rendering) sound on all "
          "9999 supported years + 10 boundary witnesses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
