#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-16032 — SKIPPED.

WHY conf_skip=true:

The gold patch has three hunks across two files
(`django/db/models/sql/query.py`, `django/db/models/fields/related_lookups.py`)
that together change ONE observable: the value of `Query.has_select_fields` for
a query carrying only annotation columns.

  1. query.py: `has_select_fields` becomes a stored class attribute
     (`has_select_fields = False`) instead of the derived property
     `bool(self.select or self.annotation_select_mask or self.extra_select_mask)`.
  2. query.py `set_values(...)`: `self.has_select_fields = True` (the flag is
     raised exactly when output columns are explicitly projected).
  3. related_lookups.py `RelatedIn.get_prep_lookup`: `clear_select_clause();
     add_fields([target], True)` -> `set_values([target])` (a
     behaviour-preserving co-change that routes the reduction through the same
     `set_values` that raises the flag).

The CHANGED behaviour the spec pins is the membership-narrowing guard
`if not self.rhs.has_select_fields:` (`lookups.py:427` for `pk__in` via `In`,
`related_lookups.py:93` for `book__in` via `RelatedIn`): a right-hand-side
subquery built from `annotate().alias()` (no explicit `.values()` projection)
must be reduced to a single output column.

The fix's only DISCRIMINATING observable is the queryset RESULT / generated SQL:

  * pre-patch the annotation-only subquery is NOT narrowed and compiles to a
    multi-column sub-select, raising
      django.db.utils.OperationalError: sub-select returns 10 columns - expected 1
  * post-patch it is narrowed to one column and the filter returns the right
    rows.

Both materialize only against a LIVE Django ORM + a real database: a configured
model layer (Book/Publisher with a 10-field model), the SQL compiler, and a
backend that actually executes the generated subquery. To observe "the subquery
was narrowed to one column" one must run the F2P integration tests themselves
(test_annotation_and_alias_filter_in_subquery,
test_annotation_and_alias_filter_related_in_subquery), not a DB-free
transliteration this gate could fuzz over >=1e5 inputs.

There is no DB-free, input-dependent R/I shadow to differential-test: the
modeled op is a 1-bit boolean decision over free inputs
(`narrow = not explicitlyProjected`); whether NOT narrowing actually changes the
returned rows / raises the error depends on the rest of the live query and the
database contents, which a pure shadow cannot reproduce. The shadow of the
boolean guard itself carries no information the spec (G-VERIFY) does not already
pin.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only
discriminating observable is a result/side effect on a live ORM + DB with no
DB-free R/I shadow, set meta.json conf_skip=true and ship this status=skip stub
(precedent: django__django-11265, django__django-11066, django__django-11451).
Soundness of the modeled behaviour is carried instead by G-VERIFY (the spec
provably forces `narrow = not explicitlyProjected`) and G-DIFF (the prepatch,
which restores the old derived disjunction
`select or annotation_select_mask or extra_select_mask`, fails exactly the
discriminating clause). See mapping.md section 4 and refinement.md section D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-16032 — the modeled op (the rhs "
          "membership-narrowing guard `not self.rhs.has_select_fields`, whose "
          "value the patch corrects from the derived disjunction "
          "`select or annotation_select_mask or extra_select_mask` to a stored "
          "flag set only by set_values) has as its only discriminating "
          "observable the queryset result / generated SQL on a live Django ORM "
          "+ database: pre-patch an annotation-only subquery compiles to a "
          "multi-column sub-select (OperationalError: sub-select returns N "
          "columns - expected 1); post-patch it is narrowed to one column. "
          "There is no DB-free, input-dependent R/I shadow to fuzz: the modeled "
          "op is a 1-bit boolean decision whose row-level consequence depends on "
          "live query + database state. conf_skip=true. Soundness covered by "
          "G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
