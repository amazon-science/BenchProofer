#!/usr/bin/env python3
"""G-AX skip stub for django__django-11138.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used: the modeled function (mysql `_convert_field_to_tz`) reads the time-zone
flag and the source / target time-zone names as plain data and assembles a SQL
string by `%`-formatting, which is modeled directly in Lean as string
concatenation (`convertTzFragment`, an I op — see refinement.md). There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is
nothing for G-AX to validate. The full R/I impl is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11138",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
