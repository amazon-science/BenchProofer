#!/usr/bin/env python
"""G-AX for django__django-14373 — SKIP STUB.

The bundle declares NO callee axioms: the modeled behavior (`DateFormat.Y`'s
rendering of the year as a leading-zero-padded, minimum-width-4 decimal numeral)
is modeled DEEPLY with concrete Lean operations — `toString` for the base-ten
numeral and `padZeros 4` for the `'%04d'` left-padding. The rendering IS the
operation the fix introduces, so it is modeled, not axiomatized; there is no
`axiom <callee>_prop` for the proof to consume.

(The deep model IS validated against the real patched `Y()` rendering by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
