#!/usr/bin/env python3
"""G-AX for django__django-15268 — SKIP STUB.

The proof of `correct_canOptimizeAcross` consumes NO `axiom <callee>_prop`
property of any callee. The single unchanged callee, `references_model`
(Lean `affectsModel`), is an A-REFERENCE, not an A-consumed axiom: the proof
reasons about its boolean value symbolically and never assumes any property of
it. Its value-level identity to the real callee is exercised mechanically by
conformance_check.py (G-CONF), which calls the REAL `references_model` in its
R/I shadow. Hence there is no axiom for G-AX to validate.

stdlib-only; exits 0 (status=skip).
"""
import sys


def main() -> int:
    print("G-AX: skip — no consumed callee axiom (affectsModel is an "
          "A-reference, validated by G-CONF)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
