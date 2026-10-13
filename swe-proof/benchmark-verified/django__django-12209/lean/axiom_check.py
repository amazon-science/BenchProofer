#!/usr/bin/env python
"""G-AX skip stub for django__django-12209.

No consumed callee axiom is declared in the bundle. The modeled value is a pure
routing decision computed inside `Model._save_table` from five booleans the
method already holds (mapping.md). The patch is a boolean conjunction
(`not raw and …`); every operation is expressible in Lean boolean algebra and is
transliterated op-for-op (refinement.md — all I / boolean-R rows). The
downstream callees (`_do_update`, `_do_insert`, `get_pk_value_on_save`, …) lie
outside the modeled decision and are summarized by the input booleans, so none is
axiomatized.

There is therefore nothing for G-AX to validate; the boolean decision is checked
end-to-end against the gold expression by the differential `conformance_check.py`
(G-CONF). Exit 0 with status=skip.
"""
import sys

if __name__ == "__main__":
    print("status=skip no consumed callee axioms (pure boolean routing decision "
          "modeled deeply; validated by G-CONF)")
    sys.exit(0)
