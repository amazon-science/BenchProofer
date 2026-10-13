#!/usr/bin/env python3
"""G-AX skip stub for django__django-16569.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`BaseFormSet.add_fields`, deletion branch)
makes a pure boolean decision over `(can_delete, can_delete_extra, index,
initial_form_count)` — whether to attach the deletion field — and the only
non-trivial sub-expression is the optional-position guard, which is modeled
DEEPLY as `withinInitial` (no axiom). The field-construction side effect is
abstracted to a boolean and is not modeled or axiomatized. There is no `opaque`
callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing for
G-AX to validate. The decision (and its positionless boundary) is
differential-tested against the real patched `add_fields` by conformance_check.py
(G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-16569",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "deletion-field decision is pure boolean logic with the "
                  "optional-position guard modeled deeply as withinInitial, so "
                  "the impl is all R/I (validated by G-CONF against the real "
                  "BaseFormSet.add_fields).",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
