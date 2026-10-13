#!/usr/bin/env python3
"""G-AX for django__django-12143 — SKIP STUB.

The matching decision is modeled DEEPLY (`matchesRowKey`: literal-prefix +
non-empty digit run + trailing field name, spelled out character-for-character
over the input key). The unchanged callees whose composite effect it captures
(the `re` engine plus `re.escape`) are A-REFERENCE, validated == the real
behavior by `conformance_check.py` (G-CONF), NOT consumed as an axiom. There are
no `axiom <callee>_prop` declarations in Solution.lean, so there is nothing for
G-AX to validate. Exit 0 with status=skip. stdlib-only.
"""
import json
import sys

print(json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"}))
sys.exit(0)
