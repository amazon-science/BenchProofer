# refinement.md — django__django-15957

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`perGroupSlice` `do` block and the `groupSlice`/`slicedGroups` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

This is a DB-effect bundle: the R/I legs are pure and input-dependent, but the
oracle is the backend window query, so G-CONF is `conf_skip` (mapping.md §4) and
the legs are audited by G-EQ + the F2P resolve (G-RESOLVE), not differential
fuzzing. There are no A legs. `patch.diff` is the gold patch **verbatim**
(G-RESOLVE).

## A. The changed operation — slice of a prefetch queryset

The patch adds a helper and routes both prefetch sites through it:

```python
def _filter_prefetch_queryset(queryset, field_name, instances):
    predicate = Q(**{f"{field_name}__in": instances})
    if queryset.query.is_sliced:
        low_mark, high_mark = queryset.query.low_mark, queryset.query.high_mark
        order_by = [expr for expr, _ in queryset.query.get_compiler(
            using=queryset._db or DEFAULT_DB_ALIAS).get_order_by()]
        window = Window(RowNumber(), partition_by=field_name, order_by=order_by)
        predicate &= GreaterThan(window, low_mark)
        if high_mark is not None:
            predicate &= LessThanOrEqual(window, high_mark)
        queryset.query.clear_limits()
    return queryset.filter(predicate)
```

Old behaviour (pre-patch, both sites): `queryset.filter(**{field__in: instances})`
with the queryset's slice marks still attached — the SQL `LIMIT/OFFSET` applies
**once, globally**, across the whole combined related-row set (so at most
`high-low` rows total are returned, not per parent). New behaviour: a window
`RowNumber()` partitioned by the relation field assigns each group its own
1-based row number; keeping `low_mark < rn ≤ high_mark` and clearing the global
limit yields each group's OWN slice `[low:high]`.

| # | Solution.lean impl op (`perGroupSlice`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | input `groups : List (List Int)` | the prefetched related rows, **grouped by `field_name`** and **ordered within each group** by the resolved `get_order_by()` | R | the already-ordered/grouped rows are an abstracted input; the ordering machinery (`get_compiler(...).get_order_by()`) is UNCHANGED and shared by both branches (mapping.md §2). One inner list = one parent instance's related rows. |
| A2 | inputs `low : Nat`, `high : Option Nat` | `queryset.query.low_mark`, `queryset.query.high_mark` (`None` ⇒ open-ended) | R | slice marks; `None ↔ none`, integer stop `h ↔ some h` (mapping.md §2). |
| A3 | `groupSlice low high g = (g.drop low).take (h-low)` (or `g.drop low` when `high=none`) | the window predicate `low_mark < RowNumber() OVER (PARTITION BY field ORDER BY order_by) ≤ high_mark`, applied within ONE partition | I | 1-based `rn`: `rn>low ∧ (high=none ∨ rn≤high)` ⇔ 0-based positions `[low,high)` ⇔ `g[low:high]`. The per-group slice modeled directly (mapping.md §2). |
| A4 | `slicedGroups low high groups`: each group sliced INDEPENDENTLY, results concatenated in group order (the backward `while` fold) | `queryset.filter(predicate)` returning the union over partitions, regrouped downstream per instance | I | because the window partitions by `field_name`, each group's `rn` restarts at 1, so each group gets its OWN `[low:high]`; the model concatenates the per-group slices, the queryset returns their union, regrouped identically by the unchanged `rel_obj_attr`. |

Discriminating content — **per-group vs global slice**. The pre-patch applies a
single global slice across all groups combined; `Solution_prepatch.lean`
reproduces exactly that (`groupSlice low high (flatten groups)`) and **fails**
`out = slicedGroups low high groups` (G-DIFF) whenever ≥2 groups are nonempty
under a nontrivial slice — precisely the scenario the F2P tests exercise (each
`Book`/`Author` is a partition; `[1:]`, `[1:2]` are nontrivial slices).

## B. The two call sites — pure delegation (kind R, not separate prepatches)

Both `RelatedManager.get_prefetch_queryset` (FK reverse, `related_descriptors.py:721-722`)
and `ManyRelatedManager.get_prefetch_queryset` (M2M, `:1054-1055`) change ONLY
by replacing the inline `queryset.filter(**query)` with the helper call (the M2M
site keeps its `._next_is_sticky()` prefix). The membership filter
`field__in: instances` is unchanged and present in both branches; the ONLY new
behaviour is the per-group window slice, which is the same modeled net effect
for both sites. Hence ONE modeled function and ONE failing prepatch cover all
four F2P behaviours (FK-reverse, M2M-forward, M2M-reverse, reverse-ordering):
they differ only in which relation supplies the groups and which ordering
resolves them — both abstracted into `groups` (A1).

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The operation that genuinely changed — global slice →
per-group slice — is modeled **directly** (the spelled-out fold `slicedGroups`
over `groupSlice`, steps A3/A4, concrete I ops), not hidden behind an axiom
about the function under change. There is **no consumed axiom** and **no
A-reference**: the unchanged ordering machinery is an abstracted input (A1, R),
so `axiom_check.py` is a `status=skip` stub. The SQL primitives (`Window`,
`RowNumber`, `GreaterThan`, `LessThanOrEqual`, `clear_limits`) are the backend
*mechanism* realising the modeled net effect; their semantic equivalence to the
deep model is grounded by G-RESOLVE (the patch resolves) + G-EQ (this narrative),
which is why G-CONF is `conf_skip` (mapping.md §4).

## D. verify(Solution) ⇒ resolved

`perGroupSlice` verifies only if its output equals `slicedGroups low high groups`
— each group's OWN ordered `[low:high]`, concatenated (A3/A4). By R
(`grouped/ordered rows ↔ List (List Int)`, `low/high ↔ Nat/Option Nat`) this is
exactly the row-set the patched `_filter_prefetch_queryset` yields through both
sites (A1/A2/B), regrouped per instance by the unchanged downstream code.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE, the F2P
`PrefetchLimitTests`). The single trust point is refinement fidelity (this doc +
G-EQ); there are no axioms (no G-AX obligation) and the R/I oracle is the
backend window query, audited by G-RESOLVE rather than fuzzed (conf_skip).
