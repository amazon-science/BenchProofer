#!/usr/bin/env python3
"""G-AX executable soundness check for sympy__sympy-21930.

This bundle ships **no axiomatized callees and no A-reference deep models**
(refinement.md §D, meta.json axioms=[] / deep_model_references=[]): the three
modeled `_latex` renderers perform only pure, total, fully-expressible
character-sequence operations (literal templates, the unchanged index-name join
modeled deeply as `concatNames`, and the added `{ … }` group wrap modeled as
`wrapGroup`). Every operation is an R or I leg, validated mechanically by
G-CONF (`conformance_check.py`).

Therefore there is no callee contract to validate here. G-AX is vacuously
sound; this script asserts the no-axiom invariant against meta.json and exits 0.

stdlib-only. Exit 0 iff the no-axiom invariant holds.
"""
import json
import os
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    meta_path = os.path.join(here, "meta.json")
    try:
        meta = json.load(open(meta_path))
    except Exception as e:
        print("G-AX ERROR: cannot read meta.json: %r" % e)
        return 1

    axioms = meta.get("axioms", [])
    deep_refs = meta.get("deep_model_references", [])

    if axioms:
        print("G-AX FAIL: meta.json declares %d axiom(s) but axiom_check.py "
              "validates none — over-claim risk: %r" % (len(axioms), axioms))
        return 1
    if deep_refs:
        print("G-AX FAIL: meta.json declares %d deep_model_reference(s) but "
              "axiom_check.py validates none: %r" % (len(deep_refs), deep_refs))
        return 1

    print("G-AX OK: no axiomatized callees and no A-reference deep models in "
          "this bundle (pure string-formatting fix; all ops are R/I legs "
          "checked by G-CONF). Nothing to validate; vacuously sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
