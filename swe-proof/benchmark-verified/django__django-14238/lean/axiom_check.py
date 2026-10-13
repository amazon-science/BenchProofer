#!/usr/bin/env python3
"""G-AX skip stub for django__django-14238.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized: the modeled method (`AutoFieldMeta.__subclasscheck__`) accepts a
candidate class iff it is a reflexive-transitive subclass of one of the
designated member classes, or the ordinary inherited check accepts it. Both
unchanged callees -- the subclass relation `issubclass` (`isSub`) and the
inherited default check `super().__subclasscheck__` (`superCheck`) -- are left as
universally-quantified parameters in Solution.lean, so the spec holds for EVERY
such relation/check and the proof consumes no property of either. There is no
`opaque` callee and no `axiom <callee>_prop` in Solution.lean, so there is
nothing for G-AX to validate. The any-over-members disjunction structure (and its
binding to the REAL `issubclass` / inherited check) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "django__django-14238",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "subclass relation and the inherited subclass check are "
                  "universally quantified, so the impl is all R/I/A-reference "
                  "(validated by G-CONF against the real issubclass and inherited "
                  "__subclasscheck__ callees)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
