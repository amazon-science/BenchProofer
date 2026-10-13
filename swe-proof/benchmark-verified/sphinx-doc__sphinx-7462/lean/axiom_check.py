#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-7462 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
only collaborator the modeled functions call but do not change is the recursive
per-element renderer (`unparse(elem)`); it is represented by leaving the
already-rendered elements as arbitrary inputs (`elems`), universally quantified
in both `correct_*` theorems, so the contract holds for every per-element
rendering and needs no executable-checked property. The behavior the patch
changes — special-casing the empty sequence so it renders as the literal
parentheses pair (display) / "()" (text) instead of popping an empty list /
joining to the empty string — is modeled DEEPLY over the observable element
inputs. SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op, so there
is no callee contract to validate against the real repo. The R/I legs are
validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-7462",
    "reason": "no consumed callee axiom and no A-reference; the per-element "
              "renderer is universally quantified and the changed assembly op "
              "is modeled deeply (R/I, validated by G-CONF)",
}))
sys.exit(0)
