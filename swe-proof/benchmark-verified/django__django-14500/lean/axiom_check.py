#!/usr/bin/env python3
"""G-AX — skip stub for django__django-14500.

The proof of `correct_unapplyMigration` consumes NO callee axiom (the axioms
region of Solution.lean is empty) and there is no A-reference deep model: the
changed operation is pure control flow that decides WHICH migration identifiers
are recorded as no-longer-applied, and in what order. The only callee on the
recording path, `recorder.record_unapplied`, is an UNCHANGED, order-independent
sink that is framed out (mapping.md), not axiomatized.

Therefore there is no callee contract to validate against the real callee.
Exit 0 with status=skip.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed axiom / no A-reference deep model "
          "(axioms region empty); nothing to validate (django__django-14500)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
