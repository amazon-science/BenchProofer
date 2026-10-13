#!/usr/bin/env python
"""G-AX skip stub for django__django-14539.

No consumed callee axiom is declared in the bundle. The only unchanged callee
the operation uses — the HTML entity decoder (`html.unescape`) — is declared
`opaque decode` in Lean and consumed by NO `_prop` axiom: the correctness proof
of the peel operation holds for an arbitrary `decode` (the `token ++ accumulator`
conservation clause follows from `List.take_append_drop`, independent of what
`decode` returns). `decode` is therefore an A-reference, not an A-consumed axiom;
its concrete behaviour is exercised against the real `html.unescape` by the
differential `conformance_check.py` (G-CONF).

There is nothing for G-AX to validate. Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (HTML entity decoder modeled "
          "as an opaque A-reference; concrete behaviour validated by G-CONF)")
    sys.exit(0)
