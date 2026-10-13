#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13315 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`selectEligible`) is the candidate-collection narrowing
of `apply_limit_choices_to_to_formfield`:

    # post-patch (the fix):
    formfield.queryset = formfield.queryset.filter(
        Exists(formfield.queryset.model._base_manager.filter(complex_filter)),
    )

The per-candidate emit (the `keep`/`keepMatching` fold) is modeled deeply and is
I/R-tagged. But the operation it abstracts — narrowing a `QuerySet` by either an
inner-join `complex_filter` (which duplicates a candidate once per matching
related row) or an `Exists()` correlated subquery (which emits it once iff a
match exists) — has observable behavior ONLY against a live relational backend:

  * the duplicate-vs-once multiplicity is produced by the SQL the ORM compiles
    (a JOIN vs an `EXISTS (...)` correlated subquery), executed against real
    related rows in real tables; there is no pure, DB-free way to produce the
    per-candidate witness multiplicity `witnesses` that drives both the bug and
    the fix.
  * reproducing the bug-triggering case (a `Q` spanning two joins, so a
    candidate matches via several related-row combinations) requires standing up
    the model graph, the related managers, and a DB connection — i.e. the F2P
    integration test itself (`test_limit_choices_to_no_duplicates`), not a pure
    R/I transliteration this gate can fuzz.

The abstraction the spec pins (`witnesses` -> once-or-zero, i.e. `keepMatching`)
IS the modeled content; there is no DB-free oracle that produces `witnesses` to
diff against. Per SPEC_GUIDE §0 / WORKER_PROMPT, when the impl region's
executable content is not reproducible as a pure R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. Soundness of the modeled
narrowing is instead carried by G-VERIFY (the fold provably emits each eligible
candidate exactly once) and G-DIFF (the prepatch, which emits
`List.replicate witnesses id`, fails exactly the `out = keepMatching rows` clause
on any candidate with witnesses >= 2 — the duplicate-options bug). This mirrors
the django__django-13089 precedent. See mapping.md §4 and refinement.md §B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-13315 — the modeled do-block is "
          "the narrowing of a QuerySet by a live-DB inner-join complex_filter vs "
          "an Exists() correlated subquery; the per-candidate witness "
          "multiplicity that drives the duplicate-vs-once behavior is not "
          "reproducible as a pure DB-free R/I shadow. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
