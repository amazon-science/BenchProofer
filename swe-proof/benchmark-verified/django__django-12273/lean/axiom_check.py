#!/usr/bin/env python3
"""G-AX for django__django-12273 — skip stub.

The modeled function (`setPrimaryKey` <-> `Model._set_pk_val`) consumes NO
opaque-callee axiom and deep-models NO callee (refinement.md: every impl op is
R/I). The patch body is a concrete sequence of attribute-store updates over
metadata supplied as input (`self._meta.parents.values()`,
`parent_link.target_field.attname`, `self._meta.pk.attname`); there is no
unchanged callee whose contract the proof relies on. The behavioral conformance
that matters here — the R/I shadow vs the post-patch `_set_pk_val` — is validated
by `conformance_check.py` (G-CONF).

stdlib-only. Exit 0 (skip).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-12273",
    "reason": "no consumed axiom and no A-reference callee; impl region is all "
              "R/I (attribute-store updates over input metadata). Behavioral "
              "conformance validated by G-CONF.",
}))
sys.exit(0)
