#!/usr/bin/env python3
"""G-AX skip stub for matplotlib__matplotlib-26342.

No consumed callee axiom is declared in the bundle and no deep-model
A-reference is used: installing the replacement path list is two direct field
updates (`self._paths = paths`, `self.stale = True`), modeled directly in Lean.
There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so
there is nothing for G-AX to validate. The full R/I impl is differential-tested
by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "matplotlib__matplotlib-26342",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
