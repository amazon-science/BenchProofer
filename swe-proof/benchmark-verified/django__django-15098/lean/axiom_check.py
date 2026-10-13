#!/usr/bin/env python3
"""G-AX — django__django-15098: SKIP (no consumed callee axiom).

The modeled function `get_language_from_path` invokes one UNCHANGED callee,
`get_supported_language_variant`, modeled in Solution.lean as the opaque
signature `resolveVariant : List Char -> Option (List Char)`. It appears on BOTH
sides of `problem_spec_langCodeFromPath` (the result is defined as
`resolveVariant` of the extracted candidate), so the proof consumes NO `_prop`
axiom about it — there is no axiom property to validate against the real callee.
The same holds for `nonAsciiOutcome : List Char -> Option (List Char)`, the
opaque whole-routine outcome on paths carrying a non-ASCII code point (where
the matcher's word class is library-specific): it too appears identically on
both sides of the spec equation with no asserted properties.

The single CHANGED op (the URL-path language-prefix regex matcher) is modeled
DEEPLY as `langPrefix` on the all-ASCII branch and is validated mechanically
against the real `re` engine by conformance_check.py (G-CONF), not here.

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "reason": "no consumed callee axiom; opaque resolveVariant and "
                  "nonAsciiOutcome appear on both sides of the spec, the "
                  "changed regex op is deep-modeled on the ASCII branch "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
