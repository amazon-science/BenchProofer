#!/usr/bin/env python3
"""G-AX skip stub for django__django-13109.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. The modeled function (`ForeignKey.validate`) is modeled DEEPLY: the
behavior the patch changes — which base collection the existence query starts
from — is the choice between scanning the underlying stored collection (full
`rows`) and scanning the default-presentation view (`rows.filter
(.defaultVisible)`). That choice plus the key/eligibility membership test is
spelled out as list transformations over the modeled `Row` records, so no opaque
callee's property is consumed by the correctness proof, and there is no
callee-property contract for G-AX to validate.

The full R/I impl is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13109",
        "reason": "no consumed callee axiom and no A-reference; the changed "
                  "manager-selection decision is modeled deeply as a list "
                  "transformation over per-record observables; behavior "
                  "validated by G-CONF",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
