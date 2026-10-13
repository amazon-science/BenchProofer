#!/usr/bin/env python
"""G-AX for scikit-learn__scikit-learn-14629 — SKIP STUB.

The bundle declares NO callee axioms. The one modeled behavior — exposing, per
target, the class labels recorded by each fitted sub-model — is modeled DEEPLY:
the impl collects each sub-model's class labels in order, spelled out directly in
Lean as `subModels.map (·.classLabels)` (an accumulator `for` loop). The only
callee, the shared multi-target fitting routine (`super().fit`), is UNCHANGED and
its result (the fitted sub-model list) enters as input DATA, not as an
axiomatized contract. There is no `axiom <callee>_prop` for the proof to consume,
so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
