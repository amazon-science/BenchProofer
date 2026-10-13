#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-13028.

This bundle declares **no axioms** and **no deep-model references**: the single
operation the gold patch changes (the per-node filterability guard) is modeled
*identically* (`nodeBad`), and the surrounding tree traversal is a structural
type refinement (`anyBad` over the flattened node list). Every refinement leg is
therefore R or I and is handled mechanically by G-CONF (conformance_check.py);
there is no opaque callee whose contract the proof assumes.

G-AX consequently has no axiom `ensures` to validate. To keep the gate
meaningful (rather than a silent pass), this script:

  1. asserts the bundle truly declares no axioms (meta.json `axioms == []` and
     `deep_model_references == []`), so a future edit that smuggles in an axiom
     without a soundness check is caught here; and
  2. exercises the two CPython builtins the refinement leans on
     (`getattr(obj, 'filterable', True)` and `hasattr(obj, 'resolve_expression')`)
     to confirm their fixed semantics match the mapping.md §2 bijection that
     G-CONF relies on.

Imports only the standard library + json. Exit 0 iff the no-axiom claim holds
and the builtin semantics are as documented.
"""
import json
import os
import sys


def check_no_axioms():
    here = os.path.dirname(os.path.abspath(__file__))
    meta_path = os.path.join(here, "meta.json")
    with open(meta_path) as fh:
        meta = json.load(fh)
    axioms = meta.get("axioms", [])
    refs = meta.get("deep_model_references", [])
    assert axioms == [], (
        "axiom_check expected no axioms but meta.json lists %r; an axiom "
        "requires an executable soundness check here." % (axioms,))
    assert refs == [], (
        "axiom_check expected no deep-model references but meta.json lists "
        "%r; an A-reference requires a == real-callee check here." % (refs,))


def check_builtin_semantics():
    class _N:
        pass

    # getattr default-True: a node lacking `filterable` reads as True (the
    # mapping.md bijection: absent ⇒ filterable = true).
    n = _N()
    assert getattr(n, "filterable", True) is True
    n.filterable = False
    assert getattr(n, "filterable", True) is False
    n.filterable = True
    assert getattr(n, "filterable", True) is True

    # hasattr resolve_expression: absent ⇒ isOperand = false; present ⇒ true.
    m = _N()
    assert hasattr(m, "resolve_expression") is False
    m.resolve_expression = True
    assert hasattr(m, "resolve_expression") is True


def main():
    check_no_axioms()
    check_builtin_semantics()
    print("G-AX OK: bundle declares no axioms / no A-references; the two "
          "builtin refinements (getattr filterable default-True, hasattr "
          "resolve_expression) match the mapping.md bijection.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
