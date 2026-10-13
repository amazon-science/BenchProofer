#!/usr/bin/env python3
"""G-AX soundness check for django__django-13112 — NO AXIOMS (skip stub).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (mapping.md §5, refinement.md §C). The single changed operation — the
case-normalization of a (possibly application-qualified) model reference into
`kwargs['to']` (the patch's `if '.' in model: app_label, model_name =
model.split('.'); ... else: model.lower()`) — is modeled DEEPLY in
Solution.lean's `pure` region (`foldCase`, `isQualified`, `appPart`, `namePart`,
`normalizedRef`), entirely from concrete character operations over the input.
Per directive 7 the operation the patch changes is never axiomatized, so there
is nothing for G-AX to validate against a real callee.

The deep model's fidelity to the patched behaviour is instead exercised
mechanically by conformance_check.py (G-CONF), which drives the REAL patched
ForeignKey.deconstruct and diffs it against the R/I transliteration over >=10^5
fuzzed inputs.

Exit 0 with a skip status (meta.json gates.G-AX.status = "skip").
"""
import sys


def main():
    print("G-AX SKIP: no axioms / no A-reference in this bundle; the changed "
          "model-reference normalization is modeled deeply (pure region) and "
          "checked by G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
