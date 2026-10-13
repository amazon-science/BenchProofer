# mapping.md — django__django-12663

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fa5e7e46d875d4143510944f19d79df7b1739bab`, states the type
abstraction (the Lean↔Python bijection used by G-CONF and G-AX), and gives the
provenance of the deep-model reference (the real attribute / truthy-fallback
semantics the deep model is validated against).

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `outputFieldIdentity (sel)` | `Query.output_field` property, the `len(self.select) == 1` branch — `django/db/models/sql/query.py:234-236` | the modeled changed function: the single-selection output-field choice |
| `Selection` (structure) | the single selected item `self.select[0]`, a `django.db.models.expressions.Col` — `django/db/models/expressions.py:763` | minimal model of the selected item, exposing only the two touched field notions |
| `Selection.source` (`Int`) | `Col.target` — `django/db/models/expressions.py:772` (`self.alias, self.target = alias, target`) | the underlying, relation-aware source field of the column |
| `Selection.field` (`Int`) | `Col.field` = `Expression.field` property → `self.output_field` — `django/db/models/expressions.py:260-262` | the resolved output field of the selected item |

The unchanged second branch of `output_field` (`elif len(self.annotation_select)
== 1: return next(iter(self.annotation_select.values())).output_field`,
`query.py:237-238`) is NOT touched by the patch and is not modeled — only the
`len(self.select) == 1` branch changes.

### 1.1 What `Col.target` vs `Col.field` are (the heart of the change)

`Col.__init__(self, alias, target, output_field=None)`
(`expressions.py:768-772`):
```python
def __init__(self, alias, target, output_field=None):
    if output_field is None:
        output_field = target
    super().__init__(output_field=output_field)
    self.alias, self.target = alias, target
```
- `self.target` is the source field the column was built from (a relation-aware
  field — e.g. a `ForeignKey`/related field that knows how to coerce a deferred
  stand-in into a concrete related instance via its `get_prep_value`).
- `Col.field` is `Expression.field`, a property aliasing `self.output_field`
  (`expressions.py:260-262`: `def field(self): return self.output_field`).
- When `Col` is built WITHOUT an explicit `output_field`, `output_field` defaults
  to `target`, so `Col.field == Col.target` — the two notions coincide.
- When `Col` is built WITH an explicit `output_field` that differs from `target`
  (the nested-subquery case in the issue, where the resolved field becomes the
  bare primary-key/integer field), `Col.field != Col.target`. The pre-patch code
  returned `Col.field` (the relation-unaware resolved field) and a comparison
  RHS such as a `SimpleLazyObject` deferred stand-in could not be coerced; the
  fix returns `Col.target` (the relation-aware field), which can.

The patched expression `getattr(select, 'target', None) or select.field`:
- `getattr(select, 'target', None)` → `Col.target` for a `Col` (the attribute is
  always present on a `Col`); `None` for a non-`Col` selected expression that has
  no `target` attribute.
- `... or select.field` → falls back to the resolved field when `target` is
  absent (`None`) or falsy.

## 2. Type abstraction (R-refinements)

| repo reality | Solution.lean carrier | bijection |
|---|---|---|
| a selected item `self.select[0]` (a `Col` / `Expression`) | `Selection` structure with two `Int` field-identity fields | the only observed aspects of the item are *which* field its `target` is and *which* field its `field`/`output_field` is; field objects are modeled by integer identities |
| `getattr(select, 'target', None)` (the related/source field, or `None` if absent, or a falsy value) | `sel.source : Int`, sentinel `0` ≡ "no usable source field" (attribute absent OR falsy); any nonzero ≡ a usable, distinct source field | `0` ↔ "`getattr(...) or` short-circuits to the fallback"; nonzero ↔ "`getattr(...)` is truthy and is returned" |
| `select.field` (the resolved output field, `Expression.field` → `output_field`) | `sel.field : Int`, always nonzero (`require sel.field ≠ 0`) | the resolved output field is always a real, usable field — never falsy |
| the returned field object (used downstream as `lhs.output_field`) | the returned `Int` identity `r` | the choice of field is observed only through which field object is returned |

A field identity is carried by integer identity; the contract quantifies over
all `sel.field ≠ 0` and all `sel.source` (including the sentinel `0`), not any
literal value.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed axiom**. The changed operation — choose the source field
when usable, else the resolved field — is modeled **deeply** (the
`if source ≠ 0 then return source else return sel.field` skeleton, mirroring
`getattr(select, 'target', None) or select.field`).

The semantics this deep model stands on are the **A-reference**, validated equal
to the real Python behaviour by `axiom_check.py` (G-AX):

1. **The `getattr(obj, 'target', None) or obj.field` primitive** has exactly the
   modeled choose-one semantics: returns `obj.target` when present and truthy;
   returns `obj.field` when `target` is absent or falsy. (Pure Python truthy
   short-circuit; checked directly over a fuzzed truthiness matrix.)
2. **The real `Query.output_field` (post-patch) on a single-selection query**
   returns `select.target` for a `Col` whose `target` is truthy (the usual
   case) and falls back to `select.field` only when there is no usable target —
   matching `outputFieldIdentity`. axiom_check.py builds real Django `Col`
   objects (both with and without an explicit, differing `output_field`),
   installs each as the sole `self.select` of a real `Query`, and asserts the
   property returns the `target` field — i.e. that `Col.field != Col.target`
   exactly when an explicit override is given, the discriminating regression in
   the issue.

Provenance: `django/db/models/sql/query.py:234-236` (the property),
`django/db/models/expressions.py:763-772` (`Col.__init__`, `Col.target`),
`expressions.py:260-262` (`Expression.field` → `output_field`). The reference
is checked in-container against the real interpreter; exit 0 iff sound.

## 4. G-CONF fuzz seed

`conformance_check.py` differential-tests the R/I shadow of the `do` block (the
modeled `source if source != 0 else field` choice) against the patched source
line `getattr(select, 'target', None) or select.field`, transliterated with the
`Int`-identity bridge (`source`/`field` integer identities; `0` ≡ falsy/absent).
Pinned seed: **12663**. ≥10⁵ fuzzed `(source, field)` pairs plus boundary cases.
