#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-15599.

No consumed callee axiom is declared in the bundle. The modeled function is the
`non_mod_l` reduction loop of `Mod.eval`'s `Mul` branch; its only non-trivial op
is the per-factor residue `i % q`, which is modeled DEEPLY in Lean as
`intMod n q := n - q * Int.fdiv n q` (the Python floored remainder). The
integer-ness test `i.is_Integer` is modeled directly by the `Factor` constructor.

Neither is a callee whose contract the proof must ASSUME — the residue arithmetic
is a concrete R op validated against the real patched logic (sympy
`Integer.__mod__` and the `is not S.Zero` test) by the differential
`conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (per-factor residue modeled "
          "directly via floored intMod; validated by G-CONF as an R op)")
    sys.exit(0)
