# mapping.md — symbol binding & type bijection (django__django-13417)

## Modeled function
- **Lean** `implementation_querysetOrdered : Bool → List String → List String → Bool → List String → List String → Bool`
- **Python** `QuerySet.ordered` (property getter) —
  `django/db/models/query.py:1216-1229 @ base_commit`.

The property returns whether the result set will carry a meaningful row ordering:

```python
@property
def ordered(self):
    if isinstance(self, EmptyQuerySet):
        return True
    if self.query.extra_order_by or self.query.order_by:
        return True
    elif self.query.default_ordering and self.query.get_meta().ordering:   # base (buggy)
        return True
    elif (self.query.default_ordering and self.query.get_meta().ordering   # patched
          and not self.query.group_by):
        return True
    else:
        return False
```

The observable behavior demanded by the F2P tests: an annotated (GROUP BY)
queryset over a model with `Meta.ordering` reports `ordered == False` (because the
default ordering does not survive the GROUP BY), while the same queryset with an
explicit `.order_by(...)` reports `ordered == True`.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `isinstance(self, EmptyQuerySet)` (bool) | `isEmpty : Bool` | the trivially-ordered empty set flag |
| `self.query.extra_order_by` (tuple/list of order specs; truthy iff non-empty) | `extraOrderBy : List String` | observed only by emptiness; non-empty ⇔ Python truthy |
| `self.query.order_by` (tuple/list of order specs; truthy iff non-empty) | `orderBy : List String` | observed only by emptiness; non-empty ⇔ Python truthy |
| `self.query.default_ordering` (bool) | `defaultOrdering : Bool` | whether the model default ordering is applied |
| `self.query.get_meta().ordering` (list of field names; truthy iff non-empty) | `metaOrdering : List String` | model `Meta.ordering`; observed only by emptiness |
| `self.query.group_by` (None / True / tuple of expressions; truthy iff not None and non-empty) | `groupBy : List String` | the GROUP BY columns; observed only by emptiness |
| return value (bool) | `result : Bool` | per the property's truthiness |

Python truthiness of a sequence/`None` carrier is modeled by `List.isEmpty`:
a non-empty `List String` ⇔ the Python attribute is truthy; the empty list ⇔
Python falsy (`()`, `[]`, `None`, or `False` for `group_by`). The two booleans
(`isEmpty`, `defaultOrdering`) map directly.

## Callee provenance
- `isinstance(self, EmptyQuerySet)`, attribute reads of `extra_order_by`,
  `order_by`, `default_ordering`, `group_by`, and `get_meta().ordering` are all
  pure attribute/predicate observations UNCHANGED by the patch. Each is reproduced
  concretely by inspecting the corresponding Lean carrier's flag/emptiness (I/R
  tagged), so no `opaque`/axiom is needed. The axioms region is empty; G-AX is a
  skip stub.
- The **changed op** is the third branch's guard: the patch conjoins
  `not self.query.group_by` to the existing `default_ordering and
  get_meta().ordering` condition. It is modeled deeply as the boolean conjunct
  `groupBy.isEmpty`, NOT axiomatized.

## Flag dependency
The default-ordering branch fires only when `default_ordering` is true AND
`get_meta().ordering` is non-empty. The fix additionally requires `group_by` to be
empty/None. G-CONF fuzzes all combinations of the two booleans and the emptiness of
the four sequence carriers.

## Scope note
`extra_order_by` and `order_by` short-circuit to `True` before the default-ordering
branch (Python `if … return True`); the model preserves this precedence by the
`||` ordering in the spec and the early `return true` in the impl. The exact
contents of any sequence are irrelevant to the property (only truthiness matters),
matching the Python.

## G-CONF fuzz seed
Pinned seed: **13417**. ≥10^5 fuzzed inputs over all six carriers (two booleans +
four sequences with varied emptiness).
