#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-9367.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized: the modeled function (`_UnparseVisitor.visit_Tuple`) wraps and
joins the already-rendered text of a tuple's components, selecting the wrapping by
component count. The per-component rendering step (`self.visit`) is unchanged by
the patch and is absorbed into the input `elts : List String` (the list of
already-rendered component strings) in Solution.lean — the spec holds for EVERY
per-component renderer, so the proof consumes no property of it. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is nothing
for G-AX to validate. The arity-dependent wrap/join impl (and its binding to the
REAL recursive visitor) is differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-9367",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "per-component renderer is absorbed into the input (list of "
                  "already-rendered component strings), so the impl is all "
                  "R/I/A-reference (validated by G-CONF against the real "
                  "recursive unparse visitor)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
