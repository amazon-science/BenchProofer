# mapping.md — django__django-15957

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f387d024fc75569d2a4a338bfda76cc2f328f627`, states the type
abstraction, and gives the provenance of every modeled callee.

Repo file under change: `django/db/models/fields/related_descriptors.py`.
The gold patch introduces a module-level helper `_filter_prefetch_queryset`
(new) and routes two existing prefetch sites through it.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `bounded_prefetch(query, member_code, instance_count)` | `_filter_prefetch_queryset(queryset, field_name, instances)` — new helper in `django/db/models/fields/related_descriptors.py` (added at line 86 by the patch) | the modeled changed behaviour: build the prefetch filter, translating any slice into a per-partition row-number window bound and then dropping the slice so the filter is applicable |
| `PrefetchQuery` (class) | the relevant state of `queryset.query` (`django/db/models/sql/query.Query`) | minimal carrier with only the touched fields (offset/limit marks + applied predicates) |
| `PrefetchQuery.offset_mark` | `Query.low_mark` (`django/db/models/sql/query.py:191`, set by `set_limits`) | slice start offset; `low_mark != 0` is part of `is_sliced` |
| `PrefetchQuery.limit_mark` | `Query.high_mark` (`django/db/models/sql/query.py:192`, `Optional`) | slice stop bound; `high_mark is not None` is part of `is_sliced` |
| `PrefetchQuery.membership_applied` | whether the `{field_name}__in=instances` predicate has been ANDed onto the query (`queryset.filter(predicate)` with `predicate = Q(**{f"{field_name}__in": instances})`) | the base equality/membership predicate every prefetch applies |
| `PrefetchQuery.lower_bound` | the strict lower window bound `GreaterThan(Window(RowNumber(), partition_by=field_name, ...), low_mark)` ANDed onto `predicate` when sliced | strict per-partition row-number lower bound; `None` when no such predicate was added |
| `PrefetchQuery.upper_bound` | the `LessThanOrEqual(window, high_mark)` window bound, ANDed only when `high_mark is not None` | inclusive per-partition row-number upper bound; `None` when absent |
| `is_sliced(query)` | `Query.is_sliced` property — `return self.low_mark != 0 or self.high_mark is not None` (`django/db/models/sql/query.py:2086-2087`) | pure predicate: a slice has been taken |
| `can_apply_filter(query)` | `Query.can_filter()` — `return not self.is_sliced` (`django/db/models/sql/query.py:2095-2098`); enforced by `QuerySet._filter_or_exclude` raising `TypeError("Cannot filter a query once a slice has been taken.")` when `is_sliced` (`django/db/models/query.py:1440-1442`) | precondition of applying a filter |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `queryset` / `queryset.query` (a `QuerySet` over a `Query`) | `PrefetchQuery` instance carrying only `offset_mark`, `limit_mark`, `membership_applied`, `lower_bound`, `upper_bound` | only the slice marks and the set of applied predicates are observable to the tested behaviour; all other query state is untouched by the helper and omitted |
| `field_name` (a `str`) | `member_code: int` | the field name is opaque to the slice→window translation; it appears only as the `partition_by`/`__in` key. Modeled as an opaque int identity carried into the membership predicate. |
| `instances` (a list) | `instance_count: int` (its length, `>= 0`) | the helper uses `instances` only as the RHS of `__in`; its content is opaque to the slice translation. The length is the only structural fact the membership predicate needs. |
| `Q(**{f"{field}__in": instances})` then `queryset.filter(predicate)` | setting `membership_applied = True` | the membership predicate is always ANDed; modeled as the boolean flag becoming true |
| `predicate &= GreaterThan(window, low_mark)` | setting `lower_bound = offset_mark` | the strict lower row-number bound equals `low_mark` |
| `predicate &= LessThanOrEqual(window, high_mark)` (guarded by `high_mark is not None`) | setting `upper_bound = limit_mark` (guarded the same way) | the inclusive upper row-number bound equals `high_mark`, present iff `high_mark is not None` |
| `queryset.query.clear_limits()` — `self.low_mark, self.high_mark = 0, None` (`query.py:2081-2083`) | `offset_mark = 0; limit_mark = None` | clearing the slice so the subsequent `filter` is applicable (`is_sliced` becomes false) |
| `queryset.filter(predicate)` raising on a sliced query | `Requires(not is_sliced(query))` on the apply-membership step | the `TypeError` guard is modeled as a precondition the fix discharges (by clearing limits first) and the prepatch violates |

`Window`, `RowNumber`, `GreaterThan`, `LessThanOrEqual`, `DEFAULT_DB_ALIAS`,
`get_compiler(...).get_order_by()` are expression *constructors* the helper
assembles into `predicate`; the tested behaviour observes only WHICH bounds end
up ANDed and with WHICH mark values, which is exactly what the model records on
the carrier. The `order_by` list passed to `Window` does not change which rows a
given `(low, high]` window selects per partition (it only orders the row numbers
within the existing query ordering); it is therefore not part of the discriminated
behaviour and is omitted (the F2P `test_reverse_ordering`/`test_foreignkey_reverse`
confirm the slice bounds, not a re-ordering, are what the fix gets right).

## 3. Callees / consumed axioms

The slice→bound translation (recording `lower_bound`/`upper_bound` and clearing
the marks) is modeled **deeply** as structural updates of the `PrefetchQuery`
carrier (R-refinements, §2). `is_sliced` is the repo's own pure predicate,
spelled out verbatim (`low_mark != 0 or high_mark is not None`). The
window/lookup constructors carry no behaviour the slice-translation depends on
beyond the bound values they wrap, so they are R-refinements onto
`lower_bound`/`upper_bound`, not axiomatized callees.

The bundle has **two consumed `@ContractOnly` axioms**, both modeling the
UNCHANGED predicate-application callee `QuerySet.filter` (NOT the function under
change):

| model symbol | repo callee (file:line @ base_commit) | what the contract captures | weakest-sufficient? |
|---|---|---|---|
| `apply_membership(query)` | `QuerySet.filter(predicate)` (`django/db/models/query.py:1424`) routed through `_filter_or_exclude` → `Query.can_filter()` (`django/db/models/sql/query.py:2095-2098`), which **raises `TypeError("Cannot filter a query once a slice has been taken.")`** when `is_sliced` (`query.py:1440-1442`) | `Requires(not is_sliced(query))` (the raise guard, modeled as a precondition the fix must discharge); `Ensures(membership_applied == True and membership_token(query))` (the predicate is ANDed and the capability granted) | yes — asserts only that the predicate is applied, that the query was unsliced at application, and grants the token; claims nothing about the predicate's contents or ordering |
| `membership_token(query)` (`@ContractOnly @Predicate`, abstract) | the EFFECT of a successful `filter` on a non-sliced query (the `__in` predicate actually ANDed onto the clone) | unforgeable capability: abstract (no body) so no impl can `Fold` it; obtainable ONLY from `apply_membership`'s `Ensures`. It pins the membership step as a control-flow effect (filter-vs-raise) that has no value-level discriminator, so a forgeable `membership_applied` flag cannot satisfy it. | yes — pure marker; carries no value claims |

`axiom_check.py` (G-AX) validates BOTH the structural slice→bound translation
against Django's real `Query` slice/limit semantics
(`set_limits`/`clear_limits`/`is_sliced`) AND the `apply_membership` contract:
it drives the real `_filter_prefetch_queryset`, confirming the membership
predicate is present on the output and the query is no longer sliced when
`filter` runs (i.e. `filter` succeeds — it does NOT raise — exactly because the
slice was cleared first, which is the token-grant condition).
