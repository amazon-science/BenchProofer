#!/usr/bin/env python3
r"""G-AX for matplotlib__matplotlib-25479.

Neither `correct_colormapEq` nor `correct_register` consumes a `_prop` axiom.

* `implementation_colormapEq` equals `(a.flag == b.flag) && (a.table == b.table)`
  purely structurally — no UNCHANGED callee's behaviour is assumed. The lookup
  table comparison is modeled deeply as `List Int` equality (an R/I concern,
  exercised by conformance_check.py against `np.array_equal`), not axiomatized.

* `implementation_register` sets the stored copy's display name to the
  registration name. `cmap.copy()` is modeled as a structural identity on the
  modeled fields (an R refinement), again validated differentially by G-CONF,
  not via a Lean `_prop` axiom.

There is therefore NO consumed callee axiom for G-AX to validate. This gate is a
principled skip stub (cf. django__django-11099: no consumed axiom => G-AX skip).

stdlib-only; exit 0.
"""
import json
import sys

report = {
    "status": "skip",
    "instance": "matplotlib__matplotlib-25479",
    "reason": (
        "no consumed callee axiom: correct_colormapEq proves the result equals "
        "(flag-equality && table-equality) structurally, and correct_register "
        "proves the stored copy reports the registration name; the copy and the "
        "lookup-table comparison are R/I refinements validated by "
        "conformance_check.py (G-CONF), not by a Lean _prop axiom"
    ),
}
print(json.dumps(report))
sys.exit(0)
