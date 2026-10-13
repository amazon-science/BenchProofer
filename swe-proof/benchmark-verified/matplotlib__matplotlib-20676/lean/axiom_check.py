#!/usr/bin/env python3
"""G-AX for matplotlib__matplotlib-20676 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
behavior the patch changes (which coordinate pair becomes the initial boundary
marker positions) is modeled DEEPLY as a pure selection on the selection
direction between the axis' horizontal and vertical view bounds. SPEC_GUIDE §3
forbids axiomatizing a deeply-modeled changed decision, so there is no callee
contract to validate against the real repo. The marker container is an identity
pass-through (an `I` refinement), and the view-bound accessors enter as grounded
inputs. The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "matplotlib__matplotlib-20676",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
