# mapping.md — django__django-15280

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 973fa566521037ac140dcece73fceae50ee522f1`, states the type
abstraction, and gives the provenance of the cache machinery the model abstracts.

Repo file under change: `django/db/models/fields/related_descriptors.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `link_children_to_parents(slot_full, slot_value, supplied)` | the reverse-relation population loop inside `create_reverse_many_to_one_manager().<locals>.RelatedManager.get_prefetch_queryset` — `django/db/models/fields/related_descriptors.py:648-650` | the modeled changed code: the loop that links each prefetched child back to its parent |
| `slot_full[i]` (0/1 occupancy flag) | `self.field.is_cached(rel_obj)` — `FieldCacheMixin.is_cached`, `django/db/models/fields/mixins.py:21-22` | per-child: whether the child's parent-field cache slot is already populated |
| `slot_value[i]` (stored parent id; -1 sentinel = empty) | the child's parent-field cache entry `rel_obj._state.fields_cache[cache_name]`, written by `setattr(rel_obj, self.field.name, instance)` → forward descriptor `__set__` → `self.field.set_cached_value(rel_obj, instance)` (`related_descriptors.py:261`, `mixins.py:24-25`) | per-child: the parent currently linked into the child's slot |
| `supplied[i]` (parent id) | `instance = instances_dict[rel_obj_attr(rel_obj)]` — the parent the current collection would link child i to (`related_descriptors.py:649`, `instances_dict` built at line 642) | per-child: the parent supplied by THIS collection |
| `linked_parent(was_full, old_value, supplied)` | the post-state of the child's slot after the (fixed) loop body | pure spec: a populated slot keeps `old_value`; an empty slot receives `supplied` |

Pre-patch repo code the change guards (for the refinement audit, not referenced
from the consumer spec view):

```python
for rel_obj in queryset:
    instance = instances_dict[rel_obj_attr(rel_obj)]   # supplied[i]
    setattr(rel_obj, self.field.name, instance)        # unconditional slot write
```

Post-patch:

```python
for rel_obj in queryset:
    if not self.field.is_cached(rel_obj):              # guard: only empty slots
        instance = instances_dict[rel_obj_attr(rel_obj)]
        setattr(rel_obj, self.field.name, instance)
```

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the iterable `queryset` of prefetched child rows | indices `0..len-1` of three parallel `List`s | child i ↔ index i; the original code iterates `for rel_obj in queryset`, the model iterates `i` over `range(len(slot_value))` |
| `self.field.is_cached(rel_obj)` (a `bool`) | `slot_full[i] == 1` (a 0/1 `int`) | `True ↔ 1`, `False ↔ 0`; the precondition pins `slot_full[i] ∈ {0,1}` |
| the child's parent cache entry / "no entry" | `slot_value[i]` (parent id ≥ 0) / `slot_value[i] == -1` (sentinel) | an occupied slot holds the parent's identity (modelled as its integer id); an empty slot is the sentinel -1. The model never reads the sentinel where the slot is occupied, so the abstraction is exact. |
| the parent object `instances_dict[rel_obj_attr(rel_obj)]` | `supplied[i]` (parent id ≥ 0) | parent object ↔ its integer id; equality of parents ↔ equality of ids |
| `setattr(rel_obj, self.field.name, instance)` (slot write) | `slot_value[i] = supplied[i]` | the descriptor `__set__` ultimately does `set_cached_value(rel_obj, instance)`, i.e. it writes the child's parent slot (mapping.md §3); the model write is the same store |

`is_cached`/`set_cached_value` are **unchanged** stdlib-shaped dict operations
on `rel_obj._state.fields_cache`; the change neither defines nor modifies them.
They are modelled **directly** (kind I), not axiomatized: occupancy is the
`slot_full` flag, the write is the `slot_value` store. Their fidelity is checked
executably by `axiom_check.py` / G-AX (§3).

## 3. Cache-machinery provenance (kind-I — fidelity checked by G-AX / axiom_check.py)

**Source** (`django/db/models/fields/mixins.py:6-25`, `FieldCacheMixin`):

```python
class FieldCacheMixin:
    def get_cached_value(self, instance, default=NOT_PROVIDED):
        cache_name = self.get_cache_name()
        try:    return instance._state.fields_cache[cache_name]
        except KeyError:
            if default is NOT_PROVIDED: raise
            return default
    def is_cached(self, instance):
        return self.get_cache_name() in instance._state.fields_cache
    def set_cached_value(self, instance, value):
        instance._state.fields_cache[self.get_cache_name()] = value
```

A child's "slot" is therefore exactly one entry of
`instance._state.fields_cache`, keyed by the field's cache name:
- `is_cached(child)` is exactly key membership ⇒ modelled by `slot_full[i]`;
- `set_cached_value(child, parent)` is exactly setting that key ⇒ modelled by
  `slot_value[i] = supplied[i]`;
- `setattr(child, field.name, parent)` routes through the forward
  `ForwardManyToOneDescriptor.__set__` (`related_descriptors.py:203-267`) whose
  line 261 calls `self.field.set_cached_value(instance=child, value=parent)`, so
  the `setattr` populates **the same slot** that `is_cached` tests. (The
  descriptor also writes the foreign-key attname columns, lines 256-257, and —
  only for one-to-one fields — the reverse cache, lines 266-267; neither is the
  parent-slot the loop's guard consults, so neither affects whether the child's
  own parent slot is preserved. The F2P test observes only `Room.house` =
  `self.field.is_cached(room)` and the deferred-field state of the linked
  parent, both governed by the parent slot the model tracks.)

**Soundness/fidelity check (G-AX):** `axiom_check.py` exercises the REAL
`FieldCacheMixin` (imported in-container; a documented two-line reconstruction
is used only when Django is not importable) over boundary collections (empty,
single empty slot, single populated slot with supplied-differs / supplied-same,
mixed, all-populated, all-empty) plus 20 000 randomized child collections. For
every child it asserts the FIXED guarded loop yields
`linked_parent(was_full, old_value, supplied)` (populated ⇒ keeps `old_value`;
empty ⇒ takes `supplied`), and that the buggy unconditional write instead
clobbers every populated slot — the discriminating behaviour. Exit 0 iff every
observation matches the model. No flag dependency (plain dict membership/store).
