#!/usr/bin/env python3
"""G-AX for pytest-dev__pytest-6202 — skip stub.

The bundle consumes NO unchanged-callee axiom. The modeled routine
(`getmodpath`'s result-assembly tail) is built entirely from standard
string/list operations — `list.reverse` and `str.join` (post-patch), plus
`str.replace` in the pre-patch variant — each modeled CONCRETELY by its exact
Lean counterpart (`List.reverse`, `String.intercalate`, `String.replace`). The
`axioms` region of Solution.lean is empty; the `proof` region of
`correct_getmodpath` consumes no `axiom … _prop`. There is therefore no callee
contract to validate against the real repo. The R/I legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "pytest-dev__pytest-6202",
    "reason": "no consumed callee axiom; the modeled tail uses only standard "
              "string/list ops modeled concretely (validated by G-CONF)",
}))
sys.exit(0)
