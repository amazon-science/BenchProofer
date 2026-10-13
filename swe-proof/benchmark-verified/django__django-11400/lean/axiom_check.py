#!/usr/bin/env python
"""G-AX skip stub for django__django-11400.

No `axiom <callee>_prop` is consumed by either correctness proof. The single
`opaque` declaration, `applyOrdering` (the record re-sequencing primitive,
i.e. `QuerySet.order_by`), is an **I-tagged identical op**: the proofs only
ECHO its result (in the non-empty-directive branch) and never assert any
property of it. The fix being verified is purely the CONTROL FLOW — apply the
primitive iff the directive is non-empty — which `correct_orderedChoices`
discharges without any axiom about `applyOrdering`. The empty-directive branch
never invokes it at all.

Therefore there is no callee contract to validate against the real callee; the
re-sequencing primitive's behavior is exercised end-to-end by G-CONF (which uses
the REAL `order_by`). This stub reports `status=skip` and exits 0.
"""
import sys


def main():
    print("status=skip no consumed callee axioms "
          "(applyOrdering is an I-tagged echo, validated end-to-end by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
