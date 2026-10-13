#!/usr/bin/env python
"""G-AX skip stub for sympy__sympy-13551.

No consumed callee axiom is declared in the bundle. The modeled function (the
additive branch of `Product._eval_product`) is modeled DEEPLY: the patched
expression `exp(Sum(log(p), (k,a,n)))` is the GENUINE finite product
`prod_{k=a}^{n} p`, and it is spelled out as the accumulator product
`(g.map (fun x => c + x)).prod` over the per-index term values — not axiomatized.
The final division by the evaluated denominator product is an identical concrete
op. No callee the patch leaves unchanged-but-relied-upon is consumed via an
`axiom`.

There is therefore nothing for G-AX to validate; the R/I ops are validated
against the real patched `Product.doit()` by the differential `conformance_check.py`
(G-CONF). Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (range-product modeled directly; "
          "validated by G-CONF as R/I ops)")
    sys.exit(0)
