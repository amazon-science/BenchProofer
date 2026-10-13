#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-10466 — SKIP STUB.

The modeled computation (`Catalog.__iter__`'s `positions = sorted(set(...))`,
sphinx/builders/gettext.py:60) consumes NO unchanged repo callee as an axiom.
Every operation (project triple -> (source,line), dedup, lexicographic sort) is
a Python builtin modeled deeply in Lean (List.dedup / List.mergeSort / lexLe),
checked behaviorally by conformance_check.py — not assumed via an `axiom`.

There are therefore no `axiom <callee>_prop` declarations and no `opaque`
callees to validate. Per SPEC_GUIDE this gate is a skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "sphinx-doc__sphinx-10466",
    "reason": "no consumed axiom and no opaque callee; all ops modeled deeply "
              "and validated by G-CONF",
}))
sys.exit(0)
