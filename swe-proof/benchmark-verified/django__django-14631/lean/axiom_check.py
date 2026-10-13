#!/usr/bin/env python
"""G-AX skip stub for django__django-14631.

No consumed callee axiom is declared in the bundle (the `axioms` region is
empty). The two external operations the changed code invokes per field —
obtaining the field's preset initial value (`get_initial_for_field`) and the
submitted value (`bf.data` / `_widget_data_value`) — are UNCHANGED by the patch,
and their results are taken as the model inputs `rawInitial` and `data`. The
changed op itself, presenting a field's initial value at its widget's precision
(`BoundField.initial`'s microsecond-stripping), is modeled DEEPLY in Lean
(`boundInitial`, an A-reference row) and validated against the real per-field
behavior by the differential `conformance_check.py` (G-CONF), not by an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (initial presentation modeled "
          "deeply as boundInitial; validated by G-CONF as A-reference)")
    sys.exit(0)
