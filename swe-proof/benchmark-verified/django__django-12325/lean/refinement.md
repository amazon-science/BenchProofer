# refinement.md — django__django-12325

Maps every operation in `implementation_collectParentLinks` to its `patch.diff`
counterpart in `ModelBase.__new__` (`django/db/models/base.py`, the parent-link
collection block). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch parent-link block)
```python
parent_links = {}
for base in reversed([new_class] + parents):
    if not hasattr(base, '_meta'):
        continue
    if base != new_class and not base._meta.abstract:
        continue
    # Locate OneToOneField instances.
    for field in base._meta.local_fields:
        if isinstance(field, OneToOneField) and field.remote_field.parent_link:   # gold adds the conjunct
            related = resolve_relation(new_class, field.remote_field.model)
            parent_links[make_model_tuple(related)] = field
```
The modeled value is the final `parent_links` dict: the related-model-keyed
mapping of parent-link fields. The candidate-field stream (`fields`) is the
in-order concatenation of `base._meta.local_fields` over the visited bases; the
per-field attributes are supplied as `FieldInfo` data (mapping.md). The base
selection (outer loop + the two `continue`s) is unchanged by the patch and is
folded into which fields appear in `fields`.

## Operation correspondence
| # | Lean op (`implementation_collectParentLinks`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut parentLinks : List (String × FieldInfo) := []` | `parent_links = {}` | R | empty dict ↔ empty assoc list (last-write-wins model, mapping.md). |
| 2 | `for field in fields do` | `for field in base._meta.local_fields:` (across visited bases) | I/R | iterate candidate fields in order; the visited-base concatenation is the `fields` input (mapping.md), order preserved. |
| 3 | `if field.isOneToOne && field.parentLink then` | `if isinstance(field, OneToOneField) and field.remote_field.parent_link:` | R | `isinstance(field, OneToOneField)` ↔ `field.isOneToOne : Bool`; `field.remote_field.parent_link` ↔ `field.parentLink : Bool`; Python `and` ↔ Lean `&&`. This is the GOLD edit — the `parentLink` conjunct. |
| 4 | `parentLinks := dictInsert parentLinks field.relatedKey field` | `parent_links[make_model_tuple(resolve_relation(new_class, field.remote_field.model))] = field` | R | the dict key `make_model_tuple(resolve_relation(...))` ↔ `field.relatedKey : String` (enters as data, mapping.md); the assignment (last-write-wins) ↔ `dictInsert` (drop prior entry for key, append). The deep-modeled overwrite semantics are the crux of the fix. |
| 5 | `return parentLinks` | the completed `parent_links` dict | I | return the built mapping. |

Every op is R or I; **no A row** (no axiom consumed; `isinstance`,
`resolve_relation`, `make_model_tuple`, `parent_link` enter as `FieldInfo` data,
and the guarded last-write-wins insertion is modeled deeply as `dictInsert`).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against `patch.diff` behavior over ≥10^5 fuzzed inputs.
`conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the guard is `if isinstance(field, OneToOneField):` — every
one-to-one field is recorded into `parent_links` keyed by its related-model
identity, last-write-wins. When a model declares two one-to-one relations to the
SAME base (one the real parent link, one an ordinary relation declared later),
the later non-parent-link field OVERWRITES the genuine parent-link entry for that
key. `_prepare` then promotes the wrong field to the pk and raises
`ImproperlyConfigured: Add parent_link=True to …` (or, with `primary_key=True`,
silently mis-wires the inheritance).

`Solution_prepatch.lean` mirrors this exactly: the impl guard is `if
field.isOneToOne then` (no `parentLink` conjunct). It therefore records
non-parent-link one-to-one fields and, on the discriminating input, produces a
mapping whose entry for a shared key is a non-parent-link field rather than the
parent link the post-patch code keeps. It cannot satisfy
`problem_spec_collectParentLinks` (`result = buildParentLinks fields`) whenever a
key is shared by a parent-link field and a later non-parent-link one-to-one field
— precisely the FAIL_TO_PASS shape (`test_onetoone_with_parent_model`,
`test_clash_parent_link`: a child with both `*_ptr` parent link and an
`other_*` plain OneToOne to the same parent). G-DIFF: the prepatch fails
verification.

### Second gold hunk (`options.py`) — not an independent behavior
The gold also removes the now-dead `if not field.remote_field.parent_link: raise
ImproperlyConfigured(...)` guard in `Options._prepare`. With the corrected
`__new__` mapping recording only parent-link fields, the field `_prepare`
promotes always has `parent_link=True`, so that `raise` is unreachable. Removing
unreachable code changes no observable behavior independently of hunk 1; it is a
consequence of fixing the mapping. Hence a single triple + single prepatch suffice
(no `Solution_prepatch_2.lean`).
