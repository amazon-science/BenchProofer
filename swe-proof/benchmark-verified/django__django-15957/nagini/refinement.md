# refinement.md — django__django-15957

The operation-by-operation correspondence between `model.py`'s implementation
(the `bounded_prefetch` impl region, the modeled `apply_membership` callee, and
the pure `is_sliced` predicate) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** (the proof uses an axiom's
`Ensures`), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The new helper — `_filter_prefetch_queryset`

Gold hunk (new module-level helper in
`django/db/models/fields/related_descriptors.py`):
```python
def _filter_prefetch_queryset(queryset, field_name, instances):
    predicate = Q(**{f"{field_name}__in": instances})
    if queryset.query.is_sliced:
        low_mark, high_mark = queryset.query.low_mark, queryset.query.high_mark
        order_by = [ ... get_order_by() ... ]
        window = Window(RowNumber(), partition_by=field_name, order_by=order_by)
        predicate &= GreaterThan(window, low_mark)
        if high_mark is not None:
            predicate &= LessThanOrEqual(window, high_mark)
        queryset.query.clear_limits()
    return queryset.filter(predicate)
```
modeled by `bounded_prefetch(query, member_code, instance_count)`.

| # | model.py impl op (`bounded_prefetch`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `query: PrefetchQuery` carrying `offset_mark`, `limit_mark`, `membership_applied`, `lower_bound`, `upper_bound` | `queryset` / `queryset.query` (a `QuerySet` over a `Query`) | R | only the slice marks and the applied-predicate set are observable to the tested behaviour; mapping.md §2 gives the field bijection (`offset_mark`↔`low_mark`, `limit_mark`↔`high_mark`). |
| A2 | params `member_code: int`, `instance_count: int` | `field_name` (`str`), `instances` (list) | R | both are opaque to the slice→bound translation; carried as scalars. The field name appears only as the `partition_by`/`__in` key, the instances only as the `__in` RHS (mapping.md §2). |
| A3 | `is_sliced(query)` = `offset_mark != 0 or limit_mark is not None` | `queryset.query.is_sliced` = `low_mark != 0 or high_mark is not None` (`sql/query.py:2086-2087`) | I | the pure predicate is spelled out verbatim from the repo property under the field bijection. |
| A4 | inside the sliced branch: `low = offset_mark`; `high = limit_mark` | `low_mark, high_mark = queryset.query.low_mark, queryset.query.high_mark` | I/R | reading the two marks; R only by the field-name rename. |
| A5 | `query.lower_bound = low` | `predicate &= GreaterThan(window, low_mark)` where `window = Window(RowNumber(), partition_by=field_name, order_by=...)` | R | the strict per-partition row-position lower bound is recorded as `lower_bound = offset_mark`. The `Window`/`RowNumber`/`GreaterThan` constructors carry no behaviour the slice translation depends on beyond the bound value (`low_mark`) and the comparison sense (strict, `>`); validated by G-AX (the real lookup is `GreaterThan` over a `Window(RowNumber())` with `rhs == low_mark`). The `order_by`/`partition_by` only fix the within-partition row numbering of the *same* query ordering and do not change which `(low, high]` positions are selected per partition (mapping.md §2). |
| A6 | `if high is not None: query.upper_bound = high` | `if high_mark is not None: predicate &= LessThanOrEqual(window, high_mark)` | R + I | identical guard (`high_mark is not None`); the inclusive upper bound is recorded as `upper_bound = limit_mark`. Validated by G-AX (`LessThanOrEqual` over the `Window(RowNumber())`, `rhs == high_mark`, present iff `high_mark is not None`). |
| A7 | `query.offset_mark = 0; query.limit_mark = None` | `queryset.query.clear_limits()` = `self.low_mark, self.high_mark = 0, None` (`sql/query.py:2081-2083`) | R/I | clearing the slice; spelled out as the assignment `clear_limits` performs. |
| A8 | `apply_membership(query)` (`@ContractOnly`: requires `not is_sliced(query)`, ensures `membership_applied == True` AND grants the unforgeable `membership_token(query)`) | `return queryset.filter(predicate)` | **A-consumed** | `queryset.filter(predicate)` ANDs the membership predicate and **raises `TypeError("Cannot filter a query once a slice has been taken.")` when the query is sliced** (`query.py:1440-1442`, `can_filter()` = `not is_sliced`). Modeled as `apply_membership`, a `@ContractOnly` callee with `Requires(not is_sliced(query))` and `Ensures(membership_applied == True and membership_token(query))`. The proof CONSUMES this contract: it is the unique producer of the `membership_token` capability (see A8b), so the membership-application step cannot be faked by a flag write. The contract is the WEAKEST sufficient one (it asserts only: predicate applied, query was unsliced at application, token granted) and is validated against the real `filter`/`can_filter` slice guard by G-AX (axiom_check.py drives the real helper and confirms the membership predicate is present and the query is unsliced when `filter` runs). |
| A8b | `membership_token(query)` (`@ContractOnly @Predicate`, abstract/no body) | the EFFECT of `queryset.filter(predicate)` succeeding on a non-sliced query (the predicate is actually ANDed onto the clone) | **A-consumed** | An unforgeable capability token. Because it is abstract it cannot be `Fold`ed by any impl, so the ONLY way to obtain it is from `apply_membership`'s `Ensures` (A8), which grants it only under `not is_sliced`. `bounded_prefetch`'s postcondition `Ensures(membership_token(query))` therefore forces every verifying impl to route the result through a successful application on an unsliced query — it cannot discharge the membership obligation by `query.membership_applied = True`. This closes the directive-8 echo cheat: the membership effect is a control-flow property (filter-vs-raise) with no value-level discriminator, so it is pinned by the capability token rather than a forgeable flag value. Its provenance (the real `filter` only ANDs the predicate when `can_filter()` holds) is checked by G-AX. |
| A9 | `return query` | `return queryset.filter(predicate)` (returns the filtered clone) | R | the returned object is the query with the membership predicate (and any bounds) applied; the model returns the same carrier mutated and carrying the token. |

## B. Why the prepatch fails on the discriminating clause

The pre-patch code at both call sites is `queryset = queryset.filter(**query)`
with `query = {"%s__in" % name: instances}` — i.e. it applies the membership
predicate **directly to the (possibly sliced) query**, with no slice→bound
translation and no `clear_limits`. `model_prepatch.py` reproduces exactly this:
its `bounded_prefetch` impl is just `apply_membership(query); return query`,
with the slice-translation/clear-limits block removed.

`model_prepatch.py` FAILS G-VERIFY on (`model_prepatch.py:157`):
```
The precondition of method apply_membership might not hold.
Assertion (not is_sliced(query)) might not hold.
```
This is the faithful encoding of the real `TypeError: Cannot filter a query
once a slice has been taken.` — the exact `AssertionError`/`TypeError` the issue
reports. (It would additionally fail to obtain `membership_token(query)` and
violate the `lower_bound is not None` and `not is_sliced(query)` postconditions,
but the first failing obligation is the membership precondition — the literal
bug.) The spec is byte-identical between `model.py` and `model_prepatch.py`
(everything outside the `bounded_prefetch` impl region; G-DIFF `same_spec`).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operations that genuinely changed
— recording the position restriction the slice carried, dropping the slice, and
applying the membership predicate only on an unsliced query — are modeled either
as structural updates of the `PrefetchQuery` carrier
(`lower_bound`/`upper_bound`/marks: A4–A7, R/I) or, for the one step that is a
control-flow effect rather than a value computation, as the guarded
`@ContractOnly` callee `apply_membership` + the unforgeable
`membership_token` capability (A8/A8b, A-consumed). None of these is an axiom
about the function *under change*: `apply_membership` models the UNCHANGED
`QuerySet.filter`/`can_filter` slice guard, not `_filter_prefetch_queryset`
itself, whose slice→bound logic is spelled out deeply on the carrier.

There are exactly **two consumed axioms**, both modeling unchanged callees:
the `apply_membership` contract (the `filter`/`can_filter` raise-on-sliced
guard) and the abstract `membership_token` predicate it grants. The token is
load-bearing for `verify ⟹ correct`: the membership effect is a control-flow
property (`filter` ANDs the predicate vs. raises `TypeError`) with NO value-level
discriminator, so a forgeable flag (`membership_applied == True`) does not pin
it — an impl could echo the flag while still sliced (which refines to filtering
a sliced query → `TypeError` → fails every F2P) and verify. The unforgeable
token forces the result to be produced by a successful application on an
unsliced query, closing that directive-8 echo cheat. `is_sliced` and the
`not is_sliced` precondition remain the repo's own pure slice predicates spelled
out verbatim. The slice→bound translation (A4–A7) and the
`filter`/`can_filter` raise guard (A8) are validated == the real
`_filter_prefetch_queryset` + `Query` slice machinery by axiom_check.py (G-AX).
The window/lookup constructors are R-refinements onto
`lower_bound`/`upper_bound`, not axiomatized callees (mapping.md §3).

## D. verify(model) ⇒ resolved

`bounded_prefetch` verifies only if (i) when the query is sliced it records a
strict lower bound equal to the offset and, iff a finite limit is present, an
inclusive upper bound equal to the limit (postconditions A5/A6), (ii) it clears
the slice so the membership predicate is applicable — passing
`apply_membership`'s `not is_sliced` precondition (A8) — and (iii) the
membership predicate is always applied **and the unforgeable
`membership_token(Result())` obtained** (A8b postcondition), which is
establishable ONLY by routing through `apply_membership` on an unsliced query —
so an impl cannot fake the membership step with a flag write while still sliced.
By R (the field
bijection, the `Window/RowNumber/GreaterThan/LessThanOrEqual` constructors, and
`clear_limits`/`filter`) the verified helper equals the gold
`_filter_prefetch_queryset`; by G-AX the structural slice→bound translation and
the unsliced-before-filter requirement match the real Django machinery on the
F2P slice patterns (`[1:]`, `[1:2]`, reverse-ordered). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and validated callees — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: callee/structural soundness
(G-AX) and refinement fidelity (this document, G-EQ).
