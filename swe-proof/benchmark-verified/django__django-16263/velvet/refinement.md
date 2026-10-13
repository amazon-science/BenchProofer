# refinement.md — django__django-16263

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `countQueryShape` `do` block, the deep `referencedNames` model, and the
pure decision functions) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses an axiom's `ensures`),
**A-reference** (deep model validated == real callee by G-AX), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A-reference leg by **G-AX** (`axiom_check.py`); the narrative by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

Claim: any impl verifying against this frozen spec, refined per the map below,
makes `Query.get_aggregation` take the same subquery decision and produce the
same retained-annotation set as the gold patch on the tested query shapes, so
the harness resolves.

## Scope

The modeled, F2P-discriminating kernel is `Query.get_aggregation`
(`query.py:438`). The four tests of `AggregateAnnotationPruningTests` observe
exactly two outcomes of it: (D1) whether the count is wrapped in a nested query
(`sql.count("select")` == 1 or 2), and (D2) which annotation aliases appear in
the produced SQL (`assertNotIn` / `assertEqual(...count(alias), 2)`). The
`summarize` plumbing (query_utils/build_filter/_add_q/solve_lookup_type/
refs_expression hunks) is not exercised by these tests (mapping.md §5); it is
behaviour-neutral here and left out of the spec.

## A. The nesting decision (D1) — `has_existing_aggregation`

Gold hunks (`query.py:444-456`, `466-473`, `485-491`):
```
- existing_annotations = [annotation for alias, annotation in self.annotations.items()
-                         if alias not in added_aggregate_names]
+ existing_annotations = {alias: annotation
+   for alias, annotation in self.annotation_select.items()
+   if alias not in added_aggregate_names}
+ has_existing_aggregation = any(getattr(a,"contains_aggregate",True)
+     or getattr(a,"contains_over_clause",True) for a in existing_annotations.values()
+   ) or any(self.where.split_having_qualify()[1:])
  if (isinstance(self.group_by, tuple) or self.is_sliced
-     or existing_annotations or self.distinct or self.combinator):
+     or has_existing_aggregation or self.distinct or self.combinator):
```

| # | Solution.lean impl op (`countQueryShape`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `annos : List Annotation` (`name`,`selected`,`isAggregate`,`isWindow`) | `self.annotations` / `self.annotation_select` projected | R | mapping.md §2: `selected ↔ alias ∈ annotation_select`; `isAggregate ↔ getattr(...,"contains_aggregate",True)`; `isWindow ↔ getattr(...,"contains_over_clause",True)`. |
| A2 | `names := added.map (·.name)` | `added_aggregate_names` | R | the set of summary aliases (`str` ↔ `String`). |
| A3 | `existing := annos.filter (isExisting names)` | the `{alias: annotation … if alias not in added_aggregate_names}` over `annotation_select` | I (under R) | `isExisting names a = a.selected && !(names.contains a.name)` ↔ "in the visible SELECT set AND not an added name". The switch from `self.annotations` to `self.annotation_select` IS the `selected` filter — the discriminator for the aliased test. |
| A4 | `priorAgg := existing.any (·.isAggregate ∨ ·.isWindow) ∨ havingFilter` | `has_existing_aggregation = any(contains_aggregate or contains_over_clause …) or any(split_having_qualify()[1:])` | I + R | element-wise disjunction transliterated; `havingFilter` is the R-input for `any(self.where.split_having_qualify()[1:])` (mapping.md §3.2). |
| A5 | `nesting := groupByTuple ∨ isSliced ∨ priorAgg ∨ distinct ∨ combinator` | the `if (... or has_existing_aggregation or ...)` test | I | identical 5-way disjunction; the four structural triggers are R-inputs. |

Discriminating content of D1: the trigger is no longer the *presence* of any
prior annotation but the presence of a prior annotation that *aggregates or
windows* (or a HAVING/QUALIFY filter), restricted to *selected* annotations.
`Solution_prepatch.lean` reproduces the pre-patch "any prior annotation present"
predicate (`priorAgg := !existing.isEmpty`) and **fails** the `needsNesting`
postcondition (G-DIFF, ensures_2). It kills `test_non_aggregate_annotation_pruned`
(name_lower is non-aggregate ⇒ must NOT nest) and
`test_unused_aliased_aggregate_pruned` (aliased ⇒ not selected ⇒ must NOT nest).

## B. The retained-annotation set (D2) — the annotation mask

Gold hunks (`query.py:485-503` nesting branch — mask-narrowing guarded by
`if not inner_query.distinct:`; `534-547` else branch):
```
  inner_query.set_annotation_mask(self.annotation_select)
  ...
  if not inner_query.distinct:
      ...
+     annotation_mask = set()
+     for name in added_aggregate_names:
+         annotation_mask.add(name)
+         annotation_mask |= inner_query.annotations[name].get_refs()
+     inner_query.set_annotation_mask(annotation_mask)
  ...
+ if existing_annotations:
+     replacements = {Ref(alias, annotation): annotation for …existing…}
+     for name in added_aggregate_names:
+         self.annotations[name] = self.annotations[name].replace_expressions(replacements)
+     self.set_annotation_mask(added_aggregate_names)
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `referencedNames : Expr → List String` (+ `referencedNamesList`) | `BaseExpression.get_refs` / `Ref.get_refs` (`expressions.py:408,1176`; `where.py:230`) | A-reference + I | the new `get_refs` is modeled **deeply**: `reference s ↦ [s]` ↔ `Ref.get_refs = {self.refs}`; `composite es ↦ ⋃` ↔ `BaseExpression.get_refs` unions over `get_source_expressions()`. The recursion ops are I (concrete); equality of the deep model to the real `get_refs` (as sets) is the **A-reference** G-AX validates. No consumed `get_refs` axiom. |
| B2 | `maskFold : List Added → List String` (backward `while` fold) | `for name in added_aggregate_names: mask.add(name); mask |= …get_refs()` | I | `maskFold (a :: rest) = (a.name :: referencedNames a.expr) ++ maskFold rest` ↔ the loop accumulating `{name} ∪ get_refs(annotations[name])`. Front-recursive fold + one drop-step lemma (`maskFold_drop_step`). |
| B3 | `keptNames nesting distinct annos added := if nesting then (if distinct then added.map (·.name) ++ (annos.filter (isExisting …)).map (·.name) else maskFold added) else added.map (·.name)` | nesting ∧ ¬distinct branch `set_annotation_mask(annotation_mask)` (the narrowing is inside `if not inner_query.distinct:` — `query.py:486` post-patch); nesting ∧ distinct: the narrowing is SKIPPED and the baseline `inner_query.set_annotation_mask(self.annotation_select)` stands, i.e. every selected annotation (added + existing selected) is retained; else branch `set_annotation_mask(added_aggregate_names)` (when `existing_annotations`) | I + R | nesting ∧ ¬distinct ⇒ retained set = added ∪ refs; nesting ∧ distinct ⇒ retained set = added ∪ existing-selected (mask-narrowing suppressed because clearing the select clause can alter which rows are duplicate-collapsed); non-nesting ⇒ retained set = added names (prior ones inlined away by `replace_expressions` and masked out). Compared as **sets** (mapping.md §2). |

Discriminating content of D2: when nesting WITHOUT query-level distinct, only
the added names and what they *reference* survive — prior annotations not
referenced are pruned. When nesting WITH query-level distinct the gold code
skips the narrowing (`if not inner_query.distinct:` — query.py:486 post-patch;
clearing the select clause can alter results if distinct is used), so the
baseline `set_annotation_mask(self.annotation_select)` stands and every
selected prior annotation survives — `keptNames` mirrors this with its
`if distinct then names ++ existing else maskFold added` branch.
`Solution_prepatch_2.lean` reproduces the pre-patch "keep every existing
annotation" behaviour UNCONDITIONALLY (`kept := names ++ existing.map
(·.name)` even when not distinct) and **fails** the `keptNames` postcondition
(G-DIFF, ensures_1) on non-distinct nesting shapes. It kills
`test_unreferenced_aggregate_annotation_pruned` (authors_count unreferenced by
`__count` ⇒ must be pruned from the subquery). `test_referenced_aggregate_
annotation_kept` (PASS) guards that a *referenced* prior annotation
(`Avg("authors_count")` ⇒ `referencedNames = ["authors_count"]`) is **kept** —
satisfied by both spec and prepatch_2, so it is correctly non-discriminating.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation genuinely *added* by the patch —
the recursive reference collector `get_refs` — is modeled **deeply**
(`referencedNames`, B1, A-reference + I), not hidden behind an axiom about the
function under change. There is **no consumed axiom** in this bundle: the
nesting predicate and mask are pure functions over observable R-inputs
(`groupByTuple`, `isSliced`, `distinct`, `combinator`, `havingFilter`, and each
annotation's `selected`/`isAggregate`/`isWindow`), and the only callee modeled
(`get_refs`) is an A-reference checked by G-AX.

## D. verify(Solution) ⇒ resolved

`countQueryShape` verifies only if (D1) its `needsNesting` equals the refined
predicate — restricted to *selected* annotations that *aggregate/window*, plus
the HAVING/QUALIFY filter — and (D2) its `keptNames` equals `added ∪ refs` when
nesting without query-level distinct, `added ∪ existing-selected` when nesting
with it (the `if not inner_query.distinct:` guard), else just the added
names. By R (the projections of `self`, set-vs-list
of aliases) these equal the gold `get_aggregation`'s subquery decision and
inner/outer annotation mask. By G-AX the deep model `referencedNames` equals the
real `get_refs` (A-reference). By G-CONF the R/I transliteration of the decision
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). Trust points: A-reference soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).
