#!/usr/bin/env python3
r"""G-AX skip stub for django__django-13512.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the JSON string-leaf rendering that the fix
flips from `ensure_ascii=True` to `ensure_ascii=False`) is spelled out deeply:
the per-character escape table is the concrete pure helper `escapeChar` in
Solution.lean (with the flag-sensitive case being the `else [c]` literal-output
branch for code points >= U+0080). There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The escape table (and its binding to the REAL `json.dumps(..., ensure_ascii=False)`
string-leaf rendering) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13512",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "JSON string escape table is spelled out deeply as escapeChar "
                  "(the ensure_ascii=False rendering), so the impl is all "
                  "R/I/A-reference (validated by G-CONF against the real "
                  "json.dumps(..., ensure_ascii=False) string serialization)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
