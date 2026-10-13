#!/usr/bin/env python3
"""G-AX skip stub for django__django-13279.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used. The modeled function (`SessionBase.encode`) selects between two
serialization schemes based on the configured serialization-format identifier;
the two schemes are declared `opaque` (`legacyEncode`, `modernEncode`) purely so
they can appear in the executable impl, and the correctness proof closes by case
analysis on the identifier (`algo == "sha1"`) WITHOUT consuming any property of
either scheme. There is therefore no `axiom <callee>_prop` in Solution.lean and
nothing for G-AX to validate.

The behavioral conformance that matters here — that `encode` dispatches to the
compatibility scheme exactly when the identifier is 'sha1' and to the standard
scheme otherwise — is differential-tested by conformance_check.py (G-CONF), which
drives the REAL patched `encode` (with its real `_legacy_encode` / `signing.dumps`
branches) in-container over >=1e5 fuzzed inputs.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-13279",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(dispatch validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
