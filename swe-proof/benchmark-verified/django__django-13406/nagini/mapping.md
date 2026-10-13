# mapping.md — django__django-13406

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 84609b3205905097d7d3038d32e6101f012c0619`, states the type
abstraction, and gives the provenance of the deep-model A-reference (the real
callee the deep model is validated against; this bundle consumes NO axioms).

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `attach_description(rs, value)` | `QuerySet.query` setter — `django/db/models/query.py:211-213` (`@query.setter def query(self, value)`) | the modeled changed function (attach a query to a result set, configuring its row producer); single contracted+implemented function (markers are module-level singletons) |
| `ResultSet` | `QuerySet` — `django/db/models/query.py:184` | the result set being mutated; minimal class with only the two touched fields |
| `ResultSet.producer_tag` | `QuerySet._iterable_class` — set in `__init__` at `query.py:198`, read in `__iter__` at `query.py:360` | the row producer; integer tag (0 = model-instance producer, 1 = value-mapping producer) |
| `ResultSet.description` | `QuerySet._query` — assigned by the setter at `query.py:213` | the attached active query (`_query` reference) |
| `LookupDescription` | `sql.Query` — the object passed to the setter (`django/db/models/sql/query.py:154`) | the attached query description; minimal class with only the one touched, read-only field |
| `LookupDescription.value_field_count` | `Query.values_select` — `django/db/models/sql/query.py:200` (init `()`), set at `:2224` (`self.values_select = tuple(field_names)`) | the selected value-field set; modeled by its count (>= 0); non-empty (truthy) ⟺ count > 0 |
| `PRODUCES_MODEL_INSTANCES` (0) | `ModelIterable` — `django/db/models/query.py:44` (default `_iterable_class`, `query.py:198`) | the producer that yields full model instances |
| `PRODUCES_VALUE_MAPPINGS` (1) | `ValuesIterable` — `django/db/models/query.py:94` (the producer `values()` installs, `query.py:831`; the one the patch installs) | the producer that yields one value mapping (dict) per row |

The pre-patch behaviour the change fixes: the setter (`query.py:211-213`) stored
`self._query = value` only, leaving `self._iterable_class` at its `__init__`
default `ModelIterable` (`query.py:198`) — so a freshly-created result set given
a value-bearing pickled query produced model instances instead of value
mappings (the crash in the issue).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `QuerySet._iterable_class` (a class object: `ModelIterable` / `ValuesIterable` / `ValuesListIterable` / `FlatValuesListIterable` / `NamedValuesListIterable`) | `int` producer tag (0 / 1) | `ModelIterable` ↔ 0 (`PRODUCES_MODEL_INSTANCES`); `ValuesIterable` ↔ 1 (`PRODUCES_VALUE_MAPPINGS`). The patch installs `ValuesIterable` for every value-bearing query (incl. those built by `values_list()`), so all five value-list flavours collapse to the single value-mapping tag 1 — see §3 and refinement.md row R3. The observable the F2P tests check is "produces value mappings (dicts), not model instances", i.e. tag ≠ 0. |
| `Query.values_select` (a `tuple` of field-name strings) | `int` count >= 0 of selected value-fields | `bool(values_select)` (the setter's `if value.values_select:`) ↔ `value_field_count > 0`; empty tuple `()` ↔ count 0; the field-name characters are never inspected (only the tuple's truthiness), so only the count is modeled. |
| `QuerySet._query` (holds the `sql.Query` reference) | `Optional[LookupDescription]` reference | `self._query = value` ↔ `rs.description = value`; identity preserved (`rs.description is value`). |
| `QuerySet` / `sql.Query` rich objects | minimal classes with only the touched fields | the setter touches only `_iterable_class` and `_query` on `self`, and reads only `values_select` on `value`; all other fields are irrelevant to the pinned behaviour and omitted. |

`str` indexing is banned in Nagini and irrelevant here (the setter never inspects
the field-name characters, only `bool(values_select)`), so the value-field
selection is carried by its integer count.

## 3. Deep-model A-reference (checked by G-AX / axiom_check.py)

This bundle consumes **no `@ContractOnly` axiom**: the attachment is a
conditional attribute update over integer tags, modeled deeply and verified
directly. The one place the model meets opaque real behaviour is the
correspondence between the modeled tags and the real Django objects; that is an
**A-reference**, validated == the real callee out-of-band by `axiom_check.py`
(G-AX), not consumed as an axiom.

**Real callee:** `QuerySet.query` setter (post-patch), `django/db/models/query.py:211-215`:

```python
@query.setter
def query(self, value):
    if value.values_select:
        self._iterable_class = ValuesIterable
    self._query = value
```

The deep model encodes exactly this:

  * `value.values_select` truthy ⟺ `value.value_field_count > 0`
    (tuple non-emptiness, mapping.md §2);
  * the truthy branch sets the value-mapping producer
    (`ValuesIterable` ↔ tag 1);
  * the falsy branch leaves `_iterable_class` at its prior value (here the
    `__init__` default `ModelIterable` ↔ tag 0) — preserved;
  * `self._query = value` ↔ `rs.description = value`.

**The known scope of the fix (the F2P observable).** The patch installs
`ValuesIterable` for *every* value-bearing query, including queries originally
built by `values_list()` (whose own producer would be `ValuesListIterable` /
`FlatValuesListIterable` / `NamedValuesListIterable`). The F2P test
`test_annotation_values_list` documents and asserts this: a pickled
`values_list()` query, when reattached, "is reloaded to values()" — its
reattached result set yields value mappings (dicts), `reloaded.get() ==
{'name': 'test'}`. So under the type abstraction §2 all value-bearing producers
collapse to the single value-mapping tag 1; the model pins exactly the property
the tests observe (a value-bearing query ⇒ a value-mapping, non-model-instance
producer).

**Soundness check (G-AX):** `axiom_check.py` runs the real post-patch
`QuerySet.query` setter against an in-memory sqlite DB on a model
(`Toy(name, material, price)` from the issue's reproducer). For each
`values()` / `values_list()` flavour (incl. `flat=`, `named=`, and a
`.annotate()` GROUP-BY query) it asserts (a) the query's real `values_select`
is non-empty, and (b) attaching it to a freshly-created (model-instance-default)
result set switches `_iterable_class` to `ValuesIterable`. For plain queries
(`all()`, `filter()`, `order_by()`) it asserts `values_select` is empty and the
default `ModelIterable` producer is preserved. It also confirms the
tuple-truthiness ⟺ count-positive correspondence over 5000 fuzz tuples. It
imports nothing repo-specific beyond Django itself (the package the patch lives
in). Exit 0 iff sound; graceful `G-AX SKIP` when Django is absent (the
orchestrator runs it in-container).
