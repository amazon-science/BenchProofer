#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-13496 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
behavior the patch changes is the threading of one constructor argument into the
stored configuration (and storing it by identity); this is modeled DIRECTLY as
record-field assignment (refinement.md rows are all I/R). The parent
constructor's per-attribute work is itself a sequence of identity stores, modeled
field-for-field, so there is no callee contract to validate against the real
repo. SPEC_GUIDE §3 forbids axiomatizing a deeply/directly-modeled changed op.
The R/I legs are validated by G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-13496",
    "reason": "no consumed callee axiom and no A-reference; impl is all I/R "
              "(identity-store of constructor args), validated by G-CONF",
}))
sys.exit(0)
