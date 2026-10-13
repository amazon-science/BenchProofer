#!/usr/bin/env python3
"""G-AX for django__django-15380 — skip stub.

The bundle consumes NO callee axiom and declares NO A-reference deep model:
the axioms region of Solution.lean is empty. The three map operations in the
modeled function (the rename-map translation and the two snapshot indexings) are
Python `dict.get` / `dict.__getitem__` builtins, reproduced concretely as total
`List.lookup`/`.getD` (I-tagged in refinement.md), not abstracted behind any
axiomatized callee property. The downstream `get_field`/rename-scan callees are
unchanged by the fix and out of model scope.

There is therefore no callee contract for G-AX to validate against the real
repo callee; the behavioral conformance that matters (the R/I shadow vs the
patched loop body) is exercised by conformance_check.py (G-CONF).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15380",
    "reason": "no consumed axiom and no A-reference deep model (axioms region "
              "empty; the map operations are reproduced concretely as I-tagged "
              "List.lookup/.getD)",
}))
sys.exit(0)
