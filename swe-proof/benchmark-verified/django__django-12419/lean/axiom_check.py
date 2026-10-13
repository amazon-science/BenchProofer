#!/usr/bin/env python3
"""G-AX skip stub for django__django-12419.

No consumed callee axiom is declared in the bundle and no deep-model
A-reference is used: the project-supplied configuration and the framework's
built-in default both enter as plain data (modeled as `Option`), and the only
operation performed is the most-specific-wins selection, modeled directly in
Lean. There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean,
so there is nothing for G-AX to validate. The full R/I impl is differential-
tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12419",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
