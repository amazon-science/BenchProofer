#!/usr/bin/env python3
r"""G-AX skip stub for sphinx-doc__sphinx-7454.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled behavior (the cross-reference `make_xref(text)`
builds for a single annotation token) is spelled out deeply: the four fields
(domain, kind, target, label) are concrete data in the `TypeRef` record, and the
only branch — `reftype = 'obj'` iff `text == 'None'`, else `'class'` — is a
concrete `if` in Solution.lean. There is no `opaque` callee and no
`axiom <callee>_prop` in Solution.lean, so there is nothing for G-AX to validate.
The impl (and its binding to the REAL patched `make_xref` via `_parse_annotation`)
is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-7454",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "cross-reference fields are concrete TypeRef data and the "
                  "None-token kind branch is a concrete `if`, so the impl is all "
                  "R/I (validated by G-CONF against the real patched make_xref via "
                  "_parse_annotation)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
