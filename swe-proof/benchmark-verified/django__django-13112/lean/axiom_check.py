#!/usr/bin/env python3
r"""G-AX skip stub for django__django-13112.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the normalized `kwargs['to']` value of
`ForeignKey.deconstruct` for a string lazy reference) is spelled out deeply: the
`str.split('.')` is the concrete pair of pure helpers `prefixSeg`/`nameSeg`, and
the `str.lower()` is per-character `Char.toLower` in Solution.lean. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is
nothing for G-AX to validate. The normalization impl (and its binding to the REAL
`str.lower` and the live patched `ForeignKey.deconstruct`) is differential-tested
by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13112",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "string split is spelled out deeply as prefixSeg/nameSeg and "
                  "the per-character lowercasing as Char.toLower, so the impl is "
                  "all R/I/A-reference (validated by G-CONF against the real "
                  "patched ForeignKey.deconstruct `to` value)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
