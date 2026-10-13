#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13109 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`validateExists`) is the existence test inside
`ForeignKey.validate`:

    # post-patch (the fix):
    qs = self.remote_field.model._base_manager.using(using).filter(
        **{self.remote_field.field_name: value}
    )
    qs = qs.complex_filter(self.get_limit_choices_to())
    if not qs.exists():
        raise exceptions.ValidationError(...)

The per-record match (the `matchesTarget`/`existsMatch` fold) is modeled deeply
and is I/R-tagged. But the operation it abstracts — building a `QuerySet` from a
chosen manager and asking `.exists()` after `.filter(**{field_name: value})` —
has observable behavior ONLY against a live relational backend:

  * which rows the existence test ranges over is produced by the SQL the ORM
    compiles for the chosen manager (`_default_manager.get_queryset()` may inject
    a custom `WHERE archived = False` clause; `_base_manager.get_queryset()` does
    not), executed against real stored rows in a real table; there is no pure,
    DB-free way to produce a manager's row-visibility (`hidden`) that drives both
    the bug and the fix.
  * reproducing the bug-triggering case (a matching row the default manager
    filters out — an `archived=True` row whose pk is referenced) requires
    standing up the model graph, a custom default manager, and a DB connection
    with the row persisted — i.e. the F2P integration tests themselves
    (`test_FK_validates_using_base_manager`,
    `test_validate_foreign_key_to_model_with_overridden_manager`), not a pure
    R/I transliteration this gate can fuzz.

The abstraction the spec pins (`hidden` -> included only in the complete view,
i.e. `existsMatch` over the full row set) IS the modeled content; there is no
DB-free oracle that produces the manager's row-visibility to diff against. Per
SPEC_GUIDE §0 / WORKER_PROMPT, when the impl region's executable content is not
reproducible as a pure R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub. Soundness of the modeled existence test is instead carried by
G-VERIFY (the fold provably consults every row, hidden or not, so the result is
true iff any complete-collection record matches) and G-DIFF (the prepatch, which
consults only non-hidden rows `matchesTarget target r && !r.hidden`, fails
exactly the `out = existsMatch target rows` clause on any input whose only
matching row is hidden — the archived-target bug). This mirrors the
django__django-13315 and django__django-13089 precedents. See mapping.md §4 and
refinement.md §B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-13109 — the modeled do-block is "
          "the existence test of ForeignKey.validate, building a QuerySet from "
          "either the default manager (which a custom view filter may narrow) or "
          "the base manager (complete row set) and asking .exists(); the "
          "per-row visibility (`hidden`) that drives the validates-vs-raises "
          "behavior is not reproducible as a pure DB-free R/I shadow. "
          "conf_skip=true. Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
