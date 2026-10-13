#!/usr/bin/env python3
"""G-AX soundness check for sympy__sympy-13551 — NOT APPLICABLE (skip).

This bundle has NO axioms and NO A-reference deep models of *unchanged* callees
(see mapping.md §3, refinement.md §C). The single operation the patch changes —
the value assigned to the numerator `p` in `Product._eval_product`'s additive
branch — is modeled DEEPLY by `prodOfSums`/`rowSum` in Solution.lean; it does not
introduce any unchanged repo callee whose contract the proof assumes. `exp`,
`log`, `Sum` are not axiomatized: their net effect on a concrete integer range
is exactly the iterated product `prodOfSums` computes, and conformance_check.py
(G-CONF) anchors that equivalence to the literal patch text by a sympy
symbolic-identity cross-check.

Therefore G-AX is vacuous for this instance. Per the worker spec, this stub
emits status=skip and exits 0.
"""
import json
import sys


def main():
    print(json.dumps({
        "status": "skip",
        "reason": "no axioms / no A-reference callees; the changed op is modeled "
                  "deeply (prodOfSums). Fidelity is covered by G-CONF; G-AX N/A.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
