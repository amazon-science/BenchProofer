#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-11555 — SKIPPED.

There are NO axioms and NO A-reference deep models in this bundle, so there is
nothing to check against a real callee.

The only unchanged callee the modeled loop consults is the recursive name
resolution `self.find_ordering_name(item, …)` (mapping.md §3.1). It is modeled
as a FREE total function `resolve : Name -> List Pair`: the postcondition
`out = expandItems resolve items` holds for EVERY `resolve`, so no
`Requires`/`Ensures` is owed on it (SPEC_GUIDE directive 7 — a free input is
strictly weaker than any concrete callee). meta.json therefore has `axioms: []`
and `deep_model_references: []`.

The behavioural content of the fix — that an order-expression item contributes
exactly `[(e, False)]` rather than being routed through name resolution — is
modeled DEEPLY in the pure region (`itemContribution`), carried by G-VERIFY +
G-DIFF + G-CONF, not by any axiom. (Mirrors the django__django-12858 /
django__django-13033 precedents: free schema/resolution inputs, no G-AX.)
"""
import sys


def main():
    print("G-AX status=skip: django__django-11555 has no axioms and no "
          "A-reference deep models. The only unchanged callee (the recursive "
          "name resolution find_ordering_name(item, ...)) is modeled as a free "
          "total function `resolve`, which owes no contract; nothing to check "
          "against a real callee. Soundness covered by G-VERIFY + G-DIFF + "
          "G-CONF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
