#!/usr/bin/env python3
"""G-AX soundness check for django__django-11815 — NO AXIOMS (skip stub).

This bundle declares no `axiom` and no A-reference deep model of an outside
callee (mapping.md §3, refinement.md §C). The single changed operation — keying
an enum member's source reference on its symbolic NAME in subscript form
(`module.Class['NAME']`) instead of its serialized VALUE in call form
(`module.Class(value)`), and emitting only the enum module's import — is modeled
DEEPLY in Solution.lean's `pure` region (`memberReference`, `quotedName`,
`referenceImports`), entirely from concrete string interpolation over the
inputs. Per directive 7 the operation the patch changes is never axiomatized,
and the post-patch reference construction calls no outside callee, so there is
nothing for G-AX to validate against a real callee.

The deep model's fidelity to the patched behaviour is instead exercised
mechanically by conformance_check.py (G-CONF), which drives the REAL patched
`EnumSerializer.serialize` and diffs it against the R/I transliteration over
>=10^5 fuzzed inputs.

Exit 0 with a skip status (meta.json gates.G-AX.status = "skip").
"""
import sys


def main():
    print("G-AX SKIP: no axioms / no A-reference in this bundle; the changed "
          "enum-member reference construction is modeled deeply (pure region) "
          "and checked by G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
