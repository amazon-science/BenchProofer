# mapping.md — symbol binding & type bijection (django__django-13807)

## Modeled function
- **Lean** `implementation_fkCheckQueries : List Char → List Char → List Char →
  (List Char × List Char × List Char)`
- **Python** `DatabaseWrapper.check_constraints(self, table_names=None)` —
  `django/db/backends/sqlite3/base.py:316-353 @ base_commit` (the
  `supports_pragma_foreign_key_check` branch, lines 326-345).

`check_constraints` iterates over `table_names`, and for each violating row it
builds three SQL query strings from identifiers (the table name, the primary-key
column name, and the foreign-key column name):

```python
'PRAGMA foreign_key_check(%s)' % table_name                       # line 330
'PRAGMA foreign_key_list(%s)'  % table_name                       # line 336
'SELECT %s, %s FROM %s WHERE rowid = %%s' % (                     # lines 341-343
    primary_key_column_name, column_name, table_name)
```

The observable behavior demanded by the F2P test
(`test_check_constraints_sql_keywords`, table `db_table = 'order'`, columns
`select` / `where`) is that each identifier substituted into a query is rendered
so that a SQL reserved word is parsed as a name, not as syntax. Pre-patch the raw
identifier is interpolated (`PRAGMA foreign_key_check(order)` → SQLite
`OperationalError: near "order": syntax error`); post-patch each identifier is
double-quoted (`PRAGMA foreign_key_check("order")`).

`implementation_fkCheckQueries` models exactly the three query-string builders
for a single (table, primaryKey, column) triple — the per-row, per-table work.
The surrounding control flow (the `chain.from_iterable` over `table_names`, the
cursor I/O, `fetchall()/fetchone()`, the `IntegrityError` message) is database/IO
plumbing orthogonal to the fix and is not modeled; the fix touches ONLY how
identifiers are rendered into these three strings.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `table_name` (str identifier) | `table : List Char` | a SQL table identifier, per-character |
| `primary_key_column_name` (str) | `primaryKey : List Char` | PK column identifier |
| `column_name` (str) | `column : List Char` | FK column identifier |
| the three rendered query strings | `List Char × List Char × List Char` | `(fkCheck, fkList, selectRow)`, per-character |

String ↔ `List Char` is the standard per-code-point bijection (SPEC_GUIDE §2).
`%s` substitution into a *literal* SQL template is, semantically, fixed-order
concatenation of the literal text and the substituted value, reproduced exactly
in both spec and impl.

## Callee provenance
- **`self.ops.quote_name(name)`** — `DatabaseOperations.quote_name`,
  `django/db/backends/sqlite3/operations.py:170-173 @ base_commit`:
  ```python
  def quote_name(self, name):
      if name.startswith('"') and name.endswith('"'):
          return name           # Quoting once is enough.
      return '"%s"' % name
  ```
  UNCHANGED by the patch. It is a tiny, total, pure string operation, so it is
  modeled **deeply** as `quoteIdentifier` (an **A-reference**, not a consumed
  axiom): wrap in double quotes unless already double-quoted at both ends. G-AX
  (`axiom_check.py`) runs the REAL `quote_name` against `quoteIdentifier` over
  boundary + fuzz inputs to validate the model.
- The cursor / `chain.from_iterable` / `fetchall` / `IntegrityError` plumbing is
  IO and is not part of the modeled string-building behavior.
- No UNCHANGED callee *property* is consumed as an `axiom <callee>_prop`; the
  axioms region is empty.

## Flag dependency
None. `quote_name` is unconditional in the patched code; both quoted and unquoted
inputs are exercised by G-AX (the `already-quoted` idempotence branch and the
plain branch).

## G-CONF fuzz seed
Pinned seed: **13807**. ≥10^5 fuzzed inputs over SQL-identifier alphabets
(including reserved words `order`/`select`/`where`, already-quoted names, and
empty names) across all three (table, primaryKey, column) positions.
