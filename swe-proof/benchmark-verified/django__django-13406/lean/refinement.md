# refinement.md — django__django-13406

Maps every operation in `implementation_installQuery` to its `patch.diff`
counterpart in the `QuerySet.query` setter (django/db/models/query.py:211-213).
Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** op left as the real repo callee in G-CONF (not axiomatized),
**I** identical concrete op.

## Patch (post-patch `query` setter)
```python
@query.setter
def query(self, value):
    if value.values_select:
        self._iterable_class = ValuesIterable
    self._query = value
```

The single added behavior is the conditional `self._iterable_class =
ValuesIterable` guarded by the truthiness of `value.values_select` (a tuple of the
field names the query projects). The unconditional `self._query = value` is
unchanged.

## Modeling decision
The observable state of a result set that the setter touches is the pair
`(_iterable_class, _query)`. Modeled as a `ResultSet` structure with fields
`rowMode : RowMode` (the row-building strategy ↔ `_iterable_class`) and
`storedQuery : StoredQuery` (the installed query ↔ `_query`). A `StoredQuery` is
observed only by `selectedFields : List String` ↔ `Query.values_select` (the
projected field names). The five concrete iterable classes are modeled as the five
`RowMode` constructors (sentinel choices assigned, never invoked — so they need no
axiom). `value.values_select` truthiness ↔ `selectedFields ≠ []`.

## Operation correspondence
| # | Lean op (`implementation_installQuery`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut rs := rs` | the bound `self` whose attributes are mutated | I | local mutable handle on the result-set state. |
| 2 | `if value.selectedFields ≠ [] then rs := { rs with rowMode := RowMode.fieldValuesDict }` | `if value.values_select: self._iterable_class = ValuesIterable` | R | `value.values_select` (tuple) truthiness ↔ `selectedFields ≠ []`; `ValuesIterable` ↔ `RowMode.fieldValuesDict`. This is the fixed behavior. |
| 3 | `rs := { rs with storedQuery := value }` | `self._query = value` | R/I | store the installed query verbatim; `Query` object identity ↔ `StoredQuery` value equality. Unchanged by the fix. |
| 4 | `return rs` | (implicit — setter mutates `self` in place) | I | the mutated result-set state IS the observable result. |

## R/I legs ⇒ G-CONF
Op 2 (the conditional row-mode switch, R) and ops 1/3/4 (handle / store / return,
I) are the entire impl — all R/I. There is no abstract callee. `conf_skip =
false`: `conformance_check.py` differential-tests the Python shadow of this impl
(transliterated op-for-op) against the REAL patched `query` setter on a live
`QuerySet`, observing `(_iterable_class.__name__, _query is value)` over ≥10^5
fuzzed `(initial_row_mode, selected_fields)` inputs.

## No A rows
The setter calls nothing and consumes no callee property, so `meta.json axioms =
[]` and `deep_model_references = []`. `ValuesIterable`/`ModelIterable`/… are
sentinel class objects (assigned, never called), modeled directly as `RowMode`
constructors — not axiomatized callees. `axiom_check.py` is a skip stub.

## F2P alignment
The discriminating clause `problem_spec_installQuery` pins is: `value.selectedFields
≠ [] → result.rowMode = RowMode.fieldValuesDict` (a field-projecting query forces
the field-value-mapping row builder). The prepatch impl (op 2 deleted: it only
stores the query, never touches `rowMode`) cannot satisfy this clause — exactly
the bug.

- `test_annotation_values`: a `values(...).annotate(...)` query (non-empty
  `values_select`) is pickled, then installed into a fresh result set (whose
  default row builder is `ModelInstances`); after the fix the result set yields a
  value-dict, so `reloaded.get()` returns `{'name': ..., 'latest_time': ...}`
  instead of a broken model instance.
- `test_annotation_values_list`: all three `values_list(...)` variants (tuple /
  flat / named — i.e. initial `rowMode ∈ {fieldValuesTuple, fieldValuesFlat,
  fieldValuesNamed}`) have non-empty `values_select`, so each is collapsed to the
  field-value-mapping builder ("values_list() is reloaded to values()"); the spec
  clause pins this for EVERY initial `rowMode`.
- `test_annotation_with_callable_default`: a `values(...).annotate(...)` query is
  pickled/unpickled and the result set must round-trip as value-dicts.

`patch.diff` (gold verbatim) makes the harness resolve.
