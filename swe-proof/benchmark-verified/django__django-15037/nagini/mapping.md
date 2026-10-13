# mapping.md — django__django-15037

Binds every `model.py` symbol to its repository counterpart at
`base_commit = dab48b7482295956973879d15bfd4d3bb0718772`, states the type
abstraction, and gives the provenance of the one referenced callee.

Repo file under change: `django/core/management/commands/inspectdb.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relation_field(...)` | the relation-handling block inside `handle_inspection.<locals>.table2model`'s per-column loop — `django/core/management/commands/inspectdb.py:118-130` (`if is_relation:` … `rel_to = …`) | the modeled changed code: decides relation kind, the `rel_to` target, and whether a `to_field` keyword is emitted |
| `RelationField` (result object: `is_one_to_one`, `rel_to_self`, `has_to_field`, `to_field_col`) | the local effects of the block: `rel_type` (`'OneToOneField'`/`'ForeignKey'`), the `rel_to` value (`'self'` vs `table2model(ref_db_table)`), and the `extra_params['to_field']` key | structured carrier of the block's decision |
| param `unique_or_pk: bool` | `extra_params.pop('unique', False) or extra_params.get('primary_key')` — `inspectdb.py:119` | whether the relation is rendered as `OneToOneField` (True) or `ForeignKey` (False) |
| param `ref_db_column: List[int]` | `ref_db_column` = `relations[column_name][0]` — `inspectdb.py:119` (post-patch) / `relations[column_name]` element 0 | the referenced column name in the other table (code points) |
| param `ref_db_table: List[int]` | `ref_db_table` = `relations[column_name][1]` — `inspectdb.py:119` (post-patch) / `relations[column_name]` element 1 | the referenced table name (code points) |
| param `table_name: List[int]` | `table_name` — the table being introspected (`inspectdb.py:43,68,124`) | current table name (code points) |
| param `ref_pk_column: Optional[List[int]]` *(A-reference)* | `ref_pk_column` = `connection.introspection.get_primary_key_column(cursor, ref_db_table)` — `inspectdb.py:124` (post-patch) | the referenced table's primary-key column name, or `None`; the return value of the unchanged callee `get_primary_key_column`, taken as introspected input |

`relations` is documented as a dict `{field_name: (field_name_other_table,
other_table)}` (`django/db/backends/base/introspection.py:147-152`; concrete
producer `django/db/backends/sqlite3/introspection.py:168`
`relations[field_name] = (other_name, table)`). Hence element 0 is the
referenced **column** and element 1 the referenced **table** — exactly the
`ref_db_column, ref_db_table = relations[column_name]` unpacking the patch adds.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| column / table name `str` | `List[int]` of Unicode code points | `s[k]` ↔ `name[k] == ord(s[k])`; `len(s)` ↔ `len(name)`; string `==`/`!=` ↔ `ToSeq` equality / its negation. `str` indexing is banned in Nagini, so names are code-point lists; equality is carried by `PSeq[int]` via `ToSeq`. |
| `extra_params['to_field'] = ref_db_column` (a key set into a dict that is later rendered into the field source) | `has_to_field: bool` + `to_field_col: List[int]` | the patch's *only* state effect of the change is whether the `to_field` key is present and, if so, that it equals `ref_db_column`. The rendering step (`', '.join('%s=%r' …)` at `inspectdb.py:166`) is a downstream identity over `extra_params` and is not part of the changed decision. |
| `rel_type` string `'OneToOneField'`/`'ForeignKey'` | `is_one_to_one: bool` | `True` ↔ `'OneToOneField'`, `False` ↔ `'ForeignKey'` (the only two values the branch produces). |
| `rel_to == 'self' if ref_db_table == table_name else table2model(ref_db_table)` | `rel_to_self: bool` | the self-vs-other choice is a pure equality `ref_db_table == table_name`; `table2model` is a downstream identity-preserving name transform of the non-self branch, unchanged by the patch. |
| `Optional` PK column (the callee may return `None`) | `Optional[List[int]]` | `None` ↔ Python `None` (no primary key found); a present value ↔ the PK column name as code points. |

## 3. Callee provenance

### 3.1 `get_primary_key_column` ↔ `ref_pk_column` input (A-reference)
**Callee:** `connection.introspection.get_primary_key_column(cursor, table_name)`
— `django/db/backends/base/introspection.py:166-173`:

```python
def get_primary_key_column(self, cursor, table_name):
    """Return the name of the primary key column for the given table."""
    for constraint in self.get_constraints(cursor, table_name).values():
        if constraint['primary_key']:
            return constraint['columns'][0]
    return None
```

It returns the primary-key column **name** of `table_name`, or `None` when the
table has no introspected primary key. This callee is **unchanged** by the
patch — the patch merely adds a *call* to it for the FK branch. The model takes
its result as the `ref_pk_column: Optional[List[int]]` parameter (introspected
data, like `relations`/`table_description`, which are loop inputs). It is an
**A-reference**, NOT a consumed axiom: the proof never relies on a contract
about its internals; G-AX (`axiom_check.py`) validates that the real callee
returns the referenced table's PK column name (or `None`) on representative
schemas, so the modeled comparison `ref_pk_column != ref_db_column` matches
reality.

The decision the patch adds, in repo terms (`inspectdb.py:118-130`, post-patch):
a `to_field` keyword is emitted iff the relation is a **ForeignKey** (not a
OneToOneField), the referenced table HAS a primary key, and that primary-key
column differs from the referenced column — and then `to_field` equals the
referenced column (`ref_db_column`). The F2P witness (`to_field='people_unique_id'`)
is exactly the case where the FK references a unique non-PK column.
