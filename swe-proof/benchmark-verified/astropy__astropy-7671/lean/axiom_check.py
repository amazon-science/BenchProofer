#!/usr/bin/env python
"""G-AX skip stub for astropy__astropy-7671.

No consumed callee axiom is declared in the bundle. The opaque callees
(`versionGe` / `versionGt`, binding `distutils.version.LooseVersion`'s `>=` / `>`,
and `orderable`, the total question of whether that comparison COMPLETES on a pair)
appear identically in the specification and the implementation, so the proof
consumes NO property of them — there is no `axiom *_prop` to validate.

The comparison is PARTIAL (it raises on incommensurable pairs; bpo-30272), so it is
carried as an operation on its DOMAIN: `versionGe a b (h : orderable a b = true)`.
That is a signature choice, not an assumed property — no axiom constrains where
`orderable` is `true`, and the proof never appeals to one; the evidence argument is
supplied by the implementation's own guard and cancels. The `none` <-> raises bridge
on the RESULT is validated by the G-CONF differential in both directions, which is
why it is not an axiom-lane obligation.

The only operation the patch changes — reducing the required-version string to its
leading release-number prefix before the comparison — is modeled DEEPLY in Lean
(`releasePrefix` / `normalizeVersion`, an A-reference) and validated against the
real patched behavior by the differential `conformance_check.py` (G-CONF), not by
an axiom.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (version-prefix reduction "
          "modeled deeply; validated by G-CONF as an A-reference; LooseVersion "
          "comparison is an opaque callee with no assumed property — its "
          "partiality is carried in the signature as an operation on its "
          "domain (an evidence argument, with nothing constraining where the "
          "domain predicate holds) and the none<->raises bridge on the result "
          "is validated by G-CONF, not by an axiom)")
    sys.exit(0)
