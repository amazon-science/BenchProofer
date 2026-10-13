#!/usr/bin/env python3
"""G-AX skip stub for django__django-16661.

The bundle models ONE function, `ModelAdmin.lookup_allowed`
(`django/contrib/admin/options.py`). It declares NO `opaque` callee and NO
`axiom <callee>_prop` in Solution.lean.

The behavior the patch changes — which lookup components count as genuine
relational hops (`relation_parts`) — is modeled DEEPLY (`continuesLocal` /
`stepFold` in the `pure` region), never axiomatized (SPEC_GUIDE §3, §0.7). The
field-metadata reads the walk performs at each component (`get_field` success,
`field.is_relation`, `field.path_infos`, `model._meta.parents.values()`,
`model._meta.auto_field`, `prev_field.to_fields`) are pure metadata lookups
whose OUTCOMES are abstracted into the input `PathStep` record (a structure
restricted to the touched fields, mapping.md) and supplied as data — they
contribute no property the proof consumes.

Since there is no consumed callee axiom and no axiomatized A-reference, there is
nothing for G-AX to validate. The R/I impl (and its binding to the real patched
control flow) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-16661",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "relation-part-counting decision is modeled deeply "
                  "(continuesLocal / stepFold) and the field-metadata reads are "
                  "abstracted into the PathStep inputs, so the impl is all R/I "
                  "(validated by G-CONF against the real patched lookup_allowed)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
