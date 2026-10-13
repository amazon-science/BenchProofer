#!/usr/bin/env python3
"""G-AX skip stub for psf__requests-1766.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`HTTPDigestAuth.build_digest_header`)
ASSEMBLES the Digest `Authorization` header string from component values
(username, realm, nonce, request uri, response digest, optional opaque/algorithm/
digest, nonce-count, client-nonce) that are all computed UPSTREAM in the same
function and unchanged by the patch. Each component is modeled as a free `String`
parameter in Solution.lean, so the spec holds for EVERY set of component values
and the proof consumes no property of any callee. There is no `opaque` callee and
no `axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The assembly (and the discriminating `qop="auth"` quoting) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "psf__requests-1766",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "header-assembly impl is all R/I over free component-string "
                  "parameters (validated by G-CONF against the real patched "
                  "build_digest_header)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
