#!/usr/bin/env python3
"""G-AX skip stub for django__django-14792.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used: the modeled function (`_get_timezone_name`) reads two observables off
the time-zone object — its short self-reported label (`timezone.tzname(None)`)
and its full textual form (`str(timezone)`) — as plain data (`Option String` /
`String`) and chooses between them by truthiness, modeled directly in Lean as a
`match` plus a non-empty test (all R/I — see refinement.md). There is no `opaque`
callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing for
G-AX to validate. The full R/I impl is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14792",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
