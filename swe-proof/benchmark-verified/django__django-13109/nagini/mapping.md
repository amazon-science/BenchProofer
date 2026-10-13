# mapping.md — django__django-13109

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fbe82f82555bc25dccb476c749ca062f0b522be3`, states the type
abstraction, and gives the provenance of the axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/fields/related.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validate_reference(value, complete_rows, curated_rows)` | `ForeignObject.validate(self, value, model_instance)` — `django/db/models/fields/related.py:909` (changed body line 917) | the modeled changed function: the relational-field reference check |
| `complete_rows: List[int]` | the keys of every row reachable through `self.remote_field.model._base_manager` (after `.using(using)`) — `related.py:917` post-patch | the COMPLETE, unfiltered row collection the fixed check consults |
| `curated_rows: List[int]` | the keys of every row reachable through `self.remote_field.model._default_manager` (after `.using(using)`) — `related.py:917` pre-patch | the curated default collection the buggy check consulted |
| `value: int` | the candidate reference value `value` validated against `self.remote_field.field_name` | the referenced key |
| `present(key, rows)` | the ORM `.filter(**{field_name: value})` + `.exists()` membership test on the chosen queryset — `related.py:917-921` | pure spec: some row in `rows` carries `key` |
| `choice_permitted(key)` *(axiom — A-consumed)* | `qs.complex_filter(self.get_limit_choices_to())` — `related.py:920` (unchanged by the patch) | the additional per-field choice restriction applied to BOTH managers' rows |
| `reference_holds(key, complete_rows)` | the full no-raise condition: `qs.exists()` is true on the base-manager queryset after `complex_filter` — `related.py:921` post-patch | pure spec: the reference is valid |
| `ReferenceInvalid` exception | `exceptions.ValidationError(self.error_messages['invalid'], code='invalid', ...)` — `related.py:922-929` | the rejection raised when no matching row exists |

The single changed token is `_default_manager` → `_base_manager` at
`related.py:917`. Everything downstream (`.using(using)`, `.filter(...)`,
`.complex_filter(get_limit_choices_to())`, `.exists()`, the `raise
ValidationError`) is unchanged by the patch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a queryset of related-model rows (a `QuerySet`) | `List[int]` of the rows' referenced-field keys | a row whose `field_name` equals `k` ↔ the int `k` appearing in the list; `qs.filter(field_name=value).exists()` ↔ `value` ∈ the list |
| `self.remote_field.model._base_manager.using(using)` queryset | `complete_rows` | the unfiltered manager returns every stored row (see §3.2); its key set is `complete_rows` |
| `self.remote_field.model._default_manager.using(using)` queryset | `curated_rows` | the default manager may apply a standing `get_queryset` filter; its key set is a SUBSET of `complete_rows` (see §3.2). The pre-patch skeleton consults this set. |
| `qs.exists()` returning a bool | `present(value, rows)` / membership | true iff at least one row in the chosen queryset carries `value` |
| `self.error_messages['invalid']` `ValidationError` raise | `raise ReferenceInvalid()` | a builtin exception in an `Exsures` crashes the Nagini translator; a user-defined subclass of `Exception` stands in. Only the raise/no-raise distinction is observable (the F2P tests assert `is_valid()` / `full_clean()` outcome, not the message). |

`value` is the referenced key; modelling it as an `int` is exact — the ORM
compares `field_name == value` for equality. The `using` database alias and the
`super().validate()`, `parent_link`, and `value is None` guards (`related.py:910-916`)
are unchanged control flow upstream of the modeled hunk and are not part of the
changed behaviour; the model is the reference check that runs after those guards.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `choice_permitted` ↔ `complex_filter(get_limit_choices_to())` (A-consumed)
**Callee:** `QuerySet.complex_filter(self.get_limit_choices_to())` —
`related.py:920`, applied identically before and after the patch.
`get_limit_choices_to()` (`related.py:390`) returns the field's
`limit_choices_to` restriction (a `Q`/dict, possibly empty). It narrows the
queryset by a per-row predicate that, for the membership decision on `value`,
depends only on whether `value`'s row satisfies the restriction — modelled as
the deterministic predicate `choice_permitted(value)`.

The axiom is the WEAKEST contract the proof needs: `choice_permitted` is a
total, deterministic boolean function of the key (`Ensures(True)` — no value
claim). The proof consumes it as a conjunct of `reference_holds`: the reference
is valid only when the matched row also passes this restriction. It is the
SAME callee in both managers' pipelines, so it does NOT discriminate the bug;
it is included so the spec pins the FULL no-raise condition
(`present ∧ choice_permitted`) rather than membership alone — preventing a
wrong impl that ignores `limit_choices_to`.

**Soundness check (G-AX):** `axiom_check.py` exercises Django's real
`complex_filter(get_limit_choices_to())` indirectly via the modelled property —
that the restriction is a deterministic function of the key applied equally to
both querysets (a row's eligibility under `limit_choices_to` does not depend on
which manager surfaced it). It confirms determinism (same key ⇒ same verdict)
on boundary + fuzz keys and that an empty `limit_choices_to` admits every key.

### 3.2 The manager subset relationship (the changed behaviour — modeled, not axiomatized)
**Callees:** `Model._base_manager` (`db/models/base.py:377` →
`options.py:382 base_manager`) and `Model._default_manager`
(`db/models/base.py:381` → `options.py:410 default_manager`).

`_base_manager` is, by construction, a plain `Manager()` (auto-created with
`auto_created=True` and no `get_queryset` override; `options.py:403-407`) unless
a model declares `base_manager_name`. It returns EVERY stored row — the Django
docs state the base manager "is used to access objects that are related to from
some other model" and "should return all objects in all cases." `_default_manager`
is the first declared manager (`options.py:409-431`); a model may give it a
`get_queryset` that adds a standing filter (the test models' `WriterManager` /
`AuthorManager` filter `archived=False`). Hence:

  rows(`_default_manager`) ⊆ rows(`_base_manager`),

i.e. `curated_rows` is a subset of `complete_rows`. The patch changes which set
the reference check consults from the curated subset to the complete set. This
is the changed operation; it is modelled DEEPLY (the membership `present` over
`complete_rows` vs `curated_rows`), NOT hidden behind an axiom about the thing
that changed. `axiom_check.py` confirms the subset relationship holds for a
default manager whose `get_queryset` filters rows, and that a key present in
`complete_rows` but absent from `curated_rows` is exactly the discriminating
witness (validated post-patch, rejected pre-patch).
