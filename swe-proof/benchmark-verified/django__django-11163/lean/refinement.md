# refinement.md — django__django-11163

Maps every operation in `implementation_modelToDict` to its `patch.diff`
counterpart in `model_to_dict` (django/forms/models.py:78-91). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch loop body)
```python
def model_to_dict(instance, fields=None, exclude=None):
    opts = instance._meta
    data = {}
    for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not getattr(f, 'editable', False):
            continue
        if fields is not None and f.name not in fields:     # was: if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = f.value_from_object(instance)
    return data
```

The single changed token is the inclusion guard: `if fields and …` →
`if fields is not None and …`. An empty Python list is falsy, so at base_commit
`fields=[]` made the guard `fields` false and the field was kept; post-patch
`fields is not None` is true for `[]`, so `f.name not in []` is true and the field
is skipped. I.e. an empty selection now admits NO field, whereas an absent
selection (`fields is None`) still admits all.

## Modeling decision
- `fields` / `exclude` (`Optional[list[str]]`) ↔ `Option (List String)`:
  `None ↔ none`, an explicit list `↔ some xs`. This bijection is exactly what
  distinguishes "absent" from "present-but-empty", which is the heart of the fix.
- The field walk `chain(opts.concrete_fields, opts.private_fields,
  opts.many_to_many)` ↔ a single ordered `fs : List (FieldRec α)`; the ordering is
  preserved and is the dict's insertion order.
- Each field object's three read attributes ↔ `FieldRec.name`,
  `FieldRec.editable`, `FieldRec.val`. `f.value_from_object(instance)` is unchanged
  by the patch and is not pinned to anything beyond "this field's value"; it is
  carried as the given attribute `FieldRec.val` (R), NOT axiomatized.
- The returned `dict` ↔ the ordered association list `List (String × α)` via
  `list(d.items())` (Python dict iteration order == insertion order).

## Operation correspondence
| # | Lean op (`implementation_modelToDict`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `for f in fs do` | `for f in chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):` | R | the concatenated field iterables ↔ one ordered `List (FieldRec α)`; order preserved. |
| 2 | `if !f.editable then continue` | `if not getattr(f, 'editable', False): continue` | R | skip non-editable; `editable : Bool` ↔ the (default-False) editable attribute. |
| 3 | `if let some sel := fields then if !(sel.contains f.name) then continue` | `if fields is not None and f.name not in fields: continue` | R | THE FIXED OP. `fields is not None` ↔ the `some` match; `f.name not in fields` ↔ `!sel.contains f.name`. An empty `sel` skips every field (`contains` is always false), mirroring `[] is not None`. |
| 4 | `if let some ex := exclude then if ex.contains f.name then continue` | `if exclude and f.name in exclude: continue` | R | unchanged exclusion. The Python truthy guard `exclude and …` is behavior-equivalent to `exclude is not None and …` here because `f.name in exclude` is already false for `exclude in (None, [])`; modeled as "present and contains the name". |
| 5 | `data := data ++ [(f.name, f.val)]` | `data[f.name] = f.value_from_object(instance)` | R | append the `(name, value)` pair; dict insertion ↔ list append (names are distinct in the field walk, so no overwrite). `f.val` ↔ `f.value_from_object(instance)`. |
| 6 | `return data` | `return data` | I | return the accumulated mapping. |

The behavior-changing op is #3. Pre-patch the inclusion guard treated a
present-but-empty selection as if no selection were supplied, so all fields were
kept; post-patch an empty selection keeps none. The prepatch impl encodes the
pre-patch quirk by adding `if !sel.isEmpty then` before the membership test, so an
empty `sel` imposes no constraint.

## List ↔ dict bijection (uniqueness invariant)
The result is modeled as an insertion-ordered `List (String × α)` and bound to the
Python `dict` via `list(d.items())`. This is a faithful bijection because the field
walk `chain(opts.concrete_fields, opts.private_fields, opts.many_to_many)` yields
field objects with DISTINCT `name`s (a model's field names are unique), so no dict
key is ever overwritten and `list(d.items())` preserves the walk order exactly.
G-CONF respects this domain invariant: each fuzzed field walk is built with unique
names (`rng.sample`), matching the real repo invariant. (On hypothetical duplicate
names the list model would keep both pairs while a dict would collapse them; that
input never arises in the modeled domain.)

## R/I legs ⇒ G-CONF
Every op is R or I — there is no axiomatized leg. G-CONF transliterates the impl
op-for-op into Python (`fields`/`exclude` as `None`/list, the field walk as a list
of duck-typed objects with deterministic per-field values) and differential-tests
it against the REAL patched `model_to_dict` over ≥10^5 fuzzed inputs, oversampling
the empty-`fields` and empty-`exclude` cases. `conf_skip = false`.

## No A-consumed / A-reference row
There is no `opaque` callee and no `axiom <callee>_prop`: `f.value_from_object` is
carried as the `FieldRec.val` attribute (R), not a callee contract the proof
consumes. So `meta.json axioms = []` and `deep_model_references = []`;
`axiom_check.py` is a skip stub.

## F2P alignment
The added F2P assertions (test_modelform_subclassed_model, model object with
editable fields `id, name, score, writer_ptr`):
- `model_to_dict(bw, fields=[])` must be `{}` → spec forces the result `[]`
  (an empty `some []` selection admits nothing). The prepatch keeps all fields,
  violating the discriminating clause.
- `model_to_dict(bw, fields=['id','name'])` → `id, name` only.
- `model_to_dict(bw, exclude=[])` → all fields (empty exclusion bars nothing).
- `model_to_dict(bw, exclude=['id','name'])` → `score, writer_ptr`.
- `model_to_dict(bw)` → all fields (absent selection admits all).
`patch.diff` (gold verbatim) makes the harness resolve.
