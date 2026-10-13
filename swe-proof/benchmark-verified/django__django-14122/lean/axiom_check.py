#!/usr/bin/env python3
"""G-AX for django__django-14122 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled function (`getGroupBy`) is all R/I (validated by G-CONF). The columns
each selected / ordering / filter expression contributes to the grouping
(`expr.get_group_by_cols()`), and the per-entry "already covered by reference" /
"references the selected columns" decisions, all enter as plain data; the
accumulation and the implicit-default-ordering gate are modeled deeply. There is
therefore no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-14122",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
