#!/usr/bin/env python3
"""G-AX — astropy__astropy-14508.

This bundle consumes NO callee axiom and declares NO A-reference. The behavior
the patch changes — which textual form of a value feeds the 20-character
limiting block — is modeled DEEPLY over grounded textual carriers (`reprStr`,
`fixedStr`); SPEC_GUIDE §3 forbids axiomatizing a deeply-modeled changed op. The
`axioms` region of Solution.lean is empty.

So G-AX has nothing to validate: it is a skip stub.
"""
import json
import sys

if __name__ == "__main__":
    print(json.dumps({
        "status": "skip",
        "instance": "astropy__astropy-14508",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    sys.exit(0)
