#!/usr/bin/env python3
"""G-AX skip stub for django__django-12965.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`SQLDeleteCompiler.single_alias`) decides
whether a deletion targets exactly one table. The one unchanged callee the fix
newly invokes (`Query.get_initial_alias`) is modeled DEEPLY as the concrete pure
helper `includePrimary` in Solution.lean (the proof unfolds it; it consumes no
opaque-callee property), and that deep model is validated == the real callee by
conformance_check.py (G-CONF). There is no `opaque` callee and no `axiom
<callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12965",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "unchanged get_initial_alias callee is modeled deeply as the "
                  "concrete helper includePrimary (validated == the real callee "
                  "by G-CONF), so the impl is all R/I/A-reference",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
