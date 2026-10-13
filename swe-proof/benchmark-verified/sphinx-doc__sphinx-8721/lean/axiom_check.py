#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-8721 — skip stub.

The modeled change is a pure control-flow decision over three inputs
(hasModules, builderName, enableEpub). The unchanged downstream page-construction
work is universally quantified in the spec (the arbitrary `generatedPages` list),
so the proof consumes NO property of any callee. There is no `opaque`/`axiom`
callee contract in Solution.lean and no axiomatized A-reference. Hence G-AX has
nothing to validate.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-8721",
    "reason": "no consumed callee axiom and no axiomatized A-reference; the "
              "modeled change is a control-flow decision over three input flags "
              "and the downstream page-construction work is universally "
              "quantified, so the impl is all R/I (validated by G-CONF against "
              "the real post-patch control flow)",
}))
sys.exit(0)
