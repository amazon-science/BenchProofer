# refinement.md — django__django-16263

Maps every operation of `implementation_countPlan` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof consumes an
axiom property), **A-reference** (deep model validated == real callee by G-AX /
G-CONF), **I** (identical concrete op).

The modeled value is the count/aggregate query-planning decision inside
`Query.get_aggregation` (`django/db/models/sql/query.py`). The patch's other
hunks (`get_refs` on `Ref`/`BaseExpression`/`WhereNode`, the `summarize`
threading through `solve_lookup_type`/`build_filter`/`_add_q`/`Q.resolve_expression`,
and `refs_expression`'s `None` return) are the *support* the decision relies on;
their observable contribution to the FAIL_TO_PASS tests is entirely via the two
decisions modeled here (subquery? + which existing annotations survive).

| # | `implementation_countPlan` op | `patch.diff` / base counterpart | tag |
|---|---|---|---|
| 1 | `existing := st.anns.filter (!added && selected)` | `existing_annotations = { alias: annotation for alias,annotation in self.annotation_select.items() if alias not in added_aggregate_names }` (post-patch: keyed off `annotation_select`, not `annotations`) | R (dict→`List Ann`; `selected` ≙ membership in `annotation_select`) |
| 2 | `for a in existing do if a.containsAggregate \|\| a.containsOverClause then hasAgg := true` | `has_existing_aggregation = any(getattr(annotation,"contains_aggregate",True) or getattr(annotation,"contains_over_clause",True) for annotation in existing_annotations.values())` | A-reference (`containsAggregate`/`containsOverClause` ≙ the `getattr(...,True)` reads; deep-modeled, validated by G-CONF) |
| 3 | `... \|\| st.postGroupFilter` (folded into `needsSub`) | `... or any(self.where.split_having_qualify()[1:])` | A-reference (`postGroupFilter` ≙ truthiness of the post-WHERE split components; G-CONF) |
| 4 | `needsSub := groupByTuple \|\| isSliced \|\| (hasAgg \|\| postGroupFilter) \|\| distinct \|\| combinator` | `if (isinstance(self.group_by, tuple) or self.is_sliced or has_existing_aggregation or self.distinct or self.combinator):` | I (boolean disjunction, identical structure) |
| 5 | `mask := mask ++ (a.aliasName :: a.refs)` over `a.added` | `annotation_mask = set(); for name in added_aggregate_names: annotation_mask.add(name); annotation_mask \|= inner_query.annotations[name].get_refs()` | A-reference (`refs` ≙ `get_refs()`, a patch-introduced method modeled deeply; G-CONF) |
| 6 | `kept := if st.distinct then existing.map aliasName else (st.anns.filter (!added && mask.contains aliasName)).map aliasName` | the masking block is guarded by `if not inner_query.distinct:` — for a distinct query it is SKIPPED and the inner mask stays at `annotation_select` (every materialised existing clause survives); otherwise `inner_query.set_annotation_mask(annotation_mask)` *replaces* the mask, so a carried clause survives iff its alias is in the mask, whether or not it was materialised (an aliased non-selected clause referenced by an added aggregate is kept) | R (distinct guard ≙ `if not inner_query.distinct:`; set membership → `List.contains`; non-distinct filter on `!added`, NOT on `selected`; result projected to alias names) |
| 7 | `else return { useSubquery := false, keptExisting := [] }` | the `else:` branch (`outer_query = self; self.select = (); ...`) — no `AggregateQuery`, existing annotations inlined-and-masked so none survive as a kept *existing* alias | I (no-subquery branch ⟹ empty kept-existing set) |

## Notes on the deep models (no dead axioms)

- **`Ann.refs` ≙ `get_refs()`** is the heart of the fix (the method is *added*
  by the patch). It is modeled as a deep data field, not axiomatized — an
  A-reference validated by G-CONF (the conformance oracle computes the same
  alias-reference set). Per SPEC_GUIDE §3 / §0.7 the changed operation is never
  axiomatized.
- **`contains_aggregate` / `contains_over_clause` / `postGroupFilter`** are
  reads of unchanged state; modeled as deep boolean fields (A-reference), again
  not axioms (the proof needs no opaque callee property — `correct_countPlan`
  closes purely by unfolding the impl and the loop folds; `#print axioms` =
  `[propext, Quot.sound]`).

No `axiom <callee>_prop` is declared or consumed ⟹ G-AX is a skip stub.

## Prepatch correspondence (G-DIFF)

- `Solution_prepatch.lean` — the **base-commit subquery-decision** behavior:
  `existing_annotations` is computed from *every* non-added annotation and its
  mere non-emptiness (`or existing_annotations`) forces the wrapping subquery.
  Modeled as `existing := filter (!added)` (drops the `selected` guard) and
  `needsSub := ... || !existing.isEmpty`. On a plain aliased/scalar clause the
  spec demands `useSubquery = false`, but this impl returns `true`; the carried
  gold proof's `impl_eq` `split`/`rfl` step is then unprovable. FAILS G-VERIFY.
- `Solution_prepatch_2.lean` — the **base-commit masking** behavior: the inner
  query is masked to the full set of existing selected annotations
  (`inner_query.set_annotation_mask(self.annotation_select)`), with no pruning by
  what the added aggregates reference. Modeled as `kept := existing.map
  aliasName` (drops the `mask.contains` filter). On an unreferenced selected
  aggregate the spec drops it (`keptExisting = []`) but this impl keeps it; the
  carried gold proof's `impl_eq` `List.filter`/`rfl` step is unprovable. FAILS
  G-VERIFY.

Each prepatch isolates one independently-observable fixed behavior (subquery
decision vs. annotation pruning), matching the two distinct FAIL_TO_PASS
discriminators.

## patch.diff

`patch.diff` == gold patch verbatim (`patch_equals_gold: true`). Applies at
`base_commit` and resolves the FAIL_TO_PASS tests (G-RESOLVE).
