#!/usr/bin/env python3
"""G-AX — django__django-10097.

The bundle consumes NO callee axiom and declares NO A-reference: the fix is a
regex character-class change, modeled deeply as the pure predicate
`urlUserinfoValid` over the segment's characters (refinement.md — all rows R/I).
There is no unchanged repo callee whose contract the proof relies on. G-AX is
therefore a skip.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-10097",
        "reason": "no consumed callee axiom and no A-reference; the changed "
                  "regex group is modeled deeply and its R/I legs are validated "
                  "by G-CONF",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
