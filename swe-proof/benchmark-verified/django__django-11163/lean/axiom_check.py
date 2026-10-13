#!/usr/bin/env python3
"""G-AX skip stub for django__django-11163.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (`model_to_dict`) reads only a field's name,
its editable flag, and its extracted value. The extracted value
(`f.value_from_object(instance)`) is unchanged by the modeled behavior and is not
constrained by the spec beyond "it is this field's value"; it is carried as the
given attribute `FieldRec.val` (a type refinement, R), NOT axiomatized. There is
no `opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is
nothing for G-AX to validate. The whole impl is R/I and is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11163",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "field's extracted value is carried as the FieldRec.val "
                  "attribute (R), so the impl is all R/I (validated by G-CONF "
                  "against the real patched model_to_dict)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
