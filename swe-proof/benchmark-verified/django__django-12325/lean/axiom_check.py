#!/usr/bin/env python3
"""G-AX — axiom soundness check for django__django-12325.

This bundle consumes NO callee axiom. The modeled function
(`implementation_collectParentLinks`) builds the parent-link mapping by a guarded
last-write-wins fold over candidate-field attributes that enter as plain DATA
(`isinstance`, `field.remote_field.parent_link`, `resolve_relation`,
`make_model_tuple` are observed and supplied as the `FieldInfo` record; the
guarded dict insertion is modeled deeply as `dictInsert`). refinement.md tags
every op R or I; `meta.json` has `axioms = []` and `deep_model_references = []`.

There is therefore no `axiom <callee>_prop` to validate. This is a skip stub.
"""
import sys


def main() -> int:
    print("no consumed callee axioms (axioms=[], deep_model_references=[]); "
          "nothing to validate")
    print("status=skip")
    return 0


if __name__ == "__main__":
    sys.exit(main())
