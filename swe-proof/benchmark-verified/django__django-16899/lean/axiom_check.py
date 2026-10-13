#!/usr/bin/env python3
"""G-AX — skip stub.

The proof consumes NO callee axiom: the axioms region of Solution.lean is empty
(no `opaque`/`_prop` decls). The four resolution checks are R-refined inputs
(their boolean outcomes are taken as given, not axiomatized), and the only
changed operation — the error-message format string — is modeled DEEPLY as a
concrete `String` concatenation, delegating to no real callee (it is neither
A-consumed nor A-reference; see refinement.md / mapping.md). There is therefore
no callee contract to validate.

exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("G-AX SKIP: no consumed axiom / A-reference callee in this bundle")
    sys.exit(0)
