#!/usr/bin/env python3
"""G-AX skip stub for django__django-14752.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`AutocompleteJsonView.get`) assembles its
response by applying a per-item rendering to each selected object, in order, and
copying the page-has-next flag through verbatim. The per-item rendering — the new
overridable `serialize_result(obj, to_field_name)` extension point — is left as a
universally-quantified parameter `render : Obj -> String -> E` in Solution.lean
(the objects and entry type are likewise abstract carriers `Obj` / `E`). The spec
holds for EVERY rendering, so the proof consumes no property of it. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing
for G-AX to validate. The per-object loop + flag framing (and its binding to the
REAL `serialize_result`) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14752",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "per-item rendering (the serialize_result extension point) is "
                  "universally quantified, so the impl is all R/I/A-reference "
                  "(validated by G-CONF against the real serialize_result step)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
