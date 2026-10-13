#!/usr/bin/env python3
"""G-AX skip stub for django__django-16560.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. Each modeled behavior (the validation-error code, the equality
including the code, and the reconstruction-data surfacing of the code) is a pure
total computation over the constraint's own data: the optional code, the
pre-existing comparison key (compared unchanged), and a boolean recording whether
the constraint's own unchanged detection found a violation. The unchanged
violation-detection and message handling are abstracted (not axiomatized), so
there is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean for
G-AX to validate. All three behaviors are differential-tested against the real
patched constraint methods by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-16560",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "three modeled behaviors (validation-error code, equality with "
                  "code, reconstruction-data code) are pure total computations "
                  "over the constraint's own data, validated by G-CONF against the "
                  "real patched constraint methods.",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
