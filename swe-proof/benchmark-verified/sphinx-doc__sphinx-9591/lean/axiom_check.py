#!/usr/bin/env python3
"""G-AX skip stub for sphinx-doc__sphinx-9591.

No consumed callee axiom is declared in the bundle and no deep-model A-reference
is axiomatized. The modeled function (`PyProperty.handle_signature`, type arm)
assembles the type-annotation children of a documented property: the `": "`
separator as a plain-text node, followed by the nodes produced by the unchanged
annotation parser. That parser (`_parse_annotation`) is left as a
universally-quantified parameter `crossRefParser : String -> List Node` in
Solution.lean — the spec holds for EVERY parser, so the proof consumes no
property of it. There is no `opaque` callee and no `axiom <callee>_prop` in
Solution.lean, so there is nothing for G-AX to validate. The node-framing impl
(and its binding to the REAL `_parse_annotation`) is differential-tested by
conformance_check.py (G-CONF).

stdlib-only; emits a skip status and exits 0.
"""
import json
import sys


def main() -> int:
    print(json.dumps({
        "status": "skip",
        "instance": "sphinx-doc__sphinx-9591",
        "reason": "no consumed callee axiom and no axiomatized A-reference; the "
                  "annotation parser is universally quantified, so the impl is "
                  "all R/I/A-reference (validated by G-CONF against the real "
                  "_parse_annotation callee)",
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
