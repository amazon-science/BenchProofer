#!/usr/bin/env python
"""G-AX skip stub for django__django-14351.

No consumed callee axiom is declared in the bundle. The two operations the fix
performs on an implicitly-selected nested right-hand side — discarding its
implicit selection and then reducing it to its single identity column — are
modeled DEEPLY in Lean (`normalizeRhs` / the field updates in
`implementation_membershipGroupColumns`, an A-reference) and validated against
the real callee `In.get_group_by_cols` (together with the faithful `Query`-state
collaborators) by the differential `conformance_check.py` (G-CONF), not by an
axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (rhs selection normalization "
          "modeled deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
