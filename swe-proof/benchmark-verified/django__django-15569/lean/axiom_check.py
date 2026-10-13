#!/usr/bin/env python3
"""G-AX for django__django-15569.

No callee is consumed as an axiom and none is validated as an A-reference: the
fix's added operation (`_clear_cached_lookups`, memo invalidation) is modeled
DEEPLY in the Lean impl (`cache := none`), and the table edit (`del`) is modeled
deeply via `eraseKey`. See refinement.md (all rows R/I). Nothing to validate.
"""
import sys

if __name__ == "__main__":
    print("G-AX skip: no consumed axioms or A-reference callees for this bundle.")
    sys.exit(0)
