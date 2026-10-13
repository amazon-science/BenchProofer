# RELAXED_LEAKAGE — django__django-16263 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`, via
the `relaxed_leakage` meta flag + this file). This bundle's own P2 audit
(`verdict.md`, Defect 1 + Sub-review 3) reached exactly this disposition —
"despite being substantively RELAXED, this bundle records `G-LEAK.status =
'pass'` … should be re-dispositioned pass→relaxed and documented. Core
soundness is unaffected." This file plus the meta flag IS that prescribed
correction.

## The mismatch

The `problem_statement` ("Strip unused annotations from count queries") asks
ONLY for an unconditional strip of annotations "not referenced by filters,
other annotations or ordering", illustrated with
`Book.objects.annotate(Count('chapters')).count()`. Token scan of the public
text: aggregate = 0 (as a discriminator; `Count` appears only as the example
annotation), window = 0, having = 0, qualify = 0, distinct = 0,
combinator = 0, subquery/nested = 0.

The gold fix (`django/db/models/sql/query.py`, `get_aggregation`) actually
implements two conditional rules the public text never states:

1. **D1 — the nesting discriminator** (`has_existing_aggregation`,
   query.py:449-456 post-patch): a subquery is forced only by a *selected*
   prior annotation that itself aggregates (`contains_aggregate`) or is
   windowed (`contains_over_clause`), or by a HAVING/QUALIFY filter — the
   mere presence of a prior annotation no longer nests.
2. **D2' — the distinct guard on mask-narrowing** (`if not
   inner_query.distinct:` at query.py:486 post-patch): when the query
   collapses duplicate rows (query-level `.distinct()`) forces the nested
   count, the mask-narrowing to `added ∪ get_refs` is SKIPPED — the baseline
   `set_annotation_mask(self.annotation_select)` stands and every selected
   prior annotation survives in the inner query (narrowing the select set
   could change which rows are duplicate-collapsed).

## The leaking lines (quoted from the spec view)

- "whether it itself summarises rows (`isAggregate`) or is a windowed
  expression (`isWindow`)" (the `Annotation` structure docstring) — facet D1.
- "A nested query is forced by a prior alias entry only when that entry
  itself summarises rows or is windowed — or when a row-summarising filter is
  present." (the `anyPriorAggregate`/`needsNesting` docstring) — facet D1.
- "When the count is nested but the query DOES collapse duplicate rows
  (`distinct`): pruning is suppressed … every visible prior entry is retained
  alongside the added names." (the `keptNames` docstring) plus the
  `if distinct then … else maskFold added` branch of `keptNames` — facet D2'.

A reader of the spec view alone can reconstruct the gold's exact nesting
condition and mask logic; a reader of the `problem_statement` alone cannot.

## Why the leak is unavoidable

**Facet D1.** The F2P set (`AggregateAnnotationPruningTests`) observes the
nesting decision directly: `test_non_aggregate_annotation_pruned` (a
non-aggregate prior annotation must NOT nest) and
`test_unused_aliased_aggregate_pruned` (an `.alias()`-ed, non-selected prior
aggregate must NOT nest). The bundle's own `Solution_prepatch.lean` — the
natural PS-consistent "any prior annotation present" rule — fails the
`needsNesting` postcondition (G-DIFF, ensures_2). So a faithful spec MUST pin
the aggregate/window/HAVING discriminator, yet that discriminator is absent
from the `problem_statement`. Faithful + non-leaking is provably impossible —
the textbook RELAXED pattern.

**Facet D2'.** The G-PANEL-2 (faithfulness) audit of the previous bundle
revision produced a concrete in-container repro on the REAL patched Django
(base 321ecb40 + gold): `User.objects.annotate(name_lower=
Lower('username')).distinct()` reaching `get_aggregation` with
`added_aggregate_names=['__count']` retains `name_lower` in the inner mask,
while the same query without `.distinct()` prunes it — "the distinct-vs-not
difference is exactly the `if not inner_query.distinct:` guard the spec
omits" (panel-2 verdict, 2026-08-02). A spec that omits the guard is
UNFAITHFUL (it was failed for exactly that); a spec that pins it must
describe conditional retention under duplicate-row collapsing — behaviour the
`problem_statement` (which demands an unconditional strip and never mentions
distinct) does not contain. Pinning it is mandatory for faithfulness, and it
is not PS-derivable: the same mismatch pattern as D1.

The D2 core (mask = added names ∪ referenced names, in the non-distinct case)
IS PS-derivable ("stripping out any annotations that are not referenced by
filters, other annotations or ordering") and is not part of this relaxation.

## Core soundness is intact

- **G-VERIFY**: `Solution.lean` (with the distinct-guarded `keptNames`)
  verifies via `scripts/lean_verify.sh`, exit 0; no sorry/axioms.
- **G-DIFF**: both prepatch twins share the strengthened spec byte-identically
  (`same_spec` = True) and still FAIL verification for the right reasons:
  `Solution_prepatch.lean` (D1 "any prior present" rule) fails ensures_2;
  `Solution_prepatch_2.lean` (keep-all-existing even when not distinct) fails
  ensures_1.
- **G-CONF**: `conformance_check.py` — with the oracle now transcribing the
  real `if not inner_query.distinct:` guard and the shadow transliterating the
  strengthened `keptNames` — re-run in-container against the real patched
  `get_aggregation` semantics: 100000 fuzzed shapes (seed 16263),
  0 disagreements, rc 0.
- **G-AX**: unchanged (the `referencedNames` deep model and `axiom_check.py`
  are untouched by this repair).
- The relaxation concerns ONLY the secondary no-leakage property, for the two
  documented facets above.
