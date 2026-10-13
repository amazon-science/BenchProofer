#!/usr/bin/env python3
"""G-AX skip stub for django__django-13741.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior — constructing the read-only field from an
optional `disabled` setting (applying the default when none is supplied) and the
resulting change decision (disabled => never changed; otherwise initial vs
submitted with missing values treated as the empty string) — is spelled out
DIRECTLY in `implementation_passwordHashField`. There is no `opaque` callee and
no `axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The construction + decision (and its binding to the REAL patched
`ReadOnlyPasswordHashField`) is differential-tested by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13741",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "field construction (defaulted disabled setting) and the change "
                  "decision are modeled deeply, so the impl is all R/I/A-reference "
                  "(validated by G-CONF against the real patched field).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
