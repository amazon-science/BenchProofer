#!/usr/bin/env python3
"""G-AX for django__django-13401 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
three modeled methods (field equality, ordering, hash key) are all R/I over the
`FieldId` carrier (validated by G-CONF). They read only the field's own
`creation_counter` and `(app_label, model_name)` model identity and compare them
with total operations; no unchanged repo callee is axiomatized. There is therefore
no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13401",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
