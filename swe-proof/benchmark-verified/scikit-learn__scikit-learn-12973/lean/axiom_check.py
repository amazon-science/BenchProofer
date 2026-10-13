#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-12973 — skip stub.

The bundle consumes NO unchanged-callee axiom and declares NO A-reference: the
modeled value (`deliveredCopy`) is all R/I (validated by G-CONF). The data-
preparation step (`_preprocess_data`) and the path solver (`lars_path`) are not
modeled — only the boolean threaded into the data-preparation step's `copy` slot
is, and that boolean is pure data flow. There is therefore no callee contract to
validate against the real repo.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "scikit-learn__scikit-learn-12973",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(validated by G-CONF)",
}))
sys.exit(0)
