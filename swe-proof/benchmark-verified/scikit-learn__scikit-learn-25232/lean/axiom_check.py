#!/usr/bin/env python3
"""G-AX for scikit-learn__scikit-learn-25232 — SKIP STUB.

The round-zero constant fill and the sentinel replacement are modeled deeply in
Solution.lean (the per-feature statistic and the element-wise rewrite are spelled
out); no UNCHANGED callee's behavior is left opaque and axiomatized. There are no
`axiom <callee>_prop` declarations, so G-AX has nothing to validate. The deep
model is instead validated end-to-end against the real library routine by G-CONF.
Exit 0 with status=skip. stdlib-only.
"""
import json
import sys

print(json.dumps({"status": "skip", "reason": "no consumed axioms in bundle"}))
sys.exit(0)
