#!/usr/bin/env python3
"""G-AX skip stub for django__django-13551.

No consumed callee axiom is declared in the bundle. The behavior the patch
changes — appending the user's (normalized) email contribution to the
concatenated token state string — is modeled DEEPLY in Lean as a string
concatenation over the component inputs (an R/I impl), validated against the real
post-patch assembly by the differential `conformance_check.py` (G-CONF), not by
an axiom. The email-locating I/O (`get_email_field_name` + `getattr(... ) or ''`)
is abstracted at the boundary into the `emailRaw : Option String` input plus the
`emailPart` normalization; there is no `opaque`/`axiom` callee whose contract the
proof consumes.

There is therefore nothing for G-AX to validate. Exit 0 with status=skip.
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-13551",
    "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
              "(state-string assembly validated by G-CONF)",
}))
sys.exit(0)
