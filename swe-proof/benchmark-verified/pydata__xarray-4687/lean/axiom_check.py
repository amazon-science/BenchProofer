#!/usr/bin/env python
"""G-AX skip stub for pydata__xarray-4687.

No consumed callee `_prop` axiom is declared in the bundle. The single opaque
callee, `getKeepAttrsDefault` (the ambient attribute-retention default,
`_get_keep_attrs(default=False)`), is invoked identically by both the spec
(`keptAttrs`) and the implementation, so the correctness proof consumes no
contract about its value — it is an A-reference whose value-relation is exercised
by the differential `conformance_check.py` (G-CONF), not by an axiom. Likewise
the elementwise selection (`duck_array_ops.where`) is modeled deeply.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (keep_attrs default policy and "
          "elementwise selection modeled as A-references; validated by G-CONF)")
    sys.exit(0)
