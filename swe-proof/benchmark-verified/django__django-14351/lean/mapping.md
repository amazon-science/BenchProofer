# mapping.md — django__django-14351

## Symbol binding (@ base_commit 06fd4df41a)

| Lean symbol | Python symbol | file:line @ base_commit |
|---|---|---|
| `implementation_membershipGroupColumns` / `problem_spec_membershipGroupColumns` / `correct_membershipGroupColumns` | `django.db.models.lookups.In.get_group_by_cols` (the method ADDED by the gold patch as an override on the `In` lookup) | `django/db/models/lookups.py` +406..415 (gold hunk) |
| prepatch impl | inherited `django.db.models.lookups.Lookup.get_group_by_cols` (the base method `In` used BEFORE the patch — no override) | `django/db/models/lookups.py:117-121` |

## The change

Pre-patch, the membership ("IN") lookup uses the base `Lookup.get_group_by_cols`:

```python
def get_group_by_cols(self, alias=None):           # lookups.py:117
    cols = self.lhs.get_group_by_cols()
    if hasattr(self.rhs, 'get_group_by_cols'):
        cols.extend(self.rhs.get_group_by_cols())
    return cols
```

When the right-hand side is a subquery (a `Query`/queryset) that the user never
gave an explicit set of selected columns, that subquery still carries all of its
model's default columns, so when it is emitted as a GROUP BY key the generated
subquery `SELECT`s many columns → `subquery must return only one column`.

The gold patch adds an override on `In` that, before collecting the rhs's
group-by contribution, normalizes such a subquery to select only its single
identity (`pk`) column — mirroring what `In.process_rhs` (lookups.py:404-406)
already does at SQL-build time:

```python
def get_group_by_cols(self, alias=None):           # gold hunk
    cols = self.lhs.get_group_by_cols()
    if hasattr(self.rhs, 'get_group_by_cols'):
        if not getattr(self.rhs, 'has_select_fields', True):
            self.rhs.clear_select_clause()
            self.rhs.add_fields(['pk'])
        cols.extend(self.rhs.get_group_by_cols())
    return cols
```

### Crux (why the result is modeled as a PAIR)

The returned `cols` list is **byte-for-byte identical** pre- and post-patch: a
non-aggregate `Query.get_group_by_cols()` returns `[self]` (one subquery
expression) regardless of how many columns that subquery internally selects, and
`self.rhs.get_group_by_cols()` is called unchanged in both versions. The ONLY
observable difference is the *mutation of the rhs subquery's select clause* — the
list `cols` literally embeds the (now-mutated) rhs. So the spec/impl return
`(cols, rhs')`: the second component carries the normalized subquery state, which
is where the fix is observable and where the prepatch differs.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean | Python | notes |
|---|---|---|
| `Col := Nat` | a column expression (`Col(alias, field)`) | modeled as an opaque integer identity; only equality/identity matters |
| `RhsSubquery` | the rhs `Query` object | only the touched state is modeled (below) |
| `RhsSubquery.explicitlySelected : Bool` | `Query.has_select_fields` property = `bool(select or annotation_select_mask or extra_select_mask)` (query.py:243-245); `getattr(rhs,'has_select_fields',True)` defaults `True` for non-Query rhs | |
| `RhsSubquery.selected : List Col` | `Query.select` tuple (the explicitly-selected columns; emitted when `has_select_fields`) | |
| `RhsSubquery.defaultColumns : List Col` | the model's default columns emitted when `not has_select_fields` (`default_cols=True`) | |
| `RhsSubquery.groupKeys : List Col` | result of `rhs.get_group_by_cols()` — patch-INVARIANT (returns `[self]` for a non-aggregate query); modeled as a fixed field | |
| `RhsSubquery.identityColumn : Col` | the `pk` column added by `add_fields(['pk'])` | |
| `rhs : Option RhsSubquery` | `some` ⟺ `hasattr(self.rhs,'get_group_by_cols')` (rhs is a subquery); `none` ⟺ a plain value rhs | |
| `lhsCols : List Col` | `self.lhs.get_group_by_cols()` | A-reference/I: collected verbatim, not changed by the patch |
| result `.1 : List Col` | the returned `cols` list | |
| result `.2 : Option RhsSubquery` | the rhs subquery's state AFTER the call (`[self]` embeds it) | discriminating component |

### Modeled callee operations (mirroring the two patch lines)

| Python op | Lean model |
|---|---|
| `self.rhs.clear_select_clause()` (query.py:1861: `select=()`, masks cleared ⇒ `has_select_fields` becomes `False`) | `{ q with selected := [], explicitlySelected := false }` |
| `self.rhs.add_fields(['pk'])` (query.py:1893: `set_select([pk])` ⇒ `select=[pk]`, `has_select_fields` becomes `True`) | `{ q with selected := [q.identityColumn], explicitlySelected := true }` |

## Flag dependency

The normalization fires only when `not getattr(self.rhs,'has_select_fields',True)`
— i.e. the rhs is a subquery (`some`) AND `explicitlySelected = false`. G-CONF
fuzzes both polarities of `explicitlySelected` and the `none` rhs.

## G-CONF fuzz seed

`conf_seed = 20240630` (pinned).
