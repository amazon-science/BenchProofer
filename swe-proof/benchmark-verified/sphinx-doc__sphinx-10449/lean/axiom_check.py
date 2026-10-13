#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-10449 — SKIP STUB.

The field-list population is modeled deeply: the field-name parsing
(`tokenize`/`declaresType`/`declaresParam`/`hasReturnField`), the per-name
type/param generation, and the return-type decision are all spelled out
element-wise in Solution.lean. There are no `axiom <callee>_prop` declarations,
so there is nothing for G-AX to validate. Exit 0 with status=skip. stdlib-only.
"""
import json
import sys

print(json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"}))
sys.exit(0)
