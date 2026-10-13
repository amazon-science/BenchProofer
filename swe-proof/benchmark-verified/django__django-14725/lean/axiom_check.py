#!/usr/bin/env python3
"""G-AX — no consumed callee axiom for this instance.

The proof of `correct_saveFormset` discharges the branch selection directly and
consumes NO `axiom <callee>_prop` (the axioms region is empty). The function's
two collaborators (`save_existing_objects` / `save_new_objects`) are UNCHANGED
and enter the model only as their returned lists (R-tagged inputs), not as
axiomatized properties. There is therefore nothing for G-AX to validate.

stdlib-only. Emits a skip status and exits 0.
"""
import sys


def main() -> int:
    print("G-AX SKIP: no consumed callee axiom (axioms region empty; "
          "callees modeled as R-tagged input lists)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
