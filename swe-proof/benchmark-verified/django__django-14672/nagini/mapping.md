# mapping.md — django__django-14672

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 00ea883ef56fb5e092cbe4a6f7ff2e7470886ac4`, states the type
abstraction, and gives the provenance of the deep-model reference (callee
source + the exact behaviour the deep model is validated against).

Repo file under change: `django/db/models/fields/reverse_related.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `identity_name_component(names)` | the through-fields slot of `ManyToManyRel.identity` — `django/db/models/fields/reverse_related.py:310-315` (the `self.through_fields` element of the returned identity tuple, body line 313) | the modeled changed operation: the value the intermediate-field-names collection contributes to the relation's identity tuple |
| `canonical_names`, `canonical_items` *(deep model — A-reference)* | `django.utils.hashable.make_hashable` — `django/utils/hashable.py:4` (called on `self.through_fields` post-patch, line 313) | unchanged community callee the patch wraps `self.through_fields` with; modeled deeply (list→tuple, None→None, order/element preserving) and validated `== make_hashable` by axiom_check.py (G-AX) |
| `is_hashable(v)` | the implicit requirement of `ManyToManyRel.__hash__` — `reverse_related.py:138-139` (`return hash(self.identity)`) | pure spec: a value may participate in a hash iff it is not a mutable sequence (a Python `list` is unhashable) |
| `Value(kind, items)` | a runtime value as it enters the identity tuple | minimal carrier: a kind tag (absent / mutable list / immutable tuple) faithfully reflecting the runtime type, plus its element sequence |
| `KIND_ABSENT / KIND_MUTABLE / KIND_IMMUTABLE` | the runtime types `NoneType` / `list` / `tuple` | the three kinds the through-fields slot can take |

The `identity` property is consumed by `__hash__` (`hash(self.identity)`,
line 139) and `__eq__` (`self.identity == other.identity`, line 136), both
inherited from `ForeignObjectRel` (lines 133-139). `ManyToManyRel.identity`
(lines 309-315) extends `super().identity` (line 119-131, which already wraps
`limit_choices_to` with `make_hashable`, line 126) with the m2m-specific
components `self.through`, `self.through_fields`, `self.db_constraint`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.through_fields`: `Optional[list/tuple of str]` (e.g. `['event', 'invitee']`, or `None`) | `Optional[List[int]]` (field names as `int` atoms; `None` for absent) | each name string ↔ an `int` atom (names are opaque, compared only for equality and order); a `list`/`tuple` of names ↔ a `List[int]`; `None` ↔ `None`. The F2P inputs are lists of strings. |
| a runtime value entering the identity tuple | `Value(kind, items)` | `kind == KIND_ABSENT` ↔ `None`; `kind == KIND_MUTABLE` ↔ a `list`; `kind == KIND_IMMUTABLE` ↔ a `tuple`; `items` ↔ the element sequence (`ToSeq`/`PSeq`) |
| hashability of the value | `is_hashable(v)` = `v.kind != KIND_MUTABLE` | a Python `list` is the only one of the three kinds that raises `TypeError` under `hash()`; `None` and `tuple` (of hashable atoms) are hashable |
| the other identity components (`self.through`, `self.db_constraint`, and the `super().identity` prefix) | omitted | unchanged by the patch; already hashable (a model string / a bool / the existing make_hashable-wrapped prefix). Only the through-fields slot changed, so only it is modeled. |

`str` indexing/iteration is banned in Nagini, so names are `int` atoms and the
collection is `List[int]`; element ordering is carried by `PSeq[int]` via
`ToSeq`.

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `canonical_names` / `canonical_items` deep model ↔ `make_hashable` (A-reference)
**Callee:** `django.utils.hashable.make_hashable(value)` — `django/utils/hashable.py:4-24`. The changed operation (wrapping `self.through_fields`) is modeled **deeply** by the `@Pure` functions `canonical_names` (the resulting kind) and `canonical_items` (the resulting element sequence) over the `Value` carrier; there is **no consumed axiom**. The deep model is validated equal to the real callee out-of-band by axiom_check.py (G-AX). Source:

```python
def make_hashable(value):
    if isinstance(value, dict):
        return tuple([(key, make_hashable(nested_value))
                      for key, nested_value in sorted(value.items())])
    try:
        hash(value)            # hashable iterables (str, frozenset, tuple) pass through
    except TypeError:
        if is_iterable(value):
            return tuple(map(make_hashable, value))   # a list -> a tuple
        raise
    return value
```

For `self.through_fields` the only cases that arise are:

  * `None` — `hash(None)` succeeds, so `make_hashable(None) is None` (absent
    stays absent, hashable);
  * a `list` of name strings — `hash([...])` raises `TypeError`, the value is
    iterable, so it becomes `tuple(map(make_hashable, value))`; each name is a
    hashable `str`, so it is left untouched and the result is the same names,
    in order, as a `tuple` (immutable, hashable);
  * an already-immutable `tuple` of names — `hash` succeeds, returned
    unchanged (still a hashable tuple of the same names).

Hence the deep model: `canonical_names(None) == KIND_ABSENT`,
`canonical_names(list) == KIND_IMMUTABLE`; `canonical_items` is the identity on
the element sequence (empty for `None`). G-AX asserts the real
`make_hashable` produces a hashable value whose kind and element sequence match
the deep model on boundary + 20 000 fuzz inputs, and confirms the **defect**:
the raw mutable list (the pre-patch component) is NOT hashable.

This component is a `list` precisely when the user passes `through_fields` as a
list (Django's own test models do: `through_fields=['event', 'invitee']`); it
is a `tuple` or `None` otherwise. The pre-patch identity carried the raw list,
so `hash(self.identity)` raised `TypeError: unhashable type: 'list'` — observed
when a model is checked (e.g. a proxy/inherited model whose reverse m2m field is
placed in a set during `_check_field_name_clashes`). Docs / provenance:
`django/utils/hashable.py`; the sibling `make_hashable(self.limit_choices_to)`
already present in `ForeignObjectRel.identity` (line 126).

**Soundness check (G-AX):** `axiom_check.py` imports the standalone
`django.utils.hashable.make_hashable` (no Django settings required — it only
pulls in `is_iterable`) and runs it on `None`, empty/non-empty lists of
name-like strings (including the F2P `['event', 'invitee']`), already-immutable
tuples, and 20 000 randomized fuzz collections. It asserts (1) the result is
always hashable, (2) the kind matches `canonical_names`, (3) the element
sequence matches `canonical_items` in order, (4) equal collections hash equally,
and (5) the raw mutable list is unhashable (the pre-patch defect). Exit 0 iff
sound.
