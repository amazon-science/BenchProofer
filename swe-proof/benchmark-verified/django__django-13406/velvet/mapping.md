# mapping.md — django__django-13406

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 84609b3205905097d7d3038d32e6101f012c0619`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee. `spec_provenance: cold`.

Repo file under change: `django/db/models/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `assignQuery (mut storedQuery) (mut shaper) (incoming)` | `QuerySet.query` setter — `django/db/models/query.py:210` (the `@query.setter def query(self, value)`) | the modeled changed function: re-seating a supplied query carrier into a container and reconciling the container's row shaper with it |
| `storedQuery` (mut field) | `self._query` — the container's installed query carrier (`django/db/models/query.py:190`, set in `__init__`) | the field unconditionally assigned the supplied carrier |
| `shaper` (mut field) | `self._iterable_class` — the container's row shaper (`django/db/models/query.py:201`, set in `__init__`) | the field reconciled with the incoming carrier |
| `incoming` (read-only) | `value` — the supplied query carrier (the setter argument) | read-only input; never altered (directive 5) |
| `Query` (structure) | a `django.db.models.sql.query.Query`, abstracted to the one observation that decides the reconciliation: `projection` ↔ `value.values_select` (the tuple of explicitly-selected value columns) | rich-object → structure with only the touched field (SPEC_GUIDE §2) |
| `projectsColumns (q)` | `bool(value.values_select)` — whether the carrier requests a non-empty explicit column projection | pure observation the decision consults |
| `Shaper` (inductive) | the row-shaper class held in `_iterable_class` (`ModelIterable`, `ValuesIterable`, `ValuesListIterable`, `FlatValuesListIterable`, `NamedValuesListIterable` — `django/db/models/query.py:44,94,115,171,145`) | rich-object → finite tag of the touched outcomes |
| `shaperAfter (incoming) (prior)` | the post-state of `_iterable_class` after the patched setter runs | pure spec: the reconciled shaper |

The pre-patch repo behaviour the change overrides (refinement audit only, NOT in
the consumer spec view): the setter was `def query(self, value): self._query = value`
— it installs the carrier but never touches `_iterable_class`. So a freshly
constructed container (`QuerySet.__init__` sets `_iterable_class = ModelIterable`,
line 201) whose `.query` is reassigned from a pickled `values()/values_list()`
query keeps `ModelIterable` and yields broken model instances instead of the row
dicts the projection demands — the observed defect (the `AttributeError:
'NoneType' object has no attribute 'attname'` crash in the issue).

## 2. Type abstraction (R-refinement) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `Query` carrier, observed only through its `values_select` tuple | `Query` with field `projection : List String` | `q.projection` ↔ `list(value.values_select)`; only emptiness is consulted, so `projectsColumns q = !q.projection.isEmpty` ↔ `bool(value.values_select)` |
| the row-shaper class in `_iterable_class` | `Shaper` (5-constructor inductive) | `entity` ↔ `ModelIterable`; `namedValues` ↔ `ValuesIterable`; `namedValuesTuple` ↔ `ValuesListIterable`; `namedValuesFlat` ↔ `FlatValuesListIterable`; `namedValuesRecord` ↔ `NamedValuesListIterable` |
| `self._query = value` (unconditional) | `storedQuery := incoming` ⇒ `ensures storedQuery = incoming` | identity install (I) |
| post-state of `self._iterable_class` | `shaper` ⇒ `ensures shaper = shaperAfter incoming shaperOld` | `namedValues` (`ValuesIterable`) when projecting columns, else the entry value `shaperOld` (the prior class, preserved) |

The patched code sets `_iterable_class = ValuesIterable` (the `namedValues`
shaper) for ANY non-empty `values_select`, regardless of whether the source was
`values()`, `values_list()`, `values_list(flat=True)`, or
`values_list(named=True)` — i.e. a `values_list()`-derived carrier is reloaded
as the `values()` shaper (this is exactly what `test_annotation_values_list`
asserts: `reloaded.get() == {'name': 'test'}`, a dict). The model captures this:
the only non-`entity` outcome the change produces is `namedValues`.

## 3. Callee provenance

The modeled function (the `query` setter) is the **changed** function itself.
Its post-patch body reads one attribute of the argument (`value.values_select`)
and writes two fields of `self` (`_iterable_class`, `_query`). It calls **no**
other function whose contract the proof would have to consume, and it
deep-models **no** foreign callee. There is therefore **no axiomatized callee**
in this bundle (no consumed axiom, no A-reference): `axiom_check.py` is omitted
and **G-AX is skipped** (cf. the no-axiom exemplars `django__django-13569` /
`django__django-13343`).

The grounding the spec relies on (validated by G-CONF / G-RESOLVE, not assumed):

- a `.values('name')` / `.values('name').annotate(...)` carrier has a non-empty
  `values_select`; assigning it makes the container's `_iterable_class` become
  `ValuesIterable`;
- a `.values_list('name'[, flat=True | named=True])` carrier likewise has a
  non-empty `values_select`; assigning it ALSO makes `_iterable_class`
  `ValuesIterable` (reloaded to `values()`);
- a plain `.all()` carrier has an empty `values_select`; assigning it leaves
  `_iterable_class` at whatever it was (preserved).

All four observations are executed directly against the real repo classes by
`conformance_check.py` (it builds real `QuerySet`s, pickle-round-trips their
`.query`, runs the **real patched setter** via `reloaded.query = value`, and
reads `reloaded._iterable_class`), so the R/I shadow is checked against the
genuine setter, not a hand-copied rule.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13406`** so the
consumer-side verdict (§11.3) is reproducible. The input space (the cross product
of {5 prior shaper classes} × {plain, values, values+annotate, values_list,
values_list-flat, values_list-named carriers}) is small and enumerated
exhaustively each round; the seed governs only the order in which combinations
are drawn during the ≥10⁵ fuzz loop.
