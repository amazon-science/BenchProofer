# mapping.md — django__django-16032

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0c3981eb5094419fe200eb46c71b5376a2266166`, states the type
abstraction, and gives the provenance of the A-reference observations checked
by `axiom_check.py` / G-AX. This bundle consumes **no axioms** (the behaviour is
pure object/state logic, modelled deeply).

Repo files under change:
- `django/db/models/sql/query.py`
- `django/db/models/fields/related_lookups.py`

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `Query` (class) | `django.db.models.sql.query.Query` — `query.py:148` (`class Query(BaseExpression)`) | minimal twin carrying only the touched state |
| `Query.restricted_to_explicit_columns` | `Query.has_select_fields` — `query.py:266-270` (the `@property`, pre-patch) / `query.py:200` (the class attribute `has_select_fields = False`, post-patch) | the boolean property recording whether the SELECT list was explicitly restricted |
| `Query.selected_columns` | `Query.select` / `Query.values_select` — `query.py:182,205` | the explicitly-selected output columns |
| `Query.aux_expr_materialized` | `Query.annotation_select_mask` (and the `extra_select_mask`) — `query.py:208,218` | the internal expression-tracking structure whose mere presence the old property mistook for an explicit projection |
| `project_columns(q, column)` | `Query.set_values(fields)` — `query.py:2383` | restrict the query to a chosen column set, mark it explicitly projected, and re-derive the annotation mask for the chosen columns (empty for ordinary columns) |
| `attach_auxiliary_expressions(q)` | `Query.add_annotation(..., select=True)` then `add_annotation(..., select=False)` — `query.py:1109`, reached via `QuerySet.annotate` / `QuerySet.alias` | attach a returned + a non-returned auxiliary expression |
| `prepare_in_rhs(q, target_column, target_is_unique_key)` | `RelatedIn.get_prep_lookup` rhs-narrowing branch — `related_lookups.py:93-108` | prepare a query rhs for a related membership filter |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `Query` object (rich) | minimal class with three touched fields | only the touched state is modelled (mapping.md §1); all untouched query state is omitted |
| `Query.has_select_fields` — a `bool` (post-patch: class attribute default `False`, set `True` by `set_values`; pre-patch: a `@property` `bool(self.select or self.annotation_select_mask or self.extra_select_mask)`) | `restricted_to_explicit_columns: bool` | identical boolean |
| `Query.select` / `Query.values_select` (a tuple of column references / names) | `selected_columns: List[int]` of column ids | a column reference ↔ its int id; tuple ↔ `List[int]`; "no explicit selection" ↔ empty list; "narrowed to one column" ↔ a single-element list |
| `Query.annotation_select_mask` (`None` or a `set` of names) | `aux_expr_materialized: bool` — whether the tracking structure holds materialized entries | "mask is `None` or an EMPTY set" ↔ `False`; "mask materialized to a non-empty set" ↔ `True`. The model needs only the boolean *non-emptiness* of the mask, which is what the old property tested via `bool(...)`. NOTE: `set_values` re-derives the mask via `set_annotation_mask(annotation_names)`; when projecting onto ordinary (non-annotation) columns `annotation_names` is empty, so the mask becomes `set()` — i.e. projection CLEARS `aux_expr_materialized` to `False`. The model's `project_columns` encodes exactly that. |
| target column "is a unique key" (`getattr(self.lhs.field.target_field, "primary_key", False)`) | `target_is_unique_key: bool` | identical boolean |

The rich `Query`/`RelatedIn` objects are reduced to the minimal twin exposing
only the three fields the change observes; everything else is untouched and
omitted.

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The three operations are
modelled deeply (spelled-out state updates). Their fidelity to the real Django
machinery — with the gold patch applied — is validated out-of-band by
`axiom_check.py` as A-reference observations:

### 3.1 `project_columns` == real `Query.set_values` (post-patch)
**Source:** `django/db/models/sql/query.py:2383` (post-patch):
```python
def set_values(self, fields):
    self.select_related = False
    self.clear_deferred_loading()
    self.clear_select_fields()
    self.has_select_fields = True          # <-- the gold-patch line
    if fields:
        ...
```
`clear_select_fields` (`query.py:2100`) resets `self.select` / `self.values_select`,
then the field machinery sets them to exactly the supplied `fields`; the new
line sets `has_select_fields = True`. The same field machinery re-derives the
annotation mask for the supplied fields: `set_values` partitions `fields` into
field/extra/annotation names and calls `set_annotation_mask(annotation_names)`
— for ordinary column names `annotation_names == []`, so
`annotation_select_mask` becomes the EMPTY set (cleared; observed on the real
gold-patched tree: `{'ann'} -> set()` after `set_values(['code'])`). Hence
`set_values([col])` restricts the selected output to that one column AND
establishes the property AND clears the materialized mask — exactly
`project_columns` (whose postcondition sets `aux_expr_materialized` to
`False`). G-AX asserts `list(q.values_select) == [col]`,
`q.has_select_fields is True`, and `not q.annotation_select_mask` on real
`Query` objects.

### 3.2 `attach_auxiliary_expressions` == real `annotate()` + `alias()` (post-patch)
**Source:** `QuerySet.annotate` / `QuerySet.alias` both funnel into
`Query.add_annotation` (`query.py:1109`), which for the returned-column kind
(`select=True`) calls `append_annotation_mask([alias])` and for the
non-returned helper kind (`select=False`) calls
`set_annotation_mask(set(self.annotation_select).difference({alias}))`
(`query.py:1115-1118`). Either way `annotation_select_mask` becomes a
materialized (non-`None`) set; combining the two kinds leaves it non-empty.
Crucially, post-patch `has_select_fields` is a class attribute (`query.py:200`)
that **neither** path touches, so it stays at its prior value. On a query that
was never projected it stays `False`. G-AX asserts `q.annotation_select_mask`
is non-empty yet `q.has_select_fields is False` after `.annotate().alias()` on
an unprojected query (the exact reported-bug witness), and `True` once
`.values(...)` is additionally applied.

### 3.3 `prepare_in_rhs` == real `RelatedIn.get_prep_lookup` rhs-narrowing (post-patch)
**Source:** `django/db/models/fields/related_lookups.py:93-109` (post-patch):
```python
elif not getattr(self.rhs, "has_select_fields", True) and not getattr(
    self.lhs.field.target_field, "primary_key", False
):
    if (... primary_key ... and ... model ...):
        target_field = self.lhs.field.name
    else:
        target_field = self.lhs.field.target_field.name
    self.rhs.set_values([target_field])       # <-- gold patch: was clear_select_clause()+add_fields([...],True)
return super().get_prep_lookup()
```
The narrowing branch is entered exactly when the rhs query has
`has_select_fields` False and the target field is not a primary key; it narrows
the rhs by calling `set_values([target_field])` (operation §3.1), which
restricts the rhs to one column, sets `has_select_fields` True, and clears the
rhs's `annotation_select_mask` (re-derived empty for the ordinary target
column). When the guard is False (rhs already projected, or target is a
primary key) the modeled branch touches nothing — the model's no-narrow frame
clause (`aux_expr_materialized == Old(...)` included) describes THIS branch.
Modeling-boundary note: after the skipped branch, control continues into the
generic `In.get_prep_lookup` (`lookups.py:418-426` — UNCHANGED by the gold
patch, outside the modeled edit), which for a `Query` rhs with
`has_select_fields` False performs its own pk-narrowing
(`clear_select_clause()` + `add_fields(["pk"])`), emptying the annotation mask
WITHOUT setting `has_select_fields`. That downstream effect is not part of the
modeled operation; the attributable observable for "the RelatedIn branch was
skipped" is `has_select_fields` staying False. G-AX builds a
`Child.objects.filter(parent__in=<annotate+alias parent qs>)`, forces the
lookup, and asserts the narrowed rhs ends up with `has_select_fields is True`,
exactly one selected column, and an empty `annotation_select_mask`; for the
pk-target (skipped-branch) rhs it asserts `has_select_fields is False`.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions (the shadow) in
lock-step with the real patched operations bound in §1 (the oracle), from a
fresh query through boundary + fuzz operation sequences, comparing the §2
abstraction (`has_select_fields` / `values_select` column-ids /
`bool(annotation_select_mask)`) after every operation. The `prepare_in_rhs`
oracle drives a real `build_filter(("<fk>__in", qs))` and snapshots the rhs at
the modeled-operation boundary (entry to the unchanged generic `In`
preparation, §3.3) via a wrapper that then calls the original. **Pinned fuzz
seed: 16032** (the instance number).

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
Django, builds real `Query` objects via `set_values`, `annotate`/`alias`, and a
related `__in` filter, and asserts every observation above. It imports only
Django (the code under test). Exit 0 iff sound. The flag dependency is the gold
patch itself (the class attribute + the `set_values` line + the
`related_lookups` swap); G-AX runs with the gold patch applied.
