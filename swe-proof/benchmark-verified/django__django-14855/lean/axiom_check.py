#!/usr/bin/env python3
"""G-AX skip stub for django__django-14855.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized: the modeled function (`AdminReadonlyField.get_admin_url`) assembles
the change-view route name, asks a URL-resolution step to turn that route name and
the encoded record id into a URL — telling it the currently-effective admin-site
identifier — and frames the outcome as a link or falls back to the record's
display text. Both downstream steps are left as universally-quantified parameters
in Solution.lean:

  * `resolveUrl : String -> String -> Option String -> Option String`  (the real
    `reverse`, with NoReverseMatch folded into Option), and
  * `formatLink : String -> String -> String`  (the real `format_html`).

The spec holds for EVERY resolver and formatter, so the proof consumes no property
of either. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The route formatting +
current-app-threaded resolution + link/fallback framing (and its binding to the
REAL reverse/format_html) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14855",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "URL resolver and link formatter are universally quantified, so "
                  "the impl is all R/I/A-reference (validated by G-CONF against the "
                  "real reverse/format_html callees)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
