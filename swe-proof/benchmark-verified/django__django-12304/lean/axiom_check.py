#!/usr/bin/env python3
"""G-AX for django__django-12304 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled constructor (`buildChoicesClass`) is all R/I (validated by G-CONF). The
member (value, label) entries enter as plain data, the value→label association is
that data carried through unchanged, the "do not invoke" flag is the literal
`True`, and the template engine's call decision is modeled deeply as the boolean
`callable and not do_not_call_in_templates and not alters_data`. There is
therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-12304",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
