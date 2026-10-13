#!/usr/bin/env python3
"""G-AX skip stub for django__django-11211.

No consumed callee axiom is declared in the bundle, and no deep-model A-reference
is axiomatized. The modeled function (`UUIDField.get_prep_value`, post-patch) is
modeled DEEPLY: its two callees — the base pass-through `Field.get_prep_value`
and the text->identifier conversion `UUIDField.to_python` — are spelled out as the
pure functions `basePrep` (identity) and `canonicalValue` (decode the identifier's
hex digits) in Solution.lean. There is no `opaque` callee and no
`axiom <callee>_prop`, so there is nothing for G-AX to validate. The faithfulness
of the deep models to the REAL callees is differential-tested by
conformance_check.py (G-CONF) against the real patched `UUIDField.get_prep_value`.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11211",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "base pass-through and the text->identifier conversion are "
                  "modeled deeply (basePrep / canonicalValue) and validated by "
                  "G-CONF against the real patched UUIDField.get_prep_value",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
