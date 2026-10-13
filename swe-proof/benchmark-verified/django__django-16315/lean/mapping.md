# mapping.md — symbol binding & type bijection (django__django-16315)

## Modeled function
- **Lean** `implementation_renderUpsertClause : List FieldRef → List FieldRef → List Char`
- **Python** the `OnConflict.UPDATE` branch of `on_conflict_suffix_sql`, fed by
  the resolved field lists that `QuerySet.bulk_create` / `SQLInsertCompiler.as_sql`
  hand it. Concretely the observable spans two changed sites:
  - `django/db/models/sql/compiler.py:1725-1730 @ base_commit`
    (`SQLInsertCompiler.as_sql` — the two arguments passed to
    `on_conflict_suffix_sql`).
  - `django/db/models/query.py:786-796 @ base_commit`
    (`QuerySet.bulk_create` — resolving the user-supplied field-name strings into
    field objects before they reach the query / compiler).
  The renderer itself (`on_conflict_suffix_sql`, e.g.
  `django/db/backends/sqlite3/operations.py:415-428`, identical UPDATE template in
  `postgresql/operations.py:352-364`) is UNCHANGED.

## The observable behavior
For `update_conflicts=True` with `unique_fields` + `update_fields`, the database
backend renders the suffix

```
ON CONFLICT(%s) DO UPDATE SET %s
```

where the first slot is `", ".join(map(quote_name, unique_fields))` and the
second is `", ".join(f"{q} = EXCLUDED.{q}" for q in map(quote_name, update_fields))`.

The user supplies field *names* (e.g. `"rank"`). A model field may declare a
distinct database column (`db_column="rAnK"`). The INSERT column list already uses
the database column; the suffix must reference each field by the **same database
column** so the generated SQL is valid. Post-fix the lists handed to
`on_conflict_suffix_sql` are the fields' `column` values; pre-fix they were the
raw field-name strings.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| a resolved model field (result of `self.model._meta.get_field(name)`) carrying `.name` and `.column` | `FieldRef` structure `{ name : List Char, column : List Char }` | only the two touched attributes are modeled; `.column` = `db_column` if set else the field's name |
| `unique_fields` after resolution (`self.query.unique_fields`) | `uniqueFields : List FieldRef` | the conflict-target fields, in caller order |
| `update_fields` after resolution (`self.query.update_fields`) | `updateFields : List FieldRef` | the fields assigned in the DO UPDATE SET clause, in caller order |
| `quote_name(s)` (sqlite/postgres identifier quoting) | `quoteName : List Char → List Char` | wraps in `"` unless already so wrapped (sqlite `operations.py:187-190`) |
| the rendered suffix `str` | `List Char` | per-character; the `params` side of the suffix is empty for UPDATE and unmodeled |

### `get_field` as the R-refinement bijection (not an axiom)
`self.model._meta.get_field(name)` is an UNCHANGED callee. The patch only moves
*where* it is called (into `bulk_create`, line 791-792 post-fix) so that the field
objects — not the bare name strings — flow into `self.query.{unique,update}_fields`
and thus into the compiler. We do not call `get_field` in the model; instead the
input carrier is the already-resolved `List FieldRef`. The string→FieldRef
correspondence (name ↦ the field whose `.name` is that string, carrying its
`.column`) is the **R** type refinement, recorded in refinement.md — no `opaque`
declaration or `_prop` axiom is consumed (axioms region empty; G-AX is a skip stub).

The pre-fix data flow passed the field-name *strings* straight through, so the
renderer effectively quoted each field's `.name`. The post-fix flow passes the
field objects and the compiler extracts `.column`. Modeling both legs as
`List FieldRef` and the changed op as `.name` (pre) vs `.column` (post) is exactly
faithful to the two-line `compiler.py` diff (`(f.column for f in …)` replacing the
bare iteration that yielded the name strings).

## Scope notes
- Only the `OnConflict.UPDATE` branch is modeled — the branch the issue and the
  F2P test exercise. `OnConflict.IGNORE` returns the fixed string
  `"ON CONFLICT DO NOTHING"` (no field rendering, unaffected by the fix); the
  `None` / `super()` branch raises / delegates and renders no fields. Both are
  orthogonal to the column-vs-name behavior and out of model scope.
- The `"pk"` → `opts.pk.name` remapping in `bulk_create` (line 788-790, present
  both pre and post fix) is name-resolution orthogonal to the column fix and not
  modeled; the F2P test uses ordinary field names.
- `quote_name`'s pre-quoted shortcut is modeled and fuzzed even though field
  names / db_columns are never pre-quoted in practice.

## Flag dependency
The suffix is rendered only when `update_conflicts=True` (→ `OnConflict.UPDATE`)
and the backend `supports_update_conflicts_with_target`. The db_column distinction
is observable only when a field declares `db_column` ≠ its name; G-CONF fuzzes both
`column == name` and `column ≠ name` field records.

## G-CONF fuzz seed
Pinned seed: **16315**. ≥10^5 fuzzed inputs over identifier alphabets for field
names and db_columns (including `column == name` and `column ≠ name`, mixed-case,
and pre-quoted identifiers), with 0–6 unique fields and 0–6 update fields.
