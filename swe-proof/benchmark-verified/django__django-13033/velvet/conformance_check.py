#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-13033 — SKIPPED.

WHY conf_skip=true:

The modeled `do` block (`orderingExpansionDecision`) is the boolean guard of
`SQLCompiler.find_ordering_name` that decides whether to append a related
model's default ordering for an ordering lookup:

    # post-patch (the fix):
    if (
        field.is_relation and
        opts.ordering and
        getattr(field, 'attname', None) != pieces[-1] and
        name != 'pk'
    ):
        ...expand the related model's default ordering...

The guard's four conjuncts are modeled deeply and are I/R-tagged. But the
operands that drive the discriminating conjunct — `field.is_relation`,
`opts.ordering`, `getattr(field, 'attname', None)`, `pieces` (the split lookup
path), and `name` — are produced ONLY by resolving a lookup against a live model
graph:

  * `field` and its `attname` come from `self._setup_joins(pieces, opts, alias)`,
    which walks the model's field metadata and the query's join machinery; there
    is no pure, DB-free way to produce a relation field whose `attname` equals
    the terminal lookup segment (the case that distinguishes the bug from the
    fix) without standing up the ORM model classes, their `_meta`, and the
    query's `alias_map`.
  * reproducing the bug-triggering case (a self-referential FK ordered by its
    stored `<rel>_id` attribute, so `attname == pieces[-1]` while
    `attname != name`) requires the model graph and a compiled SQL query — i.e.
    the F2P integration test itself (`test_order_by_self_referential_fk`), not a
    pure R/I transliteration this gate can fuzz.

The abstraction the spec pins (the four-conjunct guard with the terminal-segment
comparison) IS the modeled content; there is no DB-free oracle that produces the
resolved `(field, attname, pieces, name)` tuple to diff against. Per
SPEC_GUIDE §0 / WORKER_PROMPT, when the impl region's executable content is not
reproducible as a pure R/I shadow, set meta.json conf_skip=true and ship this
status=skip stub. Soundness of the modeled guard is instead carried by
G-VERIFY (the guard provably equals the terminal-segment formulation) and
G-DIFF (the prepatch, which compares `attname` against the whole joined `name`,
fails exactly the postcondition on any multi-segment lookup that ends at the
field's own stored attribute — the spurious-expansion bug). This mirrors the
django__django-13315 precedent. See mapping.md §4 and refinement.md §B.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-13033 — the modeled do-block is "
          "the relation-default-ordering guard of find_ordering_name; its "
          "operands (field.is_relation, opts.ordering, field.attname, the split "
          "lookup pieces, and name) are resolved only against a live ORM model "
          "graph via _setup_joins, so the bug-vs-fix discriminator is not "
          "reproducible as a pure DB-free R/I shadow. conf_skip=true. Soundness "
          "covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
