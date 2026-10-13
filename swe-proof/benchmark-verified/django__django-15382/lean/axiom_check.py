#!/usr/bin/env python3
"""G-AX for django__django-15382 — skip stub (no consumed/reference axiom).

The modeled function (`compileExistenceCheck` <-> `Exists.as_sql`) is a PURE
dispatch over `(negated, inner)`, where `inner` is the outcome of the unchanged
`super().as_sql(...)` call (success `(sql, params)` or `EmptyResultSet`). No
unchanged callee is modeled deeply or consumed as an opaque axiom: the callee's
outcome is the boundary INPUT of the modeled function, not part of its body
(refinement.md: every op is R or I; meta.json axioms=[], deep_model_references=[]).

There is therefore no callee contract to validate against a real repo callee.
The behavioral conformance that matters — the post-patch dispatch vs the Lean
impl — is mechanically checked by `conformance_check.py` (G-CONF), which diffs the
faithful post-patch `Exists.as_sql` control flow against the Lean shadow over
fuzzed `(negated, inner)`.

stdlib-only. Exit 0 (skip).
"""
import json
import sys

print(json.dumps({
    "status": "skip",
    "instance": "django__django-15382",
    "reason": "no consumed/reference axiom: the modeled function is a pure "
              "dispatch over (negated, inner) with no deeply-modeled or "
              "axiomatized callee; behavioral conformance is checked by G-CONF",
}))
sys.exit(0)
