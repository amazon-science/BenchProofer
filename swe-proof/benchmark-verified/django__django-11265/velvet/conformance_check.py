#!/usr/bin/env python3
"""G-CONF differential conformance for django__django-11265 — SKIPPED.

WHY conf_skip=true:

The gold patch has two hunks in `django/db/models/sql/query.py`:

  1. split_exclude: the inner subquery built to rewrite a negated N-to-many
     lookup must inherit the originating query's filtered-relation registry:
         query = Query(self.model)
         query._filtered_relations = self._filtered_relations   # <-- the fix
         query.add_filter(filter_expr)
     Without it, a lookup that references a named filtered relation cannot be
     resolved in the subquery and `names_to_path` raises FieldError.

  2. trim_start: the leading-join trimming guard must also refuse to trim a join
     introduced by a named filtered relation (which carries its own filter):
         first_join = self.alias_map[lookup_tables[trimmed_paths + 1]]
         if first_join.join_type != LOUTER and not first_join.filtered_relation:
     Without the `and not first_join.filtered_relation` conjunct, the inner join
     is trimmed and its filter is silently dropped, returning the wrong rows.

The CHANGED behaviours the spec pins are observable ONLY as the queryset RESULT
(the rows returned by `Author.objects.annotate(book_alice=FilteredRelation(...))
.exclude(book_alice__isnull=False)`) and, at site 1, a FieldError side effect.
Both materialize only against a LIVE Django ORM + a real database: a configured
model layer, the SQL compiler, and a populated database against which the
generated subquery actually runs.

There is no DB-free, input-dependent R/I shadow to differential-test:

  * Site 1's modeled op is a registry copy (`out = outerRelations`). Its only
    consequence — a lookup resolving instead of raising FieldError — is a
    property of the UNCHANGED downstream resolver (`names_to_path`,
    `solve_lookup_type`) executing against a live `Query`, not a value this gate
    computes. To observe "the annotation resolved in the subquery" one must run
    the F2P integration test itself (`test_with_exclude`), not a pure
    transliteration fuzzable over >=1e5 inputs.
  * Site 2's modeled op is a 2-bit boolean decision over two free inputs
    (`preservesUnmatchedRows`, `carriesOwnFilter`). Whether trimming that join
    actually changes the returned rows depends on the rest of the live query and
    the database contents, which a pure shadow cannot reproduce. The shadow of
    the boolean guard itself carries no information the spec (G-VERIFY) does not
    already pin.

Per SPEC_GUIDE section 0 / WORKER_PROMPT: when the modeled op's only
discriminating observable is a result/side effect on a live ORM + DB with no
DB-free R/I shadow, set meta.json conf_skip=true and ship this status=skip stub
(precedent: django__django-11451, django__django-11179). Soundness of the
modeled behaviour is carried instead by G-VERIFY (the spec provably forces both
`out = outerRelations` with every inherited name resolving, and the full
two-conjunct trim guard) and G-DIFF (the two prepatches, each reverting one site,
fail exactly the discriminating clause). See mapping.md section 4 and
refinement.md sections C/D.
"""
import sys


def main():
    print("G-CONF status=skip: django__django-11265 — the two modeled ops "
          "(the inner subquery inheriting the filtered-relation registry in "
          "split_exclude, and the strengthened leading-join trim guard in "
          "trim_start) have as their only discriminating observable the "
          "queryset result / FieldError on a live Django ORM + database. There "
          "is no DB-free, input-dependent R/I shadow to fuzz: site 1's effect "
          "is a property of the unchanged downstream resolver running against a "
          "live query, and site 2 is a 2-bit boolean decision whose row-level "
          "consequence depends on live query + database state. conf_skip=true. "
          "Soundness covered by G-VERIFY + G-DIFF.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
