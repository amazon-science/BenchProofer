#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-25332 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled transforms (`serialize` / `deserialize`) are all R/I (validated by
G-CONF). A reference and the act of following it (`r()`) or creating it
(`weakref.ref(x)`) are modeled DEEPLY as the `Ref` structure (`Ref.val` /
`Ref.mk`), not as an axiomatized repo callee. There is therefore no callee
contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-25332",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
