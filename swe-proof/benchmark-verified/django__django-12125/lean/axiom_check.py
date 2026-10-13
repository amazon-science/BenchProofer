#!/usr/bin/env python3
"""G-AX skip stub for django__django-12125.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`TypeSerializer.serialize`) turns a class
value into its `(reference, imports)` source pair. Every operation it performs is
a direct read of an attribute on the class descriptor (the two special-case
identity tests, the `hasattr(__module__)` test, the `__module__` /  `__name__` /
`__qualname__` reads) or a pure string/collection assembly. The behavior the
patch changes — emitting the class's fully-qualified in-module path
(`__qualname__`) rather than its bare leaf name (`__name__`) in the non-builtins
branch — is modeled DEEPLY as the `TypeRef.fullName` field (SPEC_GUIDE §3: a
deeply-modeled changed read is never axiomatized). There is no `opaque` callee
and no `axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to
validate. The R/I impl (and its binding to the real patched serializer) is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-12125",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "serializer reads only attributes of the class descriptor and "
                  "the changed read (__name__ -> __qualname__) is modeled deeply "
                  "as TypeRef.fullName, so the impl is all R/I (validated by "
                  "G-CONF against the real patched TypeSerializer.serialize)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
