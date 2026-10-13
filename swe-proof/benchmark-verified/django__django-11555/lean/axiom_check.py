#!/usr/bin/env python3
"""G-AX for django__django-11555 — skip stub.

The modeled per-item dispatch consumes NO `_prop` axiom: the specification
`result = items.flatMap expandOrderingItem` is a pure structural concatenation,
and the loop↔flatMap equality is proved by list induction (`List.forIn_cons`),
consuming no behavioural property of the recursive resolver.

The only outside callee, `resolveFieldRef` (= the UNCHANGED recursive
`SQLCompiler.find_ordering_name` on a string item), is an **A-reference**: it
appears IDENTICALLY in the spec helper `expandOrderingItem` and in the
implementation, so it cancels in the correctness statement and no contract about
it is asserted or relied upon. Exercising the real callee would require
materialising a full Query/model join graph, and would validate nothing the
proof depends on.

Therefore there is no axiom property to validate against the real callee, and
this check reports `skip`.
"""
import json
import sys

print(json.dumps({"status": "skip",
                  "reason": "no consumed _prop axiom; sole callee is an "
                            "A-reference that cancels in the statement"}))
sys.exit(0)
