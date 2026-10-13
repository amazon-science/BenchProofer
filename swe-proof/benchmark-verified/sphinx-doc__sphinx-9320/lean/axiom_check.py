#!/usr/bin/env python3
"""G-AX — axiom soundness check for sphinx-doc__sphinx-9320 — skip stub.

The bundle consumes NO `axiom <callee>_prop`. The single modeled function
(`validateRootEntry`, i.e. `is_path_or_empty`) adds an empty-string
short-circuit and otherwise delegates to the UNCHANGED existing-directory
validator (`is_path`). That validator is declared `opaque checkExistingDir` only
so it can appear in the executable implementation; it is an A-REFERENCE that
occurs IDENTICALLY in the specification's non-empty clause and the
implementation's non-empty branch, so it cancels in the differential. The proof
of `correct_validateRootEntry` consumes no property of it (the empty branch is
discharged structurally; the non-empty branch is a syntactic identity).

The soundness-critical behavior the patch changes — accepting an empty entry
verbatim — is modeled DEEPLY (a direct `.ok x` write), which SPEC_GUIDE §3
forbids axiomatizing. The R/I leg is validated by G-CONF.

There is therefore no callee contract to validate against the real repo, and this
script is a SKIP stub (SPEC_GUIDE: axiom_check.py "may be a skip stub" when the
proof needs no callee axiom). stdlib-only; exit 0.
"""
import sys


def main() -> int:
    print("status=skip reason=no consumed axiom; the existing-directory "
          "validator is an A-reference identical in spec and impl (validated "
          "by G-CONF), and the empty-acceptance decision is modeled deeply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
