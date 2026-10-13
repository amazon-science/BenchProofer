#!/usr/bin/env python
"""G-AX skip stub for django__django-11433.

No consumed callee axiom is declared in the bundle. Every per-field predicate the
modeled routine consults — editability, the auto-key test, availability of a
resolved value, presence of a model default, whether the value was omitted from
the submitted payload, whether the resolved value is an empty sentinel, and the
file-field test — is an UNCHANGED callee whose result is supplied as a boolean
field of the per-field input record. The patch changes only how those predicates
are combined in the "leave the field at its default" guard (it adds a third
conjunct), which is modeled DEEPLY in Lean (`assignField` /
`problem_spec_bindFields`, A-reference rows) and validated against the real
per-field decision by the differential `conformance_check.py` (G-CONF), not by an
axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (assignment-selection guard "
          "modeled deeply; validated by G-CONF as A-reference)")
    sys.exit(0)
