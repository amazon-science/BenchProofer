# mapping.md — django__django-11400

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1f8382d34d54061eddc41df6994e20ee38c60907`, states the type
abstraction, and gives the provenance of the axiomatized callee.

Repo files under change:
* `django/db/models/fields/__init__.py` (`Field.get_choices`)
* `django/db/models/fields/reverse_related.py` (`ForeignObjectRel.get_choices`)
* `django/contrib/admin/filters.py` (`RelatedFieldListFilter` /
  `RelatedOnlyFieldListFilter`) — pass-through call sites, see §4.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `related_choice_rows(base, ordering)` | `Field.get_choices(...)` data-row branch — `django/db/models/fields/__init__.py:809` (changed body lines 828-831) | the modeled changed function: the row sequence backing the choices of a related field |
| `reverse_choice_rows(base, ordering)` | `ForeignObjectRel.get_choices(...)` — `django/db/models/fields/reverse_related.py:117` (changed body lines 125-127) | the modeled changed function: the row sequence backing the choices of a reverse relation |
| `reordered(base, ordering)` *(axiom — A-consumed, @Pure)* | `django.db.models.query.QuerySet.order_by(*ordering)` applied to the related model's base manager queryset (`rel_model._default_manager.complex_filter(limit_choices_to)` / `self.related_model._default_manager.all()`) | unchanged queryset callee; pure value of the reordered rows |
| `apply_order_by(base, ordering)` *(axiom — A-consumed)* | the same `QuerySet.order_by(*ordering)` call, effecting form returning a materialized row sequence | unchanged queryset callee; used on the non-empty-ordering branch |
| `copy_rows(base)` | the result list comprehension that materializes the base queryset when no reorder is applied: `[(choice_func(x), str(x)) for x in qs]` over the un-reordered base `qs` | impl helper: a faithful row-order-preserving materialization (kind I/R) |

The pre-patch repo expression the change removes (for the refinement audit, not
referenced from the consumer spec view): the unconditional trailing
`.order_by(*ordering)` on the base queryset
(`...complex_filter(limit_choices_to).order_by(*ordering)` at
`fields/__init__.py:830`; `...._default_manager.order_by(*ordering)` at
`reverse_related.py:126`). When `ordering` is the empty tuple this call clears
the base manager's `Meta.ordering`, which is the bug.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the base queryset of related rows, in the order the base manager yields them (i.e. with the model's `Meta.ordering` applied) | `base: List[int]` of opaque row identities | `base[k]` ↔ the k-th row of the base queryset; `len(base)` ↔ the row count; order of `base` ↔ the base manager's emission order |
| the `ordering` argument (a tuple of field-name strings, possibly empty) | `ordering: List[int]` | only its EMPTINESS is observed: `len(ordering)==0` ↔ `ordering == ()`; `len(ordering)>0` ↔ a non-empty field-name tuple. The field-name contents are passed through to the `reordered` operation and not interpreted further; they are NOT taken to denote a permutation of `base` (a field-name path may traverse a relation, and the operation then repeats or drops base entries — see §3.1). |
| the choices row sequence (`[(choice_func(x), str(x)) for x in qs]`, the data rows after any optional blank prefix) | `Result(): List[int]` of row identities in their final order | the F2P tests compare `[(pk, str(obj)) for obj in <objs in order>]`; the discriminating observable is the ROW ORDER, which the model carries directly as the order of `Result()`. The `(pk, str)` projection is order-preserving and elided. |
| `QuerySet.order_by(*ordering)` (queryset value) | `reordered(ToSeq(base), ToSeq(ordering))` (PSeq) / `apply_order_by(base, ordering)` (List) | the reordered rows; see §3 |

Notes on omitted, behaviour-irrelevant detail:
* The optional blank-choice prefix `(blank_choice if include_blank else [])` is
  IDENTICAL pre- and post-patch (untouched) and orthogonal to the ordering bug;
  all six F2P tests use `include_blank=False`. It is not modeled — the
  discriminating behaviour is entirely the data-row order.
* `complex_filter(limit_choices_to)` / `.all()` and the `choice_func`/`pk`
  projection are unchanged and order-preserving; they are folded into `base`
  (the base row sequence) and the order-preserving result materialization.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `reordered` / `apply_order_by` ↔ `QuerySet.order_by(*ordering)`
**Callee:** `django.db.models.query.QuerySet.order_by(*field_names)`
(`django/db/models/query.py`). Returns a new queryset whose rows are the same
rows reordered by `field_names`. Documented semantics
(https://docs.djangoproject.com/en/stable/ref/models/querysets/#order-by):

> `order_by(*fields)` — Use this method to override the default ordering...
> If you don't want any ordering to be applied... call `order_by()` with no
> parameters.

The axiom is UNINTERPRETED: its contract is EMPTY, asserting nothing whatsoever
about the value of `reordered(base, ordering)`. Two facts make that the only
sound encoding, and both are true of the real callee:

1. **NOT a rearrangement — no length, set or multiset relation to `base`.** A
   member of `ordering` is a field-name *path*, not necessarily a local column,
   and `SQLCompiler.find_ordering_name` /
   `Query.setup_joins` emit a JOIN for every relation the path traverses
   (`django/db/models/sql/compiler.py:698` / `sql/query.py:1494`, whose join
   construction is `sql/query.py:1579-1588`, at base_commit). Consequences, both measured against the real callee:
   * a path crossing a **to-many** association (a reverse FK or an m2m, e.g.
     `('books__title',)`) makes the join multiply rows, so the result is
     **LONGER** than `base` — one entry per associated element;
   * a path crossing a **mandatory single-valued** association is an INNER join
     (`Query.join`, `sql/query.py:926`, promotes to LOUTER only when the
     relation is nullable), so an entry whose associate is absent **DROPS OUT**
     — the result is SHORTER than `base` and its row set differs.

   So `len(reordered(base, ordering)) == len(base)` is FALSE of the real callee,
   as is any set or multiset relation to `base`. The axiom asserts none of them.
   Being uninterpreted also GROUNDS the postcondition that consumes it: the only
   way to obtain a value equal to `reordered(base, ordering)` is to invoke the
   operation via `apply_order_by`, so the obligation cannot be discharged by
   rebuilding the value from the arguments.

2. **Silence on the empty case.** Calling `order_by()` with an EMPTY field list
   CLEARS any pre-existing ordering (including the base manager's
   `Meta.ordering`) — `Query.add_ordering` sets `default_ordering = False`
   (`sql/query.py:1858`). The resulting order is the database default, which is
   NOT the base order. The axiom therefore says NOTHING tying
   `reordered(base, [])` to `base`. This silence is the soundness crux: it
   forbids an implementation from routing the empty case through `order_by()`
   and is exactly why the patched code skips the reorder when `ordering` is
   empty.

`apply_order_by` is the effecting form (returns a materialized `List[int]`)
whose value is pinned to `reordered`; both read their inputs only (fractional
permission, directive 5).

**Soundness check (G-AX):** `axiom_check.py` executes the REAL callee
(`Model._default_manager.all().order_by(*ordering)`) over an in-memory SQLite
database. It asserts: that the operation is NOT a rearrangement, in BOTH
directions — a to-many ordering path makes the result LONGER than the base and a
mandatory single-valued one makes it SHORTER and changes its row set, so no
length/set/multiset clause would be sound and the axiom must stay uninterpreted;
that a plain local-field ordering is honoured (ascending/descending); and — the
crux — that `order_by()` (empty) does NOT reproduce a base manager whose default
order is set via `Meta.ordering` (it returns pk/rowid order instead), so the
axiom's silence on the empty case is sound and the patched skip is required.
Imports Django (whose ORM IS the callee) + stdlib only; no DB fixtures. Exit 0
iff sound.

## 4. The admin-filter pass-through sites (no separate model)
The gold patch also edits `django/contrib/admin/filters.py`: it factors out
`RelatedFieldListFilter.field_admin_ordering(...)` and makes
`RelatedOnlyFieldListFilter.field_choices(...)` forward the `ordering` kwarg
into `field.get_choices(...)`. These sites do not change the ordering SEMANTICS
— they only THREAD an `ordering` value into `get_choices`, whose behaviour is
the modeled `related_choice_rows`. The admin F2P tests
(`test_relatedfieldlistfilter_*_default_ordering`,
`test_relatedonlyfieldlistfilter_*ordering`) observe the very same row-order
fix through `get_choices`. They are therefore covered transitively by the two
modeled functions and the `reordered` axiom; no additional contracted function
is warranted (modeling the kwarg-threading would add no discriminating power).
See refinement.md §C.
