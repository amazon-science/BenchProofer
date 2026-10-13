#!/usr/bin/env python3
"""G-AX for pydata__xarray-7229 — skip stub.

The bundle consumes NO callee `_prop` axiom. The single opaque callee
`select_combine` models the unchanged combination `apply_ufunc(duck_array_ops.where,
…)`; it is an A-reference (deep-model reference), byte-identical on the pre- and
post-patch legs, and the proof asserts no property about it. There is therefore no
real-callee property to validate in-container. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "gate": "G-AX",
    "status": "skip",
    "reason": "no consumed callee axiom; select_combine is an A-reference "
              "(unchanged apply_ufunc combine, identical on both legs)",
}))
sys.exit(0)
