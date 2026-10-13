# refinement.md — django__django-15280

The operation-by-operation correspondence between `model.py`'s implementation
(the `link_children_to_parents` impl region and the deep `linked_parent` map)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == a real
callee by axiom_check.py / G-AX), or **I** (identical concrete operation). The
claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested inputs, so
it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reverse-relation population loop — `get_prefetch_queryset`

Gold hunk (`django/db/models/fields/related_descriptors.py:646-651`):

```
  for rel_obj in queryset:
-     instance = instances_dict[rel_obj_attr(rel_obj)]
-     setattr(rel_obj, self.field.name, instance)
+     if not self.field.is_cached(rel_obj):
+         instance = instances_dict[rel_obj_attr(rel_obj)]
+         setattr(rel_obj, self.field.name, instance)
```

| # | model.py impl op (`link_children_to_parents`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | iterate `i` over `range(len(slot_value))` | `for rel_obj in queryset` | R | the prefetched child collection ↔ indices `0..len-1` of the parallel lists; child i ↔ `rel_obj` at position i (mapping.md §2). Order is irrelevant to the result because each child's slot is independent. |
| A2 | `slot_full[i] != 1` (the loop guard) | `not self.field.is_cached(rel_obj)` | I + R | the slot-occupancy test is the **new** guard the patch adds; `is_cached` is an UNCHANGED 2-line dict-membership op (`FieldCacheMixin.is_cached`, mapping.md §3) modelled DIRECTLY as the 0/1 flag `slot_full[i]` (R: `bool ↔ {0,1}`). It is not axiomatized — its semantics (key membership) are concrete and spelled out; its fidelity is G-AX-checked, not consumed. |
| A3 | `slot_value[i] = supplied[i]` (only when the guard holds) | `instance = instances_dict[rel_obj_attr(rel_obj)]; setattr(rel_obj, self.field.name, instance)` | I + R | the slot write. `instances_dict[rel_obj_attr(rel_obj)]` ↔ `supplied[i]` (the parent supplied for child i, R: parent object ↔ int id). `setattr(rel_obj, self.field.name, instance)` routes through the forward descriptor `__set__` → `set_cached_value(rel_obj, instance)`, i.e. it stores the parent into the child's parent slot — modelled DIRECTLY as `slot_value[i] = supplied[i]` (mapping.md §3). Unchanged callees, concrete, not axiomatized. |

There is **no consumed axiom** and **no A-reference deep model of a *changed*
op**: the only thing that changed is the addition of the guard A2 (concrete int
comparison) around the existing concrete write A3. Both `is_cached` and
`setattr→set_cached_value` are unchanged dict operations modelled exactly (kind
I under the type refinement R); axiom_check.py validates that the parallel-list
abstraction reproduces the real `FieldCacheMixin` (G-AX), but the proof consumes
no `@ContractOnly`.

The discriminating content of the change — a child whose parent slot is ALREADY
populated (by a separately fetched child→parent collection, e.g. the nested
`Prefetch('house', …)`) must NOT be overwritten by the outer collection's parent
— lives in `linked_parent(was_full=1, old_value, supplied) == old_value` (model)
⇔ the `if not self.field.is_cached(rel_obj)` guard (real). The pre-patch code
overwrote unconditionally; `model_prepatch.py` reproduces that (drops the guard:
`slot_value[i] = supplied[i]` for every i) and **fails** the loop invariant /
postcondition

  `slot_value[k] == linked_parent(slot_full[k], Old(slot_value[k]), supplied[k])`

precisely on a populated slot whose `supplied[k] ≠ Old(slot_value[k])` — exactly
the spec sensing the change (G-DIFF). This is the same mechanism the F2P test
`test_nested_prefetch_is_not_overwritten_by_related_object` observes: after the
fix, `Room.house.is_cached(self.room)` is `True` and accessing
`house.rooms.first().house.address` runs 0 queries (the nested-prefetched, more
specific parent survives); before the fix it was clobbered by the outer parent
(which had `only('name')`, so `address` was deferred) and a query fired.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the
addition of an occupancy guard around the slot write — is an ordinary integer
comparison plus a conditional store, modelled **directly** (A2/A3 spelled out in
the verified loop), not hidden behind an axiom. There is no `@ContractOnly`
axiom in this bundle (A-consumed: none) and no deeply-modelled *changed* callee
to validate (A-reference: none); the unchanged `FieldCacheMixin` operations the
loop drives are kind-I and their abstraction fidelity is the only thing G-AX
checks (axiom_check.py).

## C. verify(model) ⇒ resolved

`link_children_to_parents` verifies only if, for every child, its slot after the
loop equals `linked_parent(slot_full[i], Old(slot_value[i]), supplied[i])` —
i.e. a populated slot is preserved and an empty slot receives the supplied parent
(A2 guard + A3 guarded write). By R (child collection ↔ indices; `bool ↔ {0,1}`;
parent object ↔ id; `setattr`→slot store) the verified loop is exactly the
post-patch loop, and by G-AX the parallel-list abstraction reproduces the real
`FieldCacheMixin` driving that loop. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ) plus the executable fidelity of the kind-I cache abstraction
(axiom_check.py / G-AX); there is no axiom-soundness trust point because the
bundle consumes no axiom.
