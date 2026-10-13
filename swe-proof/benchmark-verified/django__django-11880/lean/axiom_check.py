#!/usr/bin/env python3
"""G-AX skip stub for django__django-11880.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`Field.__deepcopy__`) duplicates a form
field: starting from a shallow copy, it replaces each mutable container with a
freshly allocated object carrying the same contents. The behavior the patch
changes — the error-message mapping becoming an INDEPENDENT object (a fresh
identity carrying equal contents) rather than a shared alias — is modeled DEEPLY
over the field's components (`errMsgId` identity + `errMsg` contents; SPEC_GUIDE
§3: a deeply-modeled changed decision is never axiomatized). The widget deep
copy and the validator-list slice are modeled the same way (fresh identity +
preserved/equal contents). There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The R/I impl (and its binding to the real patched `__deepcopy__`) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-11880",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "fresh-object duplication of each mutable container (widget, "
                  "error-message mapping, validator list) is modeled deeply "
                  "(ObjId identity + contents), so the impl is all R/I "
                  "(validated by G-CONF against the real patched __deepcopy__)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
