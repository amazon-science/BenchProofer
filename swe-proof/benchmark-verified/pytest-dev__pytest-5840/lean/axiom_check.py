#!/usr/bin/env python3
"""G-AX skip stub for pytest-dev__pytest-5840.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function is the cache-key derivation inside
`PytestPluginManager._importconftest`: given the canonical resolved path of a
conftest file, produce the key under which the loaded module is cached. The
behavior the patch changes — how that key is derived from the resolved path — is
modeled DEEPLY (SPEC_GUIDE §3: a deeply-modeled changed op is never axiomatized):
post-fix it is the IDENTITY on the resolved path (case preserved, the fix), and
pre-fix it is the ASCII lower-case fold (`os.path.normcase` on a case-insensitive
file system, the bug). The path canonicalization (`Path.resolve()` /
`py.path.realpath()`) is UNCHANGED by the patch and is factored out as the
already-resolved input, so no external callee contributes a property the proof
consumes. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The R/I impl (and its
binding to the real patched key derivation) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "pytest-dev__pytest-5840",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "cache-key derivation is modeled deeply (identity on the "
                  "resolved path post-fix; lower-case fold pre-fix), so the impl "
                  "is all R/I (validated by G-CONF against the real patched "
                  "_importconftest key derivation)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
