#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-17084 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`wrappedEvaluationDecisionM`) is the boolean guard of
`Query.get_aggregation` (django/db/models/sql/query.py:449-457) that decides
whether the aggregation must be evaluated inside a wrapping outer (sub)query:

    # post-patch (the fix), query.py:449-457:
    if (
        isinstance(self.group_by, tuple)
        or self.is_sliced
        or has_existing_aggregation
        or refs_subquery
        or refs_window            # <-- the added disjunct
        or qualify
        or self.distinct
        or self.combinator
    ):
        ...evaluate the aggregation inside a wrapping subquery...

where the new accumulator is (query.py:406, 423-426):

    refs_window = False
    ...
    refs_window |= any(
        getattr(self.annotations[ref], "contains_over_clause", True)
        for ref in aggregate.get_refs()
    )

The added disjunct is modeled deeply and is I/R-tagged. But the operands that
drive the discriminating disjunct — for each requested aggregate, the resolved
`aggregate.get_refs()` set and the `contains_over_clause` flag of each referenced
annotation in `self.annotations` — are produced ONLY by resolving aggregate
expressions against a live ORM query:

  * `aggregate = aggregate_expr.resolve_expression(self, allow_joins=True,
    reuse=None, summarize=True)` (query.py:409-411) walks the model's annotation
    graph and field metadata; `aggregate.get_refs()` and
    `self.annotations[ref].contains_over_clause` only exist once that resolution
    has stood up the model classes, their annotations, and the query state.
  * reproducing the bug-triggering case (an aggregate such as
    `Sum("cumul_DJR")` that references an annotation built from a `Window(...)`
    expression — so a referenced annotation's `contains_over_clause` is `True`
    while none of the pre-existing structural conditions hold) requires the model
    graph and a resolved query — i.e. the F2P integration test
    `test_referenced_window_requires_wrapping` itself, not a pure R/I
    transliteration this gate can fuzz.

The abstraction the spec pins (the OR of the prior structural conditions and the
per-aggregate window-reference fold) IS the modeled content; there is no DB-free
oracle that produces the resolved per-aggregate window flags to diff against.
Per SPEC_GUIDE §0 / WORKER_PROMPT, when the impl region's executable content is
not reproducible as a pure R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub. Soundness of the modeled guard is instead carried by G-VERIFY
(the guard provably equals `priorConditions || referencesWindow aggregates`) and
G-DIFF (the prepatch, which omits the window disjunct and so never accumulates a
window flag, fails the loop invariant `acc = referencesWindow (aggregates.drop i)`
exactly when some aggregate references a window-using annotation — the
missing-wrapping bug). This mirrors the django__django-13033 / django__django-13315
precedent. See mapping.md §4 and refinement.md §D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-17084 — the modeled do-block is "
          "the wrapping-subquery guard of Query.get_aggregation; its "
          "discriminating operands (per requested aggregate, the resolved "
          "get_refs() set and each referenced annotation's contains_over_clause "
          "flag) are produced only by resolving aggregate expressions against a "
          "live ORM query graph, so the bug-vs-fix discriminator is not "
          "reproducible as a pure DB-free R/I shadow. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
