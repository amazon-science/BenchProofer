#!/usr/bin/env python3
"""G-AX skip stub for django__django-15103.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized: the modeled function (`json_script`) selects whether the script
tag carries an `id` attribute (keyed on the truthiness of `element_id`) and frames
the safe JSON body with the corresponding literal tag text. The two unchanged
steps — the JSON body encoder (`json.dumps(...).translate(...)` + `mark_safe`) and
the attribute escaping `format_html` applies to the substituted id — are left as
universally-quantified parameters `jsonBody` / `escapeId : String -> String` in
Solution.lean. The spec holds for EVERY encoder/escaper, so the proof consumes no
property of either. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The branch-selection +
framing impl (and its binding to the REAL encode pipeline and format_html
escaping) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-15103",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "JSON body encoder and the id attribute-escaping are universally "
                  "quantified, so the impl is all R/I/A-reference (validated by "
                  "G-CONF against the real json_script encode + format_html steps)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
