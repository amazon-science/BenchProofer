#!/usr/bin/env python3
"""G-AX skip stub for django__django-13516.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled method (`OutputWrapper.flush`) tests whether the
underlying stream supports flushing and, when it does, invokes that stream's
flush once. Both operations are modeled structurally over the stream's
observables (its flush-support flag and its flush-invocation count) in
Solution.lean — there is no `opaque` callee and no `axiom <callee>_prop`, so
there is nothing for G-AX to validate. The flag-test + invocation-count behavior
is differential-tested against the REAL patched method by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13516",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "flush-support test and the underlying-stream flush invocation "
                  "are modeled structurally (impl region is all R/I), validated "
                  "by G-CONF against the real OutputWrapper.flush",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
