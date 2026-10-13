#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11885 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`combineByTable`) is the fast-delete combining pass of
`Collector.collect` (`django/db/models/deletion.py`):

    # post-patch (the fix):
    model_fast_deletes = defaultdict(list)
    for related in get_candidate_relations_to_delete(model._meta):
        ...
        related_model = related.related_model
        if self.can_fast_delete(related_model, from_field=field):
            model_fast_deletes[related_model].append(field)
            continue
        ...
    for related_model, related_fields in model_fast_deletes.items():
        batches = self.get_del_batches(new_objs, related_fields)
        for batch in batches:
            sub_objs = self.related_objects(related_model, related_fields, batch)
            self.fast_deletes.append(sub_objs)

The per-table grouping (the `combined`/`combineInto` fold) is modeled deeply and
is I/R-tagged. But the operation it abstracts — turning the selected
fast-deletable relations into the `self.fast_deletes` plan and ultimately into
SQL `DELETE ... WHERE col1 IN (...) OR colN IN (...)` statements — has observable
behavior ONLY against a live relational backend plus the full Collector / ORM
metadata machinery:

  * the combined-vs-separate query multiplicity (the whole point of the fix) is
    observed only by executing the compiled SQL and counting roundtrips, i.e.
    the F2P test's `assertNumQueries(2)` against real tables. There is no pure,
    DB-free way to produce the `(related_model, field)` candidate stream that
    drives the grouping.
  * reproducing the bug-triggering case (a model with two CASCADE foreign keys
    to the same table -- SecondReferrer.referrer and SecondReferrer.other_referrer
    both -> Referrer) requires standing up the model graph,
    get_candidate_relations_to_delete, can_fast_delete, the base managers, and a
    DB connection -- i.e. the F2P integration test itself
    (test_fast_delete_combined_relationships), not a pure R/I transliteration
    this gate can fuzz.

The abstraction the spec pins (a (table, column) stream -> one combined group per
table, `combined`) IS the modeled content; there is no DB-free oracle that
produces that stream to diff against. Per SPEC_GUIDE §0 / WORKER_PROMPT, when the
impl region's executable content is not reproducible as a pure R/I shadow, set
meta.json conf_skip=true and ship this status=skip stub. Soundness of the modeled
grouping is instead carried by G-VERIFY (the fold provably emits each target
table exactly once, accumulating all its columns) and G-DIFF (the prepatch, which
emits one singleton group per relation, fails exactly the `out = combined
relations` and `(out.map Prod.fst).Nodup` clauses on any input referencing one
table twice -- the un-combined-queries bug). This mirrors the django__django-13315
/ django__django-13089 precedent. See mapping.md §4 and refinement.md §A/§D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-11885 — the modeled do-block is "
          "the fast-delete combining pass of Collector.collect; the per-table "
          "grouping's observable (one combined DELETE ... OR ... query per "
          "table, counted by assertNumQueries) only manifests against a live DB "
          "plus the full Collector/ORM-metadata machinery, and the "
          "(related_model, field) candidate stream that drives it is not "
          "reproducible as a pure DB-free R/I shadow. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
