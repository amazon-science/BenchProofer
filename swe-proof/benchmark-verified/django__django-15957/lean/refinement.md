# refinement.md — operation correspondence (django__django-15957)

Maps every op in `implementation_restrictPrefetch` to its `patch.diff`
counterpart (the added `_filter_prefetch_queryset`,
`django/db/models/fields/related_descriptors.py`). Tags: **R** type refinement ·
**A-consumed** proof uses a callee axiom · **A-reference** deep model validated ==
real callee (G-AX) · **I** identical concrete op.

## Patch (the added helper)
```python
def _filter_prefetch_queryset(queryset, field_name, instances):
    predicate = Q(**{f"{field_name}__in": instances})
    if queryset.query.is_sliced:
        low_mark, high_mark = queryset.query.low_mark, queryset.query.high_mark
        order_by = [
            expr
            for expr, _ in queryset.query.get_compiler(
                using=queryset._db or DEFAULT_DB_ALIAS
            ).get_order_by()
        ]
        window = Window(RowNumber(), partition_by=field_name, order_by=order_by)
        predicate &= GreaterThan(window, low_mark)
        if high_mark is not None:
            predicate &= LessThanOrEqual(window, high_mark)
        queryset.query.clear_limits()
    return queryset.filter(predicate)
```
The two call sites (`ForwardManyToOneDescriptor`-reverse, i.e. the reverse FK
`get_prefetch_queryset` at `:738`, and the M2M `get_prefetch_queryset` at
`:1069`) both replace the old `queryset.filter(**{f"{field}__in": instances})`
with a call to this helper. The single helper captures all four FAIL_TO_PASS
behaviors (m2m forward/reverse, fk reverse, reverse ordering); it is modeled once
as `restrictPrefetch`.

## Operation correspondence
| # | Lean op (`implementation_restrictPrefetch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `query : RelatedQuery` (`ordering`, `offset`, `limit`) | the `queryset.query` state read by the helper: `get_order_by()`, `low_mark`, `high_mark` | R | rich QuerySet/Query object ↔ `RelatedQuery` structure carrying only the touched fields (mapping.md bijection: `offset↔low_mark`, `limit↔high_mark`, `ordering↔order_by`). |
| 2 | `instances : List Int`, `fieldName : String` | the `instances` / `field_name` args | R | list/str bijection. |
| 3 | `let mut predicate := [PredAtom.memberOf fieldName instances]` | `predicate = Q(**{f"{field_name}__in": instances})` | I | the base membership conjunct; modeled as the first predicate atom. |
| 4 | `if isSliced query then …` | `if queryset.query.is_sliced:` | I | `is_sliced` is `low_mark != 0 or high_mark is not None`, mirrored exactly by `isSliced q = q.offset != 0 || q.limit.isSome`. |
| 5 | `let r : Ranking := { groupBy := fieldName, ordering := query.ordering }` | `window = Window(RowNumber(), partition_by=field_name, order_by=order_by)` | I | the per-group ranking that the row-number window expresses: partition by the grouping field, ordered by the query's order_by. Modeled as the `Ranking` carrier consumed by the position predicates. |
| 6 | `predicate := predicate ++ [PredAtom.positionAbove r query.offset]` | `predicate &= GreaterThan(window, low_mark)` | I | the lower bound: keep objects whose per-group position exceeds the offset (`low_mark`). |
| 7 | `if let some h := query.limit then predicate := predicate ++ [PredAtom.positionAtMost r h]` | `if high_mark is not None: predicate &= LessThanOrEqual(window, high_mark)` | I | the conditional upper bound: when a limit (`high_mark`) is set, keep objects whose per-group position is at most that limit. |
| 8 | `offset := 0; limit := none` | `queryset.query.clear_limits()` (`low_mark, high_mark = 0, None`) | I | drop the plain offset/limit bounds, since the slice is now carried by the position conjuncts. |
| 9 | `return { predicate, offset, limit }` | `return queryset.filter(predicate)` | I | apply the accumulated predicate; the returned query carries the conjuncts and the (now-cleared, when sliced) bounds. The actual `filter()` materialization and unmodeled query state are out of scope (mapping.md). |

No **A-consumed** rows (axioms region empty — the proof discharges the data
construction by `rfl`/`simp`). No **A-reference** rows: the row-number window,
`GreaterThan`/`LessThanOrEqual` lookups and `clear_limits` are not abstracted
behind opaque callees; they are reproduced concretely as I ops over the modeled
predicate/bound state. No changed-inexpressible op. The R/I legs are
mechanically refuted by **G-CONF** (`conformance_check.py`), which diffs the
impl shadow against the gold-patch predicate/limit construction over >=10^5
fuzzed inputs (0 mismatches); G-AX is a skip stub.

## conf_skip
`conf_skip = false`: the impl region is all R/I with concrete data ops, so the
Python shadow can be built without re-implementing any real callee. G-CONF is
active.

## Prepatch = the real bug
Pre-patch, both call sites simply did
`queryset = queryset.filter(**{f"{field}__in": instances})`, with NO handling of
a sliced queryset. The prepatch impl (`implementation_restrictPrefetch :=
return { predicate := [memberOf fieldName instances], offset := query.offset,
limit := query.limit }`) is exactly this: it emits only the membership conjunct
and leaves the offset/limit bounds untouched, never adding the per-group position
conditions and never clearing the bounds. It therefore cannot satisfy
`problem_spec_restrictPrefetch` on the discriminating clause `isSliced query =
true → …`: the spec demands `result.offset = 0`, `result.limit = none`, and the
position conjuncts appended to the predicate, none of which the prepatch
produces. (In real Django the un-cleared slice bounds make `.filter()` raise
`AssertionError: Cannot filter a query once a slice has been taken` — the
problem-statement symptom — and even were it tolerated, a per-result slice would
not apply the limit per parent group.) This is the behavior the four
`PrefetchLimitTests` FAIL_TO_PASS tests exercise (sliced `Prefetch` objects on
m2m forward/reverse, reverse FK, and reversed ordering). The carried gold proof
fails to typecheck against the buggy impl (G-DIFF), confirmed by `lean_verify`
exit 1 on the position-conjunct goals.
