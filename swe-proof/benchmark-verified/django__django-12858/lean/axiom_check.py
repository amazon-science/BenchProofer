#!/usr/bin/env python3
"""G-AX skip stub for django__django-12858.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the per-entry `models.E015` report decision
of `Model._check_ordering`'s relation-field walk) is pinned over arbitrary model
machinery: the segment-resolution, relation test, related-model descent, and the
transform/lookup membership tests are all universally-quantified function
parameters in Solution.lean (`getField`, `isRelation`, `descend`, `hasTransform`,
`hasLookup`). The spec/proof hold for EVERY such machinery, so the proof consumes
no property of any of them. There is no `opaque` callee and no `axiom
<callee>_prop` in Solution.lean, so there is nothing for G-AX to validate. The
binding of these parameters to the REAL Django model machinery is differential-
tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12858",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "model machinery (getField/isRelation/descend/hasTransform/"
                  "hasLookup) is universally quantified, so the impl is all "
                  "R/I/A-reference (validated by G-CONF against the real Django "
                  "_check_ordering walk over a synthetic model graph)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
