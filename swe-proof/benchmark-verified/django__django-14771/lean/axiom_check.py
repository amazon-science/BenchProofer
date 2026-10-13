#!/usr/bin/env python3
r"""G-AX skip stub for django__django-14771.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (building the auto-reloader's relaunch
argument vector) is spelled out deeply: rendering a warning option as `-W<o>` and
an interpreter option as `-X<key>` / `-X<key>=<value>` are the concrete pure
helpers `warnArg` / `xoptArg` in Solution.lean, and the executable head, the
CPython gate, and the original-argv tail are plain list construction. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing
for G-AX to validate. The impl (and its binding to the REAL patched
`get_child_arguments`) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14771",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "token rendering is spelled out deeply as warnArg/xoptArg and the "
                  "rest of the vector is plain list construction, so the impl is "
                  "all R/I (validated by G-CONF against the real patched "
                  "get_child_arguments)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
