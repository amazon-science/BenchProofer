# mapping.md — django__django-11400

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1f8382d34d54061eddc41df6994e20ee38c60907`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo files under change:
* `django/db/models/fields/__init__.py` (`Field.get_choices`)
* `django/db/models/fields/reverse_related.py` (`ForeignObjectRel.get_choices`)
* `django/contrib/admin/filters.py` (`RelatedFieldListFilter` /
  `RelatedOnlyFieldListFilter`)

## 1. Symbol ↔ repo binding

The modeled behaviour is the **ordering-selection kernel** the patch introduces:
choosing which ordering specification a related collection is materialized under,
given the collection's intrinsic default ordering (`Meta.ordering`) and an
explicitly requested ordering. The same kernel appears at every changed site;
`Solution.lean` models it once as `orderedChoices` and shows the
`RelatedOnlyFieldListFilter` plumbing routing through it as `restrictedChoices`.

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `effectiveOrdering (defaultOrdering requested : List String)` | the `if ordering: qs = qs.order_by(*ordering)` guard newly added in both `get_choices` bodies (`django/db/models/fields/__init__.py:828-830` post-patch; `django/db/models/fields/reverse_related.py:125-127` post-patch) | pure spec: the ordering specification a collection is finally materialized under — `requested` if non-empty, else `defaultOrdering` |
| `orderedChoices (defaultOrdering requested : List String)` | `Field.get_choices(..., ordering)` ordering selection — `django/db/models/fields/__init__.py:809` (body 825-832) — driven by `RelatedFieldListFilter.field_choices` → `field_admin_ordering` (`django/contrib/admin/filters.py:196-209` post-patch) | the modeled changed kernel (forward + reverse `get_choices` share it) |
| `restrictedChoices (defaultOrdering adminOrdering : List String)` | `RelatedOnlyFieldListFilter.field_choices` (`django/contrib/admin/filters.py:426-430` post-patch): now passes `ordering=field_admin_ordering(...)` into `field.get_choices(..., ordering=ordering)` | the value-restricted call site, routing its admin-configured ordering through the SAME kernel |

The pre-patch repo symbols the change corrects (refinement audit only, not in the
consumer spec view):
* `Field.get_choices`: `... .order_by(*ordering)` applied **unconditionally**
  (`django/db/models/fields/__init__.py:830` pre-patch) — an empty `ordering`
  clears the related model's `Meta.ordering` (`QuerySet.order_by()` with no args
  removes ordering).
* `ForeignObjectRel.get_choices`: `self.related_model._default_manager.order_by(*ordering)`
  unconditionally (`django/db/models/fields/reverse_related.py:125` pre-patch).
* `RelatedOnlyFieldListFilter.field_choices`: omitted the `ordering` kwarg
  entirely (`django/contrib/admin/filters.py:422` pre-patch), so its choices were
  never ordered by the configured ordering.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an ordering specification — the `ordering` kwarg / `Meta.ordering`, a tuple of field-name strings (possibly `'-'`-prefixed) e.g. `('name',)`, `('-pos', 'name')`, `()` | `List String` | Python tuple `t` of field-name strings ↔ `List String` with the same elements in the same order; empty tuple `()` ↔ `[]`; `bool(ordering)` (Python truthiness) ↔ `¬ requested.isEmpty` |
| `QuerySet.order_by(*ordering)` then iterate (the materialization) | the unchanged shared continuation, NOT modeled | applied identically on both the pre- and post-patch branches once the ordering specification is selected; G-CONF supplies it concretely as a stable multi-key sort (`shadow_order`) and the oracle supplies it as the real SQLite `ORDER BY` |
| `bool(ordering)` truthiness guard `if ordering:` | `requested.isEmpty` test | a Python ordering tuple is falsy iff empty; `effectiveOrdering` branches on `requested.isEmpty`, the exact analogue |

The carrier is `List String` because an ordering specification is a sequence of
ordering keys and the only operations on it are emptiness-test and verbatim
pass-through; element structure (field names, `-` prefixes) is opaque to the
kernel and is exercised concretely by G-CONF.

## 3. Callee provenance — no axioms, no deep-model references

There is **no `axiom` declaration and no A-reference** in this bundle, so there
is **no `axiom_check.py`** and **G-AX is skipped** (gates.py `gate_ax`: skip when
`axiom_check.py` absent).

The only callee beyond the modeled kernel is the materialization
`QuerySet.order_by(*ordering)` + iteration that turns the selected ordering
specification into an ordered row sequence. It is:

* **UNCHANGED** by the patch — both the pre- and post-patch code reach the very
  same `.order_by(*ordering)` / iteration; the patch changes only *which*
  ordering specification is handed to it (guarded vs unconditional), never the
  materialization itself.
* **a shared continuation reached identically on both branches** — so the spec
  needs to assume nothing about it. It is therefore neither consumed as an axiom
  (the proof never uses an `ensures` about it) nor deep-modeled as an A-reference
  (no Lean model is validated equal to it). Modeling it would be a dead axiom
  (SPEC_GUIDE §3, directive 7).

`restrictedChoices` calls `orderedChoices` as a **callee-under-spec**
(`let out ← orderedChoices …`); `prove_correct` discharges it via the generated
`orderedChoices_correct` (SPEC_GUIDE §3 multi-site), not via an axiom.

### Flag / behaviour dependency
The selection turns on Python truthiness of the `ordering` tuple (`if ordering:`).
An empty tuple is the only falsy ordering value the call sites can produce
(`field_admin_ordering` returns either `related_admin.get_ordering(request)` or
`()`; `Meta.ordering` defaults to `()`), so emptiness is the exact and total
trigger. G-CONF sweeps empty and non-empty orderings on both sites, with and
without a non-empty `Meta.ordering` default.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11400`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`effectiveOrdering` (the only R/I-tagged op) to Python and applies the unchanged
materialization concretely (a stable multi-key sort matching SQLite's `ORDER BY`
over distinct-valued columns); there are no A-tagged ops to leave as a real
callee.
