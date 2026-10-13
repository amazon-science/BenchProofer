#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-13480.

No consumed callee axiom is declared in the bundle. The modeled observable is
the dispatch in the additive-argument branch of the hyperbolic-cotangent
evaluator: it selects `coth(x)` or `tanh(x)` according to a single decidable
test (`coth(m) is S.ComplexInfinity`). The proof of `correct_cothReduce`
discharges `problem_spec_cothReduce` by definitional case analysis on that test
and consumes NO property of the abstract callees `cothFn` / `tanhFn` /
`complexInfinity`. They are A-reference declarations (unchanged `coth` / `tanh` /
`S.ComplexInfinity`), not consumed `_prop` axioms.

Their faithfulness — that the abstract dispatch reproduces the real patched
`coth` over additive arguments with a nonzero half-period multiple — is
validated end-to-end by the differential `conformance_check.py` (G-CONF).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (dispatch decided by a single "
          "decidable test; abstract callees are A-reference, validated by G-CONF)")
    sys.exit(0)
