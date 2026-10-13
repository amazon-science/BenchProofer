# refinement.md — django__django-13401

Maps every operation in the three `implementation_*` skeletons to its
`patch.diff` counterpart in `Field.__eq__` / `__lt__` / `__hash__`
(`django/db/models/fields/__init__.py:516–541` @ base_commit). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference** op left
as the real repo callee in G-CONF (not axiomatized), **I** identical concrete op.

## Carrier refinement (applies to all three)
A real `Field` instance ↔ `FieldId`:
- `self.creation_counter : int` ↔ `creationCounter : Int`  (R)
- `getattr(self, 'model', None)` / `hasattr(self, 'model')` + `self.model._meta`
  ↔ `model : Option (String × String)` where `none ↔ no model attr` and
  `some (app_label, model_name) ↔ model attached with that `_meta` identity` (R).
  A Django model class is uniquely identified by `(_meta.app_label,
  _meta.model_name)`, so model-object identity comparison ↔ pair equality.

## `__eq__`  →  `implementation_fieldEq`
Post-patch:
```python
return (self.creation_counter == other.creation_counter and
        getattr(self, 'model', None) == getattr(other, 'model', None))
```
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `a.creationCounter == b.creationCounter` | `self.creation_counter == other.creation_counter` | R | Int ↔ int equality |
| 2 | `&& (a.model == b.model)` | `and getattr(self,'model',None) == getattr(other,'model',None)` | R | `Option (String×String)` equality ↔ model-object equality (incl. `None==None`) |

## `__lt__`  →  `implementation_fieldLt`
Post-patch (counter-first, then model identity):
```python
if (self.creation_counter != other.creation_counter or
        not hasattr(self,'model') and not hasattr(other,'model')):
    return self.creation_counter < other.creation_counter
elif hasattr(self,'model') != hasattr(other,'model'):
    return not hasattr(self,'model')
else:
    return ((self.model._meta.app_label, self.model._meta.model_name) <
            (other.model._meta.app_label, other.model._meta.model_name))
```
| # | Lean op (`fieldLtPure` body, mirrored in impl) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if a.creationCounter ≠ b.creationCounter ∨ (a.model.isNone ∧ b.model.isNone)` | `if self.creation_counter != other.creation_counter or not hasattr(self,'model') and not hasattr(other,'model')` | R | `isNone ↔ not hasattr(...,'model')`; Python `or`/`and` precedence: `!= or (not.. and not..)` |
| 2 | `return decide (a.creationCounter < b.creationCounter)` | `return self.creation_counter < other.creation_counter` | R | Int `<` ↔ int `<` |
| 3 | `else if a.model.isSome ≠ b.model.isSome then return a.model.isNone` | `elif hasattr(self,'model') != hasattr(other,'model'): return not hasattr(self,'model')` | R | exactly one attached → unattached first |
| 4 | `match … some ka, some kb => return keyLt ka kb` | `else: return ((app_label,model_name) < (...))` | R | lexicographic tuple `<` ↔ `keyLt` (compare app_label, then model_name). Both attached here, so `none` arms are unreachable. |

## `__hash__`  →  `implementation_fieldHashKey`
Post-patch:
```python
return hash((self.creation_counter,
             self.model._meta.app_label if hasattr(self,'model') else None,
             self.model._meta.model_name if hasattr(self,'model') else None))
```
| # | Lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `(a.creationCounter, a.model.map Prod.fst, a.model.map Prod.snd)` | the 3-tuple `(creation_counter, app_label?, model_name?)` argument to `hash(...)` | R | We model the injective HASH KEY (the tuple) rather than Python's opaque `hash()` int; the observable contract of `__hash__` is exactly that equal fields share, and distinct-identity fields are free to differ on, this key. `none ↔ None` for both components. |

`hash(...)` itself is NOT modeled/axiomatized — modeling the key tuple is the
faithful and stronger contract (it discriminates wherever the test relies on hash
distinctness). Tagged R, not A.

## Summary
- All operations are **R** (carrier/type refinement) or trivially **I**.
- No **A-consumed** axioms, no **A-reference** deep-model callees.
- No changed-inexpressible op: every read/comparison is total over `FieldId`.
- conf_skip = false (impl region is all-R, not all-A): G-CONF differential-tests
  all three legs against the real patched methods.
