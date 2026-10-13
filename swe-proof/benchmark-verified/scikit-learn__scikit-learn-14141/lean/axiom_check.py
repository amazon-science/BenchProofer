#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-14141 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference. The
only behavior the patch changes is the membership/order of the hardcoded
dependency-name roster, modeled DEEPLY/literally as `expectedDeps`. The per-module
version resolution (`lookupVersion`) is an UNCHANGED callee, declared `opaque` so
it can appear in the executable impl and used IDENTICALLY on both sides of the
spec equation, so the proof consumes no property of it. There is therefore no
callee contract to validate against the real repo. The R/I legs are validated by
G-CONF.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-14141",
    "reason": "no consumed callee axiom and no A-reference; the changed value "
              "(the dependency roster) is modeled literally and the version "
              "resolver is a shared opaque symbol; R/I validated by G-CONF",
}))
sys.exit(0)
