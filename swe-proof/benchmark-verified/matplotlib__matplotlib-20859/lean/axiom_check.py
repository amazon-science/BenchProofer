#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-20859 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled decision (`resolveLegendParent`) is all R (validated by G-CONF). The
parent's runtime kind, its own object identity, and the identity of the canvas an
axes belongs to all enter as plain data; the two `isinstance` tests are modeled
deeply as the kind predicates `isAxesKind` / `isCanvasKind`. There is therefore
no callee contract to validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-20859",
    "reason": "no consumed callee axiom and no A-reference; impl is all R "
              "(validated by G-CONF)",
}))
sys.exit(0)
