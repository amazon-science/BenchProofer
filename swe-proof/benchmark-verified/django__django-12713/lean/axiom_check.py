#!/usr/bin/env python3
"""G-AX skip stub for django__django-12713.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (the widget-selection block of
`formfield_for_manytomany`) decides which form widget a multi-valued relation
field ends up with. The behavior the patch changes — whether the
classification cascade runs at all — is modeled DEEPLY by the
`if widget.isNone` guard over the caller-supplied widget plus `defaultWidget`
over the four configuration lists (SPEC_GUIDE §3: a deeply-modeled changed
decision is never axiomatized).

The unchanged callees contribute no property the proof consumes:
`get_autocomplete_fields(request)` just returns `self.autocomplete_fields` and
is read directly AS the input list `auto`; the widget constructors
(`AutocompleteSelectMultiple`, `ManyToManyRawIdWidget`, `FilteredSelectMultiple`)
are unchanged and only the selected KIND is observable, captured by the `Widget`
constructors. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The R/I impl (and its
binding to the real patched selection block) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12713",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "widget-selection guard and the classification cascade are "
                  "modeled deeply (widget.isNone / defaultWidget), so the impl "
                  "is all R/I (validated by G-CONF against the real patched "
                  "formfield_for_manytomany selection block)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
