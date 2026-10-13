#!/usr/bin/env python
"""G-AX for django__django-16263 — SKIP STUB.

The bundle declares NO callee axioms. The one modeled decision (the
count/aggregate query-planning logic inside `Query.get_aggregation`) is modeled
DEEPLY: every quantity it reads is a field on the modeled carrier —
  * `containsAggregate` / `containsOverClause`  (the `getattr(...,True)` reads),
  * `refs`                                       (the patch-introduced `get_refs()`),
  * `postGroupFilter`                            (`where.split_having_qualify()[1:]`),
  * the query-level booleans (group_by tuple / sliced / distinct / combinator),
and the decision (subquery? + which carried clauses survive masking) is spelled
out directly in the Lean impl (`List.filter`, an accumulator `for` loop, list
membership). `correct_countPlan` closes by unfolding the impl and the two loop
folds; `#print axioms correct_countPlan` = [propext, Quot.sound]. There is no
`axiom <callee>_prop` for the proof to consume, so there is nothing to validate.

(The deep model — in particular `refs` ≙ `get_refs()` and the aggregate/window
flags — is validated against the post-patch behavior by G-CONF /
conformance_check.py as an A-reference.)
"""
import sys

print("status=skip no callee axioms declared (decision modeled deeply)")
sys.exit(0)
