#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-8120.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is used: the modeled function (the search-list assembly inside
`Sphinx._init_i18n`) reads the caller-supplied directories and the bundled
directory as plain data and builds an ordered list by literal construction and
concatenation, modeled directly in Lean as list construction / `++` (R/I ops —
see refinement.md). There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The full R/I impl is
differential-tested by conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-8120",
        "reason": "no consumed callee axiom and no A-reference; impl is all R/I "
                  "(validated by G-CONF)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
