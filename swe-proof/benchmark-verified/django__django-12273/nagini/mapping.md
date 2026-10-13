# mapping.md — django__django-12273

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 927c903f3cd25c817c21738328b53991c035b415`, states the type
abstraction, and gives the provenance of the metadata the deep model reads.

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assign_identity(store, target, active, pk_idx, value)` | `Model._set_pk_val(self, value)` — `django/db/models/base.py:571` (reached via the `pk` property setter, `pk = property(_get_pk_val, _set_pk_val)`, `base.py:574`) | the modeled changed function (the primary-key value setter) |
| `store` | the instance's mutable attribute store (`self.__dict__`, accessed by `setattr(self, <attname>, value)`) | the slot values the operation writes |
| `pk_idx` | the slot of `self._meta.pk.attname` | identity slot index |
| `target[k]` | the slot of `parent_link.target_field.attname` for the k-th entry of `self._meta.parents.values()` | linked identity slot index |
| `active[k]` | `1` iff `parent_link and parent_link != self._meta.pk` (the patch guard) for the k-th parent link | whether the k-th linked slot is written |
| `value` | the `value` argument of `_set_pk_val` | the assigned identity value |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| an instance's attribute store `self.__dict__`, written by `setattr(self, attname, value)` | `store: List[int]` indexed by a fixed attname→slot layout | `getattr(self, attname)` ↔ `store[slot(attname)]`; `setattr(self, attname, value)` ↔ `store[slot(attname)] = value` |
| `self._meta.pk.attname` | `pk_idx: int` | the slot of the pk attname |
| `self._meta.parents` — an ordered dict `{parent_model: parent_link_field_or_None}` (`Options.parents`, `django/db/models/options.py:120`) | `target: List[int]` + `active: List[int]` (parallel, one entry per parent link) | `target[k] = slot(parents.values()[k].target_field.attname)`; `active[k] = 1` iff `parents.values()[k]` is truthy AND `!= self._meta.pk` |
| the assigned identity value (`None`, an int auto-pk, etc.) | `value: int` | the F2P assignments set `pk = None`; modeled as a single scalar `value` written into the touched slots — the propagation is value-agnostic, so any `int` witnesses it (axiom_check fuzzes `None` and ints) |

Slot model justification: `_set_pk_val` only ever reads `self._meta.pk.attname`,
`self._meta.parents.values()`, and each parent link's `target_field.attname`,
and only ever writes those attnames via `setattr`. Modeling the store as a
`List[int]` indexed by attname is therefore a faithful 1:1 abstraction of the
exact attributes the operation touches. `value` is treated as opaque content
(the propagation does not depend on it), so an `int` carrier suffices.

## 3. Callee provenance (the metadata the deep model reads)

There is **no consumed `@ContractOnly` axiom**: the changed operation is the
slot-write cascade itself, which is modeled DEEPLY in `assign_identity`'s impl.
The three pieces of `_meta` the operation consults are unchanged structural
metadata; they appear in the model only as the read-only inputs `target`,
`active`, `pk_idx`, whose correspondence to reality is validated by
`axiom_check.py` (G-AX), not assumed by an axiom.

### 3.1 `parent_link.target_field.attname`
`ForeignObject.target_field` (`django/db/models/fields/related.py:879`) returns
`self.foreign_related_fields[0]`, the single related (parent) primary-key field;
`.attname` is the field's attribute name (`Field.attname`, set in
`Field.set_attributes_from_name`, `django/db/models/fields/__init__.py:745`). For
an auto-created parent link `<base>_ptr`, the target field is the base model's
pk and the attname is e.g. `user_ptr_id` / `politician_ptr_id`. Unchanged by the
patch.

### 3.2 `self._meta.parents` and the guard
`Options.parents` (`options.py:120`) maps each concrete ancestor model to the
`OneToOneField(parent_link=True)` linking to it, or `None` for proxy/abstract
links. When a child declares no own pk, the first parent link is *promoted* to
be the pk (`options.py:241-253`); in that case that parent link **is**
`self._meta.pk`, which is exactly why the patch guard excludes
`parent_link != self._meta.pk` (otherwise it would redundantly re-target the pk
through its own parent attname). The `parent_link and …` half excludes the
`None` entries. Both are encoded by `active[k]`.

### 3.3 Soundness check (G-AX) — the A-reference
`axiom_check.py` builds two structural twins of the F2P models inside the
container:
- single inheritance with an own pk (`Child(Ancestor)` ≅ `Profile(User)`): one
  active parent link distinct from the own pk;
- multi inheritance with a promoted pk (`MultiChild(LeftParent, RightParent)` ≅
  `Congressman(Person, Politician)`): one parent link that IS the promoted pk
  (excluded by the guard) and one distinct active linked slot.

For each it derives `pk_attname` / `active_targets` from the **real** `_meta`
the same way the model abstracts them, drives the **real** patched
`instance.pk = value` (the `pk` property setter → `_set_pk_val`) over a sweep of
values (`None`, small/large/negative ints), and asserts the three contract
obligations slot-for-slot: (1) the pk attname holds `value`; (2) every active
linked target attname holds `value` (the cascade); (3) every other attname is
unchanged. Exit 0 iff the deep model equals the real operation on every
observation. It imports only Django (the very module the patch lives in) and
the stdlib.
