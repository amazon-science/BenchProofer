#!/usr/bin/env python3
"""G-AX skip stub for django__django-15695.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. Whether migration is permitted, the starting index, the target index,
and the target name are all resolved upstream and enter the modeled decision as
plain data; the only operation modeled is the decision of which index relabel to
emit (if any), spelled out directly in Lean. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The full R/I impl is differential-tested by conformance_check.py (G-CONF) against
the real patched operation.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-15695",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
