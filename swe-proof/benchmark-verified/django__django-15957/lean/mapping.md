# mapping.md — django__django-15957

## Symbol binding (file:line @ base_commit f387d024fc75569d2a4a338bfda76cc2f328f627)
Modeled function: the prefetch-query restriction helper that the gold patch ADDS,
`_filter_prefetch_queryset` in
`django/db/models/fields/related_descriptors.py` (post-patch `:84-100`):

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

Call sites that switch to it (both replace
`queryset.filter(**{"%s__in" % name: instances})`):
- reverse FK `get_prefetch_queryset`, `related_descriptors.py:738-739` post-patch.
- M2M `get_prefetch_queryset`, `related_descriptors.py:1069-1071` post-patch.

Supporting unchanged callees (read, not modeled as separate functions):
- `Query.is_sliced` (`django/db/models/sql/query.py:2086-2087`):
  `return self.low_mark != 0 or self.high_mark is not None`.
- `Query.clear_limits` (`query.py:2081-2083`): `self.low_mark, self.high_mark = 0, None`.
- `Query.low_mark` / `Query.high_mark` (`query.py:191-192`): offset / final
  position bounds; `high_mark is None` means no upper bound.

Why it fixes the bug: pre-patch, a sliced prefetch queryset reached
`queryset.filter(**{f"{field}__in": instances})`; filtering a query that already
has a slice raises `AssertionError: Cannot filter a query once a slice has been
taken`. The fix translates the slice (`low_mark`/`high_mark`) into a per-parent
row-number window condition (`RowNumber()` partitioned by the grouping field),
appends it to the membership predicate, and clears the plain limits so the query
is filterable again — applying the slice PER PARENT GROUP rather than to the flat
result.

Lean modeled function name: `restrictPrefetch` (neutral — names the *behavior*
"restrict a prefetch query to the related objects, honoring a slice", sharing no
substring with the patched symbols `_filter_prefetch_queryset`, `Window`,
`RowNumber`, `GreaterThan`, `LessThanOrEqual`, `clear_limits`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `restrictPrefetch` (modeled helper) | `_filter_prefetch_queryset` (post-patch `related_descriptors.py:84-100`) |
| `query : RelatedQuery` | the `queryset.query` state read by the helper |
| `query.ordering` | `order_by` = `[expr for expr,_ in …get_order_by()]` |
| `query.offset` | `queryset.query.low_mark` |
| `query.limit : Option Nat` | `queryset.query.high_mark` (`none` == `None`) |
| `fieldName : String` | the `field_name` argument |
| `instances : List Int` | the `instances` argument (parent rows / their key values) |
| `isSliced query` | `queryset.query.is_sliced` (`low_mark != 0 or high_mark is not None`) |
| `PredAtom.memberOf field instances` | `Q(**{f"{field_name}__in": instances})` |
| `Ranking { groupBy, ordering }` | `Window(RowNumber(), partition_by=field_name, order_by=order_by)` |
| `PredAtom.positionAbove r low` | `GreaterThan(window, low_mark)` |
| `PredAtom.positionAtMost r high` | `LessThanOrEqual(window, high_mark)` |
| `offset := 0; limit := none` | `queryset.query.clear_limits()` |
| result `FilteredQuery` | `queryset.filter(predicate)` (its predicate + remaining bounds) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `low_mark : int` (>=0) | `offset : Nat` |
| `high_mark : int | None` | `limit : Option Nat` (`some h` / `none`) |
| `order_by : list[expr]` | `ordering : List String` |
| `field_name : str` | `fieldName : String` |
| `instances : list` | `instances : List Int` |
| `Q(field__in=…) & GreaterThan(window, low) [& LessThanOrEqual(window, high)]` | `predicate : List PredAtom` (conjunction, in append order) |
| `Window(RowNumber(), partition_by=field, order_by=ob)` | `Ranking { groupBy := field, ordering := ob }` |

## Callee provenance + flag deps
- `is_sliced` is a pure property of `(low_mark, high_mark)`; no flag/config
  dependence. Modeled concretely as `isSliced`.
- The `high_mark is not None` guard controls whether the upper-bound conjunct is
  appended — mirrored by the `if let some h := query.limit` branch.
- No unchanged callee is consumed as an axiom; G-AX is a skip stub.

## G-CONF fuzz seed
Pinned seed: **15957** (`conformance_check.py`), N = 200_000 fuzzed inputs +
edge cases (empty/short orderings; offset/limit combinations covering
unsliced, offset-only, limit-only, both, and the `set_empty` boundary
offset==limit). 0 disagreements between the impl R/I shadow and the gold-patch
predicate/limit construction.
