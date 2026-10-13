#!/usr/bin/env python3
"""G-AX skip stub for django__django-17029.

No consumed callee axiom is declared in the bundle and no deep-model
A-reference is used: the registry's two memoized result caches and its readiness
flag enter as plain data (entry lists + a boolean), and the only operations
performed are discarding the memoized entries (modeled directly as emptying the
lists) and a readiness-gated metadata refresh that is the identity on the modeled
carrier. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The full R/I impl is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-17029",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
