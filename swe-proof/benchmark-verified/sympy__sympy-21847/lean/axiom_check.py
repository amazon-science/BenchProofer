#!/usr/bin/env python
"""G-AX: callee-axiom soundness for sympy__sympy-21847.

SKIP STUB. The proof of `correct_selectMonomials` consumes NO callee axiom: the
modeled change is the per-candidate acceptance predicate, modeled DIRECTLY as
`minDegree <= powers.sum` (total degree of the exponent vector). There is no
`opaque` callee and no `axiom … _prop` — `sum`/`max` over the per-variable
exponent counts are modeled by `List.sum` / `List.foldr Nat.max 0`. The R/I
selection logic is validated end-to-end by G-CONF (conformance_check.py).

Exit 0 with status=skip.
"""
import sys


def main():
    print("status=skip no consumed callee axioms "
          "(acceptance predicate modeled directly; validated by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
