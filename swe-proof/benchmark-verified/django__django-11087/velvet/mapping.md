# mapping.md — django__django-11087

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8180ffba21bf10f4be905cb0d4890dc2bcff2788`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/db/models/deletion.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `columnsToFetch` *(method)* | the column-set decision added inside `Collector.collect`, `django/db/models/deletion.py:169` (the changed `elif sub_objs:` block at `:223`, replaced by the `else:` block in the patch) | the modeled changed behaviour: which columns are fetched for a batch of dependent rows |
| `hasExposingSubscriber (preDelete postDelete)` *(pure, deep model)* | `Collector._has_signal_listeners(model)` — the helper the patch ADDS at `django/db/models/deletion.py:120` (post-patch) | pure spec: are pre-/post-removal change-notification subscribers registered for the model |
| `mayNarrow (widenedFetch preDelete postDelete)` *(pure, deep model)* | the guard `not (sub_objs.query.select_related or self._has_signal_listeners(related_model))` (post-patch `collect`) | pure spec: is narrowing the fetched column set permitted |
| `columnsFetched (allColumns referencedColumns widenedFetch preDelete postDelete)` *(pure, deep model)* | the `sub_objs = sub_objs.only(*referenced_fields)` narrowing vs. the unchanged full fetch (post-patch `collect`) | pure spec: the column set actually fetched |

Pre-patch repo symbols the change replaces (refinement audit only, not in the
consumer spec view): the `elif sub_objs: field.remote_field.on_delete(...)`
branch (`deletion.py:223-224`), which fetched the full column set
unconditionally; and the three-way listener test in `can_fast_delete`
(`deletion.py:138-140`, `pre_delete or post_delete or m2m_changed`) that the
patch refactors into the new `_has_signal_listeners` helper (pre/post only).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the set of columns a `QuerySet` would fetch (the model's concrete local fields, by `attname`) | `allColumns : List Nat` | a column ↔ a `Nat` id; the full default fetch ↔ `allColumns`. Only set IDENTITY (which columns) is observed, so a stable per-column id list is a faithful carrier. |
| the referenced-only column set `set(chain.from_iterable(rf.attname for rf in rel.field.foreign_related_fields for rel in ...))`, i.e. the result of `.only(*referenced_fields)` | `referencedColumns : List Nat` | the referenced FK target columns ↔ a `Nat` id list. `referencedColumns ⊆ allColumns` in the repo; the spec pins the exact returned set, so no subset hypothesis is modeled. |
| `bool(sub_objs.query.select_related)` — whether the dependent fetch was widened to also pull related rows | `widenedFetch : Bool` | truthy `select_related` (a non-empty dict / `True`) ↔ `true`; falsy (`False`/`{}`) ↔ `false`. |
| `signals.pre_delete.has_listeners(model)` | `preDelete : Bool` | listener registered ↔ `true`. |
| `signals.post_delete.has_listeners(model)` | `postDelete : Bool` | listener registered ↔ `true`. |
| `QuerySet.only(*fields)` narrowing the SELECT to `fields` | choosing `referencedColumns` over `allColumns` | `.only(referenced)` produces a query whose fetched column set is exactly `referencedColumns ∪ {pk}` (pk always referenced as an FK target here); observationally the referenced set. mapping below treats the narrowed fetch as `referencedColumns`. |

The column sets are modeled as `List Nat` (identifiers) because the operation is
a SET CHOICE between two precomputed lists — no per-element string content is
inspected, so a faithful id carrier suffices and avoids modeling field objects.

## 3. Callee provenance & flag dependencies

### 3.1 `hasExposingSubscriber` deep model ↔ `_has_signal_listeners` (deep model, R/I — NOT an axiom)
**Callee:** the helper the patch adds:
```python
def _has_signal_listeners(self, model):
    return (
        signals.pre_delete.has_listeners(model) or
        signals.post_delete.has_listeners(model)
    )
```
Modeled DEEPLY as `hasExposingSubscriber preDelete postDelete = preDelete ||
postDelete`. The two `has_listeners` queries are abstracted to the boolean
inputs `preDelete`/`postDelete` (R refinement, §2). There is **no consumed
axiom**: the disjunction is spelled out and G-CONF validates the whole decision
against the real `_has_signal_listeners` + real `signals` registry.

**Flag dependency:** the pre-patch `can_fast_delete` test also disjoined
`signals.m2m_changed.has_listeners(model)`; the patch's `_has_signal_listeners`
(used at BOTH the `can_fast_delete` site and the new narrowing guard) drops
`m2m_changed`. For the narrowing decision modeled here, `m2m_changed` is
deliberately excluded: an m2m-changed subscriber never receives the dependent
rows the SELECT fetches, so it places no requirement on the column set. G-CONF
fuzzes pre/post/m2m configurations and confirms only pre/post gate the choice.

### 3.2 `mayNarrow` / `columnsFetched` deep model ↔ the `collect` narrowing (deep model, R/I)
**Callee:** the changed block in `Collector.collect` (post-patch):
```python
related_model = related.related_model
if not (sub_objs.query.select_related or self._has_signal_listeners(related_model)):
    referenced_fields = set(chain.from_iterable(
        (rf.attname for rf in rel.field.foreign_related_fields)
        for rel in get_candidate_relations_to_delete(related_model._meta)
    ))
    sub_objs = sub_objs.only(*tuple(referenced_fields))
if sub_objs:
    field.remote_field.on_delete(self, field, sub_objs, self.using)
```
`mayNarrow widenedFetch preDelete postDelete = !(widenedFetch ||
hasExposingSubscriber preDelete postDelete)` models the `not (... or ...)`
guard; `columnsFetched` selects `referencedColumns` when narrowing is permitted
(the `.only(...)` branch) and `allColumns` otherwise (no `.only`, full fetch).
This is modeled deeply (R/I), not behind an axiom about the function under
change. The `if sub_objs:` truthiness guard and `on_delete` dispatch are
orthogonal control flow unchanged by the column choice and are not modeled
(they fire identically in both branches; the F2P test observes only the emitted
SELECT's column list, captured query #0).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11087`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`hasExposingSubscriber`/`mayNarrow`/`columnsFetched` to Python and exercises the
decision against the REAL patched `_has_signal_listeners` plus the real
`signals` registry (pre_delete/post_delete/m2m_changed connect/disconnect) over
boundary + fuzzed boolean configurations, and confirms the chosen column set
matches what the patched `Collector.collect` would fetch (referenced-only vs
full) for the test models `Origin`/`Referrer`/`SecondReferrer`.
