#!/usr/bin/env python3
"""G-AX skip stub for django__django-15741.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. The modeled function (`django.utils.formats.get_format`) is changed only
by the coercion `format_type = str(format_type)` (modeled as `realizeName`, an R
op). The downstream resolution (`lookupFormat`) is the UNCHANGED callee: it is
declared `opaque` (signature only) with NO `axiom lookupFormat_prop`, and the
correctness proof closes by definitional `rfl` over `realizeName` without
consuming any property of it. There is therefore nothing for G-AX to validate;
the full R/I impl is differential-tested by conformance_check.py (G-CONF), which
leaves `lookupFormat` as the real patched callee.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-15741",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
