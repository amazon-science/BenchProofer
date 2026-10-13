# mapping.md — django__django-16938

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed for the twin-artifact bundle. Read with `refinement.md` (the op
correspondence) and `meta.json` (the gate map).

`spec_provenance: cold` — the spec was derived from the `problem_statement`, the
gold `patch`, and the real repo source at `base_commit`
(`1136aa5005f0ae70fea12796b7e37d6f027b9263`), with no consultation of any prior
solution/twin for this instance.

## 1. Symbol binding (file:line @ base_commit)

The fix touches a local closure named `queryset_iterator` defined identically in
two serializer backends; both build the relation-iteration load plan the same
way and both receive the identical one-line change.

| Lean symbol | repo symbol | file:line @ base_commit |
|---|---|---|
| `queryIterPlan` (model of the load plan built by the m2m relation iterator) | `queryset_iterator` (the `else`-branch closure inside `Serializer.handle_m2m_field`) | `django/core/serializers/python.py:81` |
| (same model) | `queryset_iterator` (the `else`-branch closure inside `Serializer.handle_m2m`) | `django/core/serializers/xml_serializer.py:158` |

The two sites are byte-identical in both the pre- and post-patch state
(`return getattr(obj, field.name).only("pk").iterator()` →
`return getattr(obj, field.name).select_related().only("pk").iterator()`), so a
single `method` models both. G-DIFF needs only one failing prepatch because the
two sites express one and the same fixed behavior (no independently-observable
second behavior).

## 2. Type bijection (Lean ↔ Python)

The change is about the *load plan* a queryset hands to the SQL compiler, not
about a value carrier (`str`/`list`/`dict`). We model the two plan components
the conflict depends on, abstracting the rest of the queryset:

| repo reality | Lean model | bijection |
|---|---|---|
| `queryset.query.select_related` ∈ {`False`, `True`, `dict`} | `RelatedPlan` | `False`/`True` ↔ `RelatedPlan.unrestricted` (the boolean form — both "no related" and "follow all related" are *unrestricted*, i.e. `isinstance(..., dict)` is `False`); a `dict` of named relations ↔ `RelatedPlan.restricted names`, where `names = list(dict.keys())`. Only the `dict` form makes `restricted = isinstance(select_related, dict)` true. |
| immediate-load mask (`query.deferred_loading`, set by `.only(...)` / `.defer(...)`) | `QState.immediate : Option (List String)` | no `.only`/`.defer` ↔ `none` (load every field, nothing deferred); `.only(fs)` ↔ `some fs` (load exactly `fs` immediately, defer the rest). `.only("pk")` ↔ `some ["pk"]`. |
| the SQL-compiler refusal `FieldError("… cannot be both deferred and traversed using select_related at the same time")` raised by `select_related_descend` (`django/db/models/query_utils.py:343`) | `planRejected : QState → Bool` | `planRejected q = true` ↔ the compiler raises `FieldError` while building related selections for `q`. Encodes exactly the `restricted ∧ select_mask ∧ field.name ∈ requested ∧ field ∉ select_mask` raise condition: restricted-to-names AND at least one named relation is deferred by the immediate-load mask. |

The model deliberately tracks only relation *names* (`List String`), which is
the granularity the conflict is decided at; column-level masking of
non-relation fields is irrelevant to the `FieldError` and is abstracted away.

## 3. Callee provenance + flag deps (the A-reference transformers)

No consumed axioms. The three plan operations are deep models of UNCHANGED
queryset machinery the changed closure calls; each is validated == its real
callee by G-AX (`axiom_check.py`). None is the operation the patch changes — the
patch changes the *composition* (it inserts a call), not these callees.

| Lean def | real callee | provenance @ base_commit | A-kind |
|---|---|---|---|
| `selectAllRelated` (`related := .unrestricted`) | `QuerySet.select_related()` called with **no arguments** | `django/db/models/query.py:1546`; the no-arg branch sets `obj.query.select_related = True` (the boolean form ⇒ `isinstance(..., dict)` is `False` ⇒ `restricted = False`) | A-reference (§3.1) |
| `loadOnlyPk` (`immediate := some ["pk"]`) | `QuerySet.only("pk")` | `django/db/models/query.py:1728`; `add_immediate_loading(("pk",))` restricts the immediate-load set to the primary key, deferring the rest | A-reference (§3.2) |
| `planRejected` | `select_related_descend(...)`'s raise condition, exercised through `SQLCompiler.get_related_selections` → query setup | `django/db/models/query_utils.py:343` (raise); `django/db/models/sql/compiler.py:1184` (`restricted = isinstance(self.query.select_related, dict)`) | A-reference (§3.3) |

**Flag dependency (G-AX must fuzz the right configuration).** The `FieldError`
fires only when `restricted` is true, i.e. when `select_related` is a *dict*
(a named-relation selection such as a custom manager's
`get_queryset().select_related("master")`). With `select_related = True` (the
no-arg post-patch form) `restricted` is `False` and the raise never fires even
though `.only("pk")` still defers the relation. G-AX therefore builds the real
queryset BOTH ways — restricted (dict) and unrestricted (boolean) — and checks
`select_related_descend`'s verdict against `planRejected` in each.

## 4. G-CONF fuzz seed + status

`conformance_check.py` is a **skip** (`meta.json conf_skip = true`). The impl
region's value-carrying ops (`selectAllRelated`, `loadOnlyPk`) are both
A-reference callees, and the residual content is the `planRejected` predicate
(also A-reference) over them — there is no R (type-rename) or I (identical
concrete computation) data carrier to transliterate to Python and differentially
fuzz. The cross-language weight rests on G-AX (each A-reference validated against
the real queryset machinery) and G-EQ/G-PANEL. Pinned seed for the G-AX fuzz:
**16938**.
