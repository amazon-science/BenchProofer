#!/usr/bin/env python
"""G-AX for django__django-12774 — SKIP STUB.

The bundle declares NO callee axioms: the one modeled function (the field-name
acceptability guard of `QuerySet.in_bulk`) is modeled DEEPLY. The decision reads
only (a) whether `field_name` is the primary key, (b) the resolved field's own
`unique` flag (supplied as a model input observable, since `get_field` is an
unchanged callee and is not the fixed operation), and (c) membership of
`field_name` among the field names that are each the sole field of an
unconditional `UniqueConstraint` on the model — collected by filtering the
constraints to the unconditional single-field ones and projecting their one
field name. All of this is spelled out directly in the Lean impl (list
filter/map over the constraint records, an `Option`-free `headD`, and a list
membership test). There is no `axiom <callee>_prop` for the proof to consume, so
there is nothing to validate.

(The deep model IS validated against the post-patch behavior by G-CONF /
conformance_check.py.)
"""
import sys

print("status=skip no callee axioms declared (behavior modeled deeply)")
sys.exit(0)
