#!/usr/bin/env python3
"""G-AX for sphinx-doc__sphinx-9258 — SKIP stub.

The bundle declares no `opaque` callee and consumes no `axiom <callee>_prop`:
the only changed op is the regex tokeniser in `PyXrefMixin.make_xrefs`, which is
modeled DEEPLY as pure Lean functions (SPEC_GUIDE §3 forbids axiomatizing a
deeply-modeled changed op). The impl region is all R/I; its soundness against the
real callee (`re.split` + `delims_re.match`) is checked mechanically by
`conformance_check.py` (G-CONF), not by a callee-axiom contract.

Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "gate": "G-AX",
    "instance": "sphinx-doc__sphinx-9258",
    "status": "skip",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(the changed regex tokeniser is modeled deeply; validated by G-CONF)",
}, indent=2))
sys.exit(0)
