#!/usr/bin/env python3
"""G-AX skip stub for django__django-14534.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`BoundWidget.id_for_label`) reports the
DOM identifier to associate with a rendered option's label by reading the value
stored under the `'id'` key of the option's attribute table
(`self.data['attrs'].get('id')`). The behavior the patch changes — which value
the property returns — is modeled DEEPLY by `List.lookup "id"` over the option's
attribute table (SPEC_GUIDE §3: a deeply-modeled changed op is never
axiomatized). The only callee is the builtin `dict.get`, which IS the changed op
itself. The construction of `self.data['attrs']` is upstream of the modeled
property and unchanged by the patch, so its contents are a free input rather than
an axiomatized callee result. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The R/I impl (and its binding to the real patched body) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14534",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "id-attribute lookup is modeled deeply (List.lookup over the "
                  "option's attribute table), so the impl is all R/I (validated "
                  "by G-CONF against the real patched id_for_label body)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
