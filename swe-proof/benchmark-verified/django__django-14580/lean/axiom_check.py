#!/usr/bin/env python3
"""G-AX skip stub for django__django-14580.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized: the modeled function (`TypeSerializer.serialize`) is plain string
and collection manipulation over a small special-case table plus a
module/qualname fallback, modeled DEEPLY as `serializeSpec` in Solution.lean.
There is no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so
there is nothing for G-AX to validate. The full impl is R/I and is
differential-tested by conformance_check.py (G-CONF) against the real patched
`TypeSerializer.serialize`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14580",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "type-serialization logic is modeled deeply (serializeSpec) and "
                  "the impl is all R/I (validated by G-CONF against the real "
                  "patched TypeSerializer.serialize)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
