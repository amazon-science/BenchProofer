#!/usr/bin/env python
"""G-AX skip stub for django__django-14170.

No consumed callee axiom is declared in the bundle. The behavior the patch
introduces — selecting ISO-8601 week-numbering bounds instead of calendar bounds
when the year-type flag is set — is modeled DEEPLY in Lean: the Gregorian and ISO
calendar day-number computations are spelled out as arithmetic on the year
(`gregJan1` / `gregDec31` / `isoYearStart` in the `pure` region, A-references),
and validated against the real standard-library `datetime` calendar by the
differential `conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (calendar/ISO day-number "
          "computations modeled deeply; validated by G-CONF as A-references)")
    sys.exit(0)
