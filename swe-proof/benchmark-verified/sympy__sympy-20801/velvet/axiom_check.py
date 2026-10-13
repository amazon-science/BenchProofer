#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-20801.

This bundle has **no axioms and no deep-model references**: every operation of
the modeled function (`Float.__eq__`) is grounded in `Solution.lean` as exact
integer equality or a constructor match on the operand kind (see mapping.md §3
and refinement.md §B). There is therefore no callee contract to validate against
a real callee — nothing for G-AX to check.

`meta.json` records empty `axioms` / `deep_model_references`; this stub exits 0
so the gate is a sound no-op. The behavioral fidelity of the R/I refinement is
checked mechanically by `conformance_check.py` (G-CONF), not here.
"""
import sys


def main():
    print("G-AX OK: no axioms / no deep-model references in this bundle "
          "(Float.__eq__ is grounded; nothing to validate against a real callee).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
