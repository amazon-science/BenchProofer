#!/usr/bin/env python
"""G-AX for django__django-15104 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function
(`MigrationAutodetector.only_relation_agnostic_fields`) is modeled DEEPLY. The
normalization performs only (a) the per-field relation test and (b) the removal
of the target-model entry from a related field's keyword mapping. The relation
test and each field's deconstruction are folded into the input representation
(`FieldDef`), and the removal is spelled out directly in the Lean impl as an
association-list filter. There is no `axiom <callee>_prop` for the proof to
consume, so there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
