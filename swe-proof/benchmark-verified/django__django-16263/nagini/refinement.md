# refinement.md — django__django-16263

The operation-by-operation correspondence between `model.py`'s implementation
(the two contracted decisions `existing_summary_forces_derived` and
`inner_column_kept`, plus the deep `collect_refs` fold) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(the proof uses an axiom's `Ensures`), **A-reference** (a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are **no consumed axioms**. The one non-R/I element is the **A-reference**
deep model `collect_refs` (== the new `get_refs()`), validated by G-AX.

## A. Decision #1 — the subquery wrapping decision (`get_aggregation`)

Gold hunk (`django/db/models/sql/query.py`):
```
- existing_annotations = [ annotation
-     for alias, annotation in self.annotations.items()
+ existing_annotations = { alias: annotation
+     for alias, annotation in self.annotation_select.items()
      if alias not in added_aggregate_names ]
+ has_existing_aggregation = any(
+     getattr(annotation, "contains_aggregate", True)
+     or getattr(annotation, "contains_over_clause", True)
+     for annotation in existing_annotations.values()
+ ) or any(self.where.split_having_qualify()[1:])
  ...
  if ( isinstance(self.group_by, tuple) or self.is_sliced
-      or existing_annotations
+      or has_existing_aggregation
       or self.distinct or self.combinator ):
```

This gold decision changes **two orthogonal axes** that must BOTH be modelled:
* **Axis 1 (source):** the carrier is built from `self.annotation_select`
  (SELECTED annotations) instead of `self.annotations` (ALL annotations,
  including alias-only ones). Modelled by the per-column `selected` bit.
* **Axis 2 (predicate):** an entry forces the wrapping only when it carries an
  aggregate / over-clause (or a retained HAVING/QUALIFY filter does), instead of
  merely existing. Modelled by the per-column `summ` (summary) bit + `filter_summary`.

| # | model.py impl op (`existing_summary_forces_derived`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A0 | param `selected: List[int]`, `selected[k] != 0` ⇔ existing annotation k is in `annotation_select` | the dict source `self.annotation_select.items()` (vs the old `self.annotations.items()`) | R | one observed bit per existing annotation = whether it is a SELECTED annotation; an alias-only annotation has `selected[k]==0` and never participates. Grounded in `add_annotation(select=…)` (mapping.md §2, axiom_check `_selected_bit`). |
| A1 | param `summ: List[int]`, `summ[k] != 0` ⇔ existing annotation k carries an aggregate or over-clause | each annotation read via `getattr(...,"contains_aggregate",True) or getattr(...,"contains_over_clause",True)` | R | one observed bit per existing annotation = the disjunction of the two boolean attributes (mapping.md §2). |
| A2 | param `filter_summary: int`, `!= 0` ⇔ a retained post-WHERE filter exists | `any(self.where.split_having_qualify()[1:])` | R | one observed bit: a retained HAVING/QUALIFY part. |
| A3 | the loop sets `found` = `any_selected_summary(ToSeq(selected), ToSeq(summ))` (some index with BOTH bits set) | the `any(... contains_aggregate ... or ... contains_over_clause ... for annotation in existing_annotations.values())` generator, where `existing_annotations` is built from `annotation_select` | I (over the R-refined carriers) | both are "does any SELECTED existing annotation carry aggregation"; the source-filter (`annotation_select`) is exactly the `selected` conjunct, the attribute disjunction is the `summ` conjunct. |
| A4 | `return found or filter_summary != 0` | `has_existing_aggregation = any(...) or any(self.where.split_having_qualify()[1:])`, consumed in the wrapping `if` | I | the disjunction that decides the wrapping; the other `if` disjuncts (`group_by`/`is_sliced`/`distinct`/`combinator`) are independent and out of scope (mapping.md §1). |

The discriminating content lives in
`Result() == (any_selected_summary(selected, summ) or filter_summary != 0)`,
covering both axes:

* **Axis 2 (predicate)** — a SELECTED non-aggregate annotation must NOT force the
  wrapping. The pre-patch used the *mere presence* of any SELECTED annotation;
  `model_prepatch.py` reproduces that (`any(selected[k] != 0)`) and **fails** the
  postcondition on `selected=[1], summ=[0]` (a lone selected non-aggregate
  column) — exactly `test_non_aggregate_annotation_pruned` (1 SELECT expected,
  pre-patch wraps → 2) (G-DIFF, variant 1).
* **Axis 1 (source)** — an ALIAS-ONLY aggregate must NOT force the wrapping. The
  pre-patch built the carrier from `self.annotations` (ALL annotations);
  `model_prepatch_3.py` reproduces that (`any(summ[k] != 0)`, ignoring `selected`)
  and **fails** the postcondition on `selected=[0], summ=[1]` (an alias-only
  aggregate) — exactly `test_unused_aliased_aggregate_pruned` (1 SELECT expected,
  pre-patch wraps → 2) (G-DIFF, variant 3).

## B. Decision #2 — the inner-query annotation mask (`get_aggregation`)

Gold hunk (`django/db/models/sql/query.py`):
```
+ # Mask existing annotations that are not referenced by
+ # aggregates to be pushed to the outer query.
+ annotation_mask = set()
+ for name in added_aggregate_names:
+     annotation_mask.add(name)
+     annotation_mask |= inner_query.annotations[name].get_refs()
+ inner_query.set_annotation_mask(annotation_mask)
```
(replacing the pre-patch `inner_query.set_annotation_mask(self.annotation_select)`
which kept every annotation).

| # | model.py impl op (`inner_column_kept`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `added: List[int]` (codes of pushed-out summaries) | `added_aggregate_names` | R | alias string ↔ code (mapping.md §2). |
| B2 | first loop: `in_added` = `seq_contains(ToSeq(added), alias)` | `annotation_mask.add(name)` for `name in added_aggregate_names` | I (over R) | "alias is one of the pushed-out summary names". |
| B3 | `collect_refs(ToSeq(ref_tree))` (the references reachable from the pushed-out summary) | `inner_query.annotations[name].get_refs()` | A-reference | the new reference-gatherer is modelled DEEPLY as `collect_refs`; G-AX asserts `set(collect_refs(flatten(tree))) == real get_refs(tree)` over 12 boundary + 5000 fuzz trees, with `Ref` as a LEAF on both sides (mapping.md §3.1). No consumed `get_refs` axiom. |
| B4 | second loop: `in_refs` = `seq_contains(collect_refs(ToSeq(ref_tree)), alias)` | `annotation_mask |= ...get_refs()` | I (over R) + A-reference | union-membership of the gathered references; membership == real-set membership by B3. |
| B5 | `return in_added or in_refs` | `set_annotation_mask(annotation_mask)` keeps exactly `added_aggregate_names ∪ ⋃ get_refs()` | I | an alias survives the inner selection iff it is pushed-out or referenced. |

The discriminating content — an UNREFERENCED pre-existing aggregate annotation
must be pruned — lives in
`Result() == (seq_contains(added, alias) or seq_contains(collect_refs(ref_tree), alias))`.
The pre-patch kept ALL existing annotations; `model_prepatch_2.py` reproduces
that (`return True`) and **fails** the postcondition when `alias` is neither
pushed-out nor referenced — exactly `test_unreferenced_aggregate_annotation_pruned`
(`authors_count` must NOT be in the inner SQL; `Count("*").get_refs() == set()`).
For the kept case, `test_referenced_aggregate_annotation_kept`,
`Avg(Ref("authors_count")).get_refs() == {"authors_count"}` ⇒ `in_refs` True ⇒
`authors_count` retained (G-DIFF, variant 2).

## B.1 Termination (total-correctness clause, both decisions)

Each contract additionally carries `Requires(MustTerminate(2))`, and each model
loop discharges it with a strictly decreasing, bounded-below measure
(`Invariant(MustTerminate(i))` / `Invariant(MustTerminate(j))`). This is not an
extra behaviour beyond the gold patch: the real `has_existing_aggregation`
computation is an `any(...)` over the finite `existing_annotations` dict plus
one `split_having_qualify()` call, and the real `annotation_mask` computation is
a bounded `for name in added_aggregate_names` loop over finite `get_refs()`
sets — both always complete and return their decision to `get_aggregation`.
Nagini verifies partial correctness by default, so without the obligation a
same-spec implementation that diverges before returning (e.g. an endless loop
in place of the scan) satisfies every `Ensures` vacuously while its faithful
real patch — a `get_aggregation` that hangs instead of deciding — would time
out every F2P/P2P aggregation test and NOT resolve (the audit's P1 witness
class; properties.py `weak-nonterm-esfd` / `weak-nonterm-ick` pin the
rejection).

## C. The `get_refs` fold itself (deep model, A-reference)

| # | model.py construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `collect_refs(tree)`: front-recursive — a `Ref` leaf (`tree[0] != 0`) contributes its code ONLY; a non-ref node (`0`) contributes nothing of its own but its children are folded; tail folded | `Ref.get_refs` (`return {self.refs}` — a hard LEAF, no recursion into `self.source`), `BaseExpression.get_refs` (union over sources), `WhereNode.get_refs` (union over children) | A-reference | the deep model of the new recursive gatherer; the flatten encodes a `Ref` as its referent code and **does NOT descend into the Ref's source** (matching `Ref.get_refs() == {self.refs}`), every other node as `0`+children, so set-membership of `collect_refs(flatten(tree))` == `get_refs(tree)`. Validated by axiom_check.py (G-AX) over trees whose Ref sources are themselves Ref-bearing (the divergent region), not consumed as an axiom. |

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The two operations that genuinely
*changed* — the wrapping discriminator (both axes: source + predicate) and the
inner-mask computation — are modelled **deeply** over the `List[int]` carriers
(decisions #1 and #2); the new recursive reference-gatherer they consume is
modelled **deeply** as `collect_refs` (an **A-reference** validated == real
`get_refs`), not hidden behind an axiom about the function under change. There is
**no consumed `@ContractOnly` axiom** anywhere in this bundle.

## E. The `summarize` flag threading

The gold also threads `summarize=False` through `build_filter` / `_add_q` /
`solve_lookup_type` / `Q.resolve_expression` (`query.py`, `query_utils.py`). It
only affects filter resolution when a *summarized aggregate is filtered on*; it
changes neither modelled decision and is observed by none of the F2P pruning
tests (none filter on a summarized aggregate). It is carried verbatim in
`patch.diff` so G-RESOLVE is exact, but is intentionally outside the modelled
behavioural core (mapping.md §4). This is not a kind-3 step in the model — it is
a no-op for the modelled behaviour, fully inside `patch.diff`.

## F. verify(model) ⇒ resolved

`existing_summary_forces_derived` verifies only if its result equals
`any_selected_summary(selected, summ) or filter_summary`: an ALIAS-ONLY aggregate
(`selected=0`) does NOT force the wrapping (1 SELECT — F2P
`test_unused_aliased_aggregate_pruned`), a SELECTED non-aggregate column
(`summ=0`) does NOT force it (1 SELECT — F2P
`test_non_aggregate_annotation_pruned`), while a SELECTED aggregate / windowed
column or a retained HAVING/QUALIFY filter does (2 SELECTs).
`inner_column_kept` verifies only if its result equals
`alias ∈ added ∪ get_refs(pushed-out)`: an unreferenced aggregate annotation is
pruned (F2P `test_unreferenced_aggregate_annotation_pruned`), a referenced one is
kept (`test_referenced_aggregate_annotation_kept`).
By R (the per-annotation selected/summary bits, the alias↔code map, set↔membership)
the verified decisions equal the gold's `has_existing_aggregation`
(built from `annotation_select`) and `annotation_mask` computations; by G-AX the
deep model `collect_refs` equals the real `get_refs` (A-reference, Ref-as-leaf).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: the
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
