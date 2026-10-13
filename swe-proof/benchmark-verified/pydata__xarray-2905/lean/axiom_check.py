#!/usr/bin/env python3
"""G-AX for pydata__xarray-2905 — SKIP stub.

The changed decision (an `isinstance` type test plus a `.values` unwrap) is
modeled DEEPLY in Solution.lean (structural case split on `Obj`), not via any
axiomatized unchanged callee. There is therefore no `axiom <callee>_prop` to
validate against a real callee. G-AX is a no-op for this bundle.
"""
import json, sys

print(json.dumps({"status": "skip", "reason": "no consumed callee axioms; "
                  "changed op modeled deeply"}))
sys.exit(0)
