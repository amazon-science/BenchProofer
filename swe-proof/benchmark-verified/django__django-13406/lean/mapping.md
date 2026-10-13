# mapping.md — django__django-13406

## Instance
- repo: django/django
- base_commit: 84609b3205905097d7d3038d32e6101f012c0619
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
A result set (`QuerySet`) carries two pieces of state that the `query` *setter*
(`QuerySet.query.setter`, django/db/models/query.py:211-213) touches: the stored
query object (`self._query`) and the row-building strategy (`self._iterable_class`)
used to turn raw DB rows into Python results. When a query that *projects specific
field values* (one produced by `values(...)` / `values_list(...)`) is installed
into a result set, the rows must be built as value-dicts; a query that projects no
specific fields leaves the existing row-builder in place.

At `base_commit` the setter only stored the query:

```python
@query.setter
def query(self, value):
    self._query = value
```

The row-builder (`_iterable_class`) is NOT part of the query object, so installing
a query that projects fields into a fresh result set (whose default row-builder
emits full model instances) left the wrong row-builder in place — the result set
yielded model instances instead of value-dicts. The gold patch sets the
value-dict row-builder whenever the installed query projects fields:

```python
@query.setter
def query(self, value):
    if value.values_select:
        self._iterable_class = ValuesIterable
    self._query = value
```

`value.values_select` is a tuple of the projected field names; truthiness ==
non-empty. The fix collapses *every* field-projecting query (including the
`values_list()` variants, whose source result sets use tuple / flat / named
row-builders) to the value-dict row-builder — this is exactly what the
FAIL_TO_PASS test `test_annotation_values_list` asserts ("values_list() is
reloaded to values() when using a pickled query"): all three variants come back
as value-dicts.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_installQuery` | `QuerySet.query` setter (django/db/models/query.py:211-213) |
| `problem_spec_installQuery` | the post-condition that setter must satisfy |
| `ResultSet.rowMode` | `QuerySet._iterable_class` (the BaseIterable subclass; django/db/models/query.py:198 default `ModelIterable`) |
| `ResultSet.storedQuery` | `QuerySet._query` |
| `StoredQuery.selectedFields` | `Query.values_select` (django/db/models/sql/query.py:200), the tuple of projected field names |
| `RowMode.fieldValuesDict` | `ValuesIterable` (django/db/models/query.py:94) |
| `RowMode.modelInstances` | `ModelIterable` (django/db/models/query.py:44) |
| `RowMode.fieldValuesTuple` | `ValuesListIterable` (django/db/models/query.py:115) |
| `RowMode.fieldValuesFlat` | `FlatValuesListIterable` (django/db/models/query.py:171) |
| `RowMode.fieldValuesNamed` | `NamedValuesListIterable` (django/db/models/query.py:145) |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `rs.rowMode : RowMode` | `qs._iterable_class` (a `BaseIterable` subclass object) | 5-way enumeration ↔ the 5 concrete iterable classes (table above); compared by class `__name__` |
| `rs.storedQuery : StoredQuery` | `qs._query` (a `Query`) | compared by object identity (`is`) — the setter stores the value verbatim |
| `q.selectedFields : List String` | `value.values_select` (tuple of `str`) | element-wise `str` ↔ `String`; `≠ []` ↔ truthiness (non-empty tuple) |
| result `: ResultSet` | the mutated `qs` (its `_iterable_class` + `_query`) | observed as `(_iterable_class.__name__, _query is value)` |

`List String` ↔ Python field-name tuple is element-wise identity. The setter never
reads element VALUES — only the tuple's emptiness — so the bijection only needs to
preserve emptiness, which it does.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom and none is deep-modeled as an
  A-reference. The setter calls NOTHING: it reads one attribute (`value.values_select`,
  modeled as the struct field `StoredQuery.selectedFields`) and performs two
  assignments. `ValuesIterable` etc. are sentinel class objects (assigned, never
  called), modeled directly as `RowMode` enum constructors. Hence `axioms = []`,
  `deep_model_references = []`, and `axiom_check.py` is a skip stub.
- Flag dependency: the row-builder choice depends solely on whether
  `value.values_select` is non-empty. G-CONF fuzzes empty vs non-empty field lists
  AND all five initial row-builders (to exercise the frame branch).

## G-CONF fuzz seed
- pinned seed: `13406`
- ≥10^5 fuzzed `(initial_row_mode, selected_fields)` tuples; `initial_row_mode`
  drawn uniformly over the 5 iterable classes, `selected_fields` empty ~40% of the
  time else a random list of field names. Oracle = the REAL patched `query` setter
  on a `QuerySet(model=ContentType)`; observation = `(_iterable_class.__name__,
  _query is value)`.
