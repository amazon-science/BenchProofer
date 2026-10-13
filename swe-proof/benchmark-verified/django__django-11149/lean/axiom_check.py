#!/usr/bin/env python3
"""G-AX — axiom soundness check for django__django-11149.

SKIP STUB. The bundle declares and consumes NO callee `_prop` axiom.

The only repo callee the changed code calls is `get_permission_codename(action,
opts)` (UNCHANGED, `django/contrib/auth/__init__.py`), whose body is exactly
`'%s_%s' % (action, opts.model_name)`. It is modeled DEEPLY in Solution.lean as
`permString` (the `"<app>.<action>_<model>"` format spelled out), so it is an
A-reference validated by G-CONF, never an axiomatized contract (SPEC_GUIDE
§0.7 / §3). The user's permission lookup `request.user.has_perm(s)` is modeled
as membership of `s` in the supplied `userPerms` input, and target-model
resolution over `opts.fields` is modeled deeply as the field loop. Nothing is
axiomatized.

Exit 0 (skip).
"""
import sys

if __name__ == "__main__":
    print("status=skip (no consumed callee axioms; codename format + target "
          "resolution modeled deeply, validated by G-CONF)")
    sys.exit(0)
