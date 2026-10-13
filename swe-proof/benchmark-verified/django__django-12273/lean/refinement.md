# refinement.md — django__django-12273

Maps every operation in `implementation_setPrimaryKey` to its `patch.diff`
counterpart (the body of `Model._set_pk_val`, `django/db/models/base.py`). Tags:
**R** type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled used callee validated == real callee, **I** identical concrete op.

## Patch (post-patch `_set_pk_val`)
```python
def _set_pk_val(self, value):
    for parent_link in self._meta.parents.values():
        if parent_link and parent_link != self._meta.pk:
            setattr(self, parent_link.target_field.attname, value)
    return setattr(self, self._meta.pk.attname, value)
```

## Operation correspondence
| # | Lean op (`implementation_setPrimaryKey`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut s := store` | the instance's attribute store (`getattr`/`setattr` target) | I | the accumulator is the object's attribute map; updates are pure `setAttr`. |
| 2 | `for link in ancestorLinks do` | `for parent_link in self._meta.parents.values():` | R | `self._meta.parents.values()` (ordered ancestor parent-links) ↦ `ancestorLinks : List AncestorLink`, order-preserving (mapping.md). |
| 3 | `if link.linked && !link.sameAsPrimaryKey then` | `if parent_link and parent_link != self._meta.pk:` | R | `parent_link` truthiness ↦ `linked`; `parent_link != self._meta.pk` ↦ `!sameAsPrimaryKey`. A `None`/absent link ⇒ `linked = false`; a link equal to the own pk ⇒ `sameAsPrimaryKey = true`. |
| 4 | `s := setAttr s link.keyName value` | `setattr(self, parent_link.target_field.attname, value)` | I | write the ancestor-key attribute (`target_field.attname` ↦ `keyName`) to `value`; pure functional store update. |
| 5 | `s := setAttr s primaryKeyName value` | `return setattr(self, self._meta.pk.attname, value)` | I | the always-applied own primary-key write (`self._meta.pk.attname` ↦ `primaryKeyName`). |

Every op is **I** (concrete attribute-store update / control flow) or **R** (the
metadata-list and flag type-refinements declared in mapping.md). There is **no
A-consumed row** and **no A-reference row**: nothing is axiomatized and no callee
is deep-modeled — `target_field.attname`, `pk.attname` and `parents.values()` are
unchanged metadata accessors that supply the function's INPUTS, not computed
callees. Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a `status=skip` stub.

## conf_skip
`conf_skip = false`. The impl region is all R/I, so `conformance_check.py` runs a
real cross-language differential test: it builds the R/I shadow of
`implementation_setPrimaryKey` in Python (loop over ancestor links, guard on
`linked && !sameAsPrimaryKey`, `setAttr` each ancestor key, then the own pk) and
diffs the resulting store against an independent reconstruction of the post-patch
`_set_pk_val` behavior over ≥10⁵ fuzzed (store, primaryKeyName, ancestorLinks,
value) inputs. Zero disagreements required.

## Prepatch = the real bug
Pre-patch, `_set_pk_val` is just `return setattr(self, self._meta.pk.attname,
value)` — it assigns ONLY the object's own primary-key attribute and never
touches the ancestor-key attributes. The prepatch impl
(`implementation_setPrimaryKey := s := setAttr s primaryKeyName value`) is exactly
this. It cannot satisfy `problem_spec_setPrimaryKey` whenever a qualifying
ancestor link exists (`linked ∧ ¬sameAsPrimaryKey`): the spec then writes that
ancestor key to `value` (via `applyLinks`) while the buggy impl leaves it at its
old value. This is precisely the FAIL_TO_PASS behavior: setting `pk = None` on an
inherited object must clear the ancestor key (`user_ptr_id` /
`politician_ptr_id`) too, so that `save()` creates a NEW row instead of
overwriting the original (`test_create_new_instance_with_pk_equals_none`,
`…_multi_inheritance`). The carried gold proof body (`unfold; simp [Id.run]; rfl`)
fails to typecheck against the buggy impl (G-DIFF), confirmed by `lean_verify`
exit 1.
