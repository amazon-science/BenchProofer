#!/usr/bin/env python
"""G-AX for django__django-15022 — SKIP STUB.

The bundle declares NO callee axioms: the changed behaviour (the quantifier
structure of the multi-word search-term filtering in
`ModelAdmin.get_search_results`) is modeled DEEPLY with concrete Lean operations
over the per-(related-row, word) match matrix (`List.filter` of `rows.any` of
`terms.all`). There is no `axiom <callee>_prop` for the proof to consume.

The unchanged helpers folded into the inputs (`smart_split`,
`unescape_string_literal`, `construct_search`, the per-row OR-of-lookups match
test) are not consumed axioms and not reference callees: the modeled value
(which records survive) depends only on the per-(row, word) match matrix they
produce, which is supplied as input.

(The deep model IS validated against the real patched `get_search_results` by
G-CONF / conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
