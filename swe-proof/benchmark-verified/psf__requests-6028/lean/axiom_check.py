#!/usr/bin/env python
"""G-AX skip stub for psf__requests-6028.

No consumed callee axiom is declared in the bundle. The only operation the patch
changes — re-attaching the userinfo/credentials field to the front of the
authority on re-assembly (`netloc = '@'.join([auth, netloc])`) — is modeled
DEEPLY in Lean (spelled out in `reassemble` / `implementation_prependScheme` as
`auth ++ "@" ++ authority`, an A-reference) and validated against the real
patched callee by the differential `conformance_check.py` (G-CONF), not by an
axiom. The upstream URL parse step is out of scope (it produces the function's
inputs and is not changed by the patch).

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (userinfo re-attachment + URL "
          "re-assembly modeled deeply; validated by G-CONF as an A-reference)")
    sys.exit(0)
