# mapping.md — django__django-12708

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 447980e72ac01da1594dd3373a03ba40b7ee6f80`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
callee the deep model is validated against by G-AX).

Repo file under change: `django/db/backends/base/schema.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selected_for_removal(constraints)` | the composite-index removal pipeline: `alter_index_together`'s "Deleted indexes" loop (`schema.py:394-396`) → `_delete_composed_index(model, fields, constraint_kwargs, sql)` (`schema.py:402-416`) → `_constraint_names(...)` filtering loop (`schema.py:1142-1170`) | the modeled changed behavior: how many constraints the removal selects (must be the non-unique indexes only) |
| `selects(code)` *(deep model — A-reference)* | the per-constraint match in `_constraint_names` under the kwargs the removal passes, i.e. `infodict['index'] == True and infodict['unique'] == False` (`schema.py:1156,1160` driven by `alter_index_together`'s `constraint_kwargs`) | pure spec: a candidate is selected iff it is an index and not unique |
| `keeps_any_index(code)` | the pre-patch per-constraint match under `{'index': True}` only (`schema.py:1160`, no `unique` filter) | pure spec: the over-broad (ambiguous) pre-patch selection — used only as the differential reference for the prepatch witness |
| `count_selected(s)` | `len(self._constraint_names(... index=True, unique=False))`, the count the post-patch `_delete_composed_index` checks against 1 (`schema.py:410`) | pure spec: number of non-unique indexes among the candidates |
| `count_any_index(s)` | `len(self._constraint_names(... index=True))`, the pre-patch count (`schema.py:410` pre-patch) | pure spec: number of any-index candidates (the over-count) |
| `is_index(code)` / `is_unique(code)` | the introspection `infodict['index']` / `infodict['unique']` boolean attributes (`get_constraints`, e.g. `django/db/backends/sqlite3/introspection.py:387-394`) | pure spec: the two attribute bits of a candidate constraint |

The gold patch changes exactly one operation: the `constraint_kwargs` argument
`alter_index_together` passes to `_delete_composed_index` for the deletion of an
index — from `{'index': True}` to `{'index': True, 'unique': False}`
(`schema.py:395-396`). That argument is fed verbatim into the `_constraint_names`
filter (`unique`/`index` keyword parameters), so the change is exactly: add the
`unique == False` conjunct to the per-constraint match.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the set/list of candidate constraints on the columns (each an introspection `infodict`, after excluding meta-managed names) | `List[int]` of 2-bit attribute codes | each constraint ↔ one `int` code; `code & 1 == infodict['index']` (bit 0 = `is_index`), `code & 2 == infodict['unique']*2` (bit 1 = `is_unique`). The columns/exclude filtering is upstream of the change and identical in both patches, so it is abstracted away: the modeled list is exactly the post-column-match, post-exclude candidate set. |
| `unique=True/False`, `index=True/False` keyword filters of `_constraint_names` | the conjuncts of `selects` / `keeps_any_index` | `index=True` ↔ `is_index(code)`; `unique=False` ↔ `not is_unique(code)`. A `None` filter ↔ omit the conjunct. |
| the result `constraint_names` list, and `len(constraint_names)` checked against 1 in `_delete_composed_index` (`schema.py:410`) | `Result()` of `selected_for_removal` (the count) | the model returns the COUNT of selected names; `_delete_composed_index` raises `ValueError` iff that count != 1. The fix's purpose is to make the count exclude co-located unique constraints, so the count is 1 (no error) when exactly one non-unique index exists. |

The constraint dict / set machinery is banned-construct-heavy in Nagini; the
candidate set is therefore modeled as `List[int]` codes with the specification
carried over `PSeq[int]` via `ToSeq`, and the two boolean attributes recovered
arithmetically (`code % 2`, `(code // 2) % 2`).

## 3. Callee / deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `selects` / `count_selected` deep model ↔ real `_constraint_names` (A-reference)

**Callee:** `BaseDatabaseSchemaEditor._constraint_names`
(`django/db/backends/base/schema.py:1142-1170` @ base_commit). The changed
selection operation is modeled **deeply** by the `@Pure` predicate `selects` and
the front-recursive fold `count_selected` in the `pure` region; there is **no
consumed `@ContractOnly` axiom**. The deep model is validated **== the real
callee** out-of-band by axiom_check.py (G-AX).

Source (the matching loop, abridged):

```python
for name, infodict in constraints.items():
    if column_names is None or column_names == infodict['columns']:
        if unique is not None and infodict['unique'] != unique:
            continue
        ...
        if index is not None and infodict['index'] != index:
            continue
        ...
        if not exclude or name not in exclude:
            result.append(name)
```

Under the composite-index removal's post-patch kwargs `index=True, unique=False`
(passed via `_delete_composed_index(..., {'index': True, 'unique': False}, ...)`),
a candidate `infodict` on the matched columns is kept iff
`infodict['index'] == True and infodict['unique'] == False` — exactly
`selects(code)`. The number kept is `count_selected`. The pre-patch kwargs
`{'index': True}` drop the `unique` conjunct, giving `keeps_any_index` /
`count_any_index`.

**Attribute-bit provenance.** Introspection reports a composite UNIQUE
constraint as `index=True, unique=True` (a unique constraint is backed by a
unique index; e.g. `django/db/backends/sqlite3/introspection.py:390,393`) and a
plain composite index (from `index_together`) as `index=True, unique=False`
(`introspection.py:393` with `unique=bool(unique)=False`). Hence when both sit
on the same columns, the pre-patch `{'index': True}` filter matches BOTH (count
2 → `_delete_composed_index` raises `ValueError("Found wrong number (2) ...")`,
the reported bug), while the post-patch `{'index': True, 'unique': False}` filter
matches only the plain index (count 1 → no error). This is the single
behavioural change the F2P test
`test_alter_index_together_remove_with_unique_together` observes
(`skipUnlessDBFeature('allows_multiple_constraints_on_same_fields')`, default
`True`; `django/db/backends/base/features.py:296`).

**Soundness check (G-AX):** `axiom_check.py` loads the REAL `_constraint_names`
straight out of `django/db/backends/base/schema.py` (the patched module), drives
it with synthetic introspection dicts in the exact backend shape, and asserts —
over 11 boundary sets, exhaustive candidate sets of length ≤ 5 over the four
attribute codes, and 20 000 randomized fuzz sets — that the names the real
filter selects under `index=True, unique=False` are exactly the codes
`selects` keeps, and that the count equals `count_selected`. It additionally
asserts the discriminating scenario `[unique, index]` selects only the index
post-patch but both pre-patch. stdlib-only imports; exit 0 iff sound.
