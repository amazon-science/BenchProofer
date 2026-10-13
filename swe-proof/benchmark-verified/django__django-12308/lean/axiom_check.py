#!/usr/bin/env python
"""G-AX skip stub for django__django-12308.

No consumed callee axiom is declared in the bundle. The fix is a pure dispatch
change: it routes a present, non-empty JSON value through its JSON serializer
(`field.get_prep_value`) with a fall-back to the generic renderer
(`display_for_value`) on a `TypeError`. Both leaf operations are UNCHANGED by
the patch and are modeled as `opaque` callees that appear IDENTICALLY in
`problem_spec_displayForField` and in `implementation_displayForField`; the
correctness proof therefore consumes NO property of either (it is case analysis
on `isNull` / `truthy` / the serialization result). Their real behavior is
exercised on both legs of the differential by `conformance_check.py` (G-CONF) as
A-reference rows, not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (JSON serializer + generic "
          "renderer are unchanged callees, modeled opaquely and validated by "
          "G-CONF as A-reference)")
    sys.exit(0)
