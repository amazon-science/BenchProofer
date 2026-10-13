# mapping.md — django__django-13807

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 89fc144dedc737a79929231438f035b1d4a993c9`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one deep-model reference.

Repo file under change: `django/db/backends/sqlite3/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildCheckStatements (tables)` | the `chain.from_iterable(... for table_name in table_names)` generator inside `check_constraints` — `django/db/backends/sqlite3/base.py:328-332` | the modeled changed site (1): one integrity-check statement per table name |
| `buildViolationStatements (violations)` | the `for table_name, rowid, … in violations:` loop body inside `check_constraints` — `django/db/backends/sqlite3/base.py:334-348` | the modeled changed site (2+3): per offending row, the foreign-key-listing statement and the value-fetch SELECT |
| `quoteIdent (name)` *(deep model — A-reference)* | `DatabaseOperations.quote_name` — `django/db/backends/sqlite3/operations.py:170` | the SQLite identifier quoter the gold patch newly calls at every identifier position; modeled deeply, validated `quoteIdent == quote_name` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `fkCheckSql` / `fkListSql` / `selectSql` | the three `%`-format SQL templates `check_constraints` assembles (`base.py:330`, `336`, `341-347`) | pure spec: the statement for one table / one row's listing / one row's value-fetch, identifiers quoted |
| `checkStmts` / `violationStmts` | the ordered sequence of statements the two loops construct | pure spec: front-recursive folds; deep model of the loops' string output |

`check_constraints` itself is the function under change; it is NOT axiomatized.
The methods model its two statement-constructing sites; `quote_name` is the
unchanged callee they newly route every identifier through.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a SQL identifier `str` (table / column name) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| the assembled SQL statement `str` | `List Char` | same `str ↔ List Char`; the `'…%s…' % ident` template assembly ↔ literal `List Char` ++ of the fixed fragments around `quoteIdent ident` |
| a single character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| `table_names` (a list of name `str`) | `List (List Char)` | element-wise `str ↔ List Char`; list order preserved |
| one offending row's `(table_name, primary_key_column_name, column_name)` identifiers | `Violation { table, pk, col : List Char }` | the three identifier positions the value-fetch quotes; `rowid` / `foreign_key_index` are not identifiers embedded in SQL text (a bound parameter / a list index), so they are out of the modeled string-construction scope |

The order in which the value-fetch SELECT places its identifiers — `pk`, then
`col`, then `table` — mirrors the gold template `'SELECT %s, %s FROM %s …' %
(primary_key_column_name, column_name, table_name)`.

`List Char` indexing is total and sound; the carrier is `List Char` because the
operation is per-character string assembly.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `quoteIdent` deep model ↔ `DatabaseOperations.quote_name` (A-reference)
**Callee:** `django.db.backends.sqlite3.operations.DatabaseOperations.quote_name`.
The identifier-quoting operation the gold patch introduces is modeled **deeply**
by `quoteIdent` (with `fkCheckSql`/`fkListSql`/`selectSql`) in the `pure` region;
there is **no `quoteName` axiom** the proof consumes. Source at base_commit
(`operations.py:170-173`):

```python
def quote_name(self, name):
    if name.startswith('"') and name.endswith('"'):
        return name  # Quoting once is enough.
    return '"%s"' % name
```

`quoteIdent` encodes exactly this: an identifier already double-quoted at both
ends is returned unchanged; otherwise it is wrapped in double quotes. The method
is a pure string function that does not touch the live connection, so G-AX
constructs `DatabaseOperations(connection=None)` and compares the deep model
against the real callee.

**Soundness check (G-AX):** `axiom_check.py` runs the real `quote_name` on
boundary identifiers (the SQL keywords `order`/`select`/`where` of the F2P
scenario, ordinary identifiers, already-quoted identifiers, and degenerate
quote-only strings) plus 20 000 randomized fuzz identifiers, asserting
`quoteIdent == quote_name` on every one. Imports Django (instance image) + stdlib.
Exit 0 iff sound.

### 3.2 No consumed axioms
There are no `axiom` declarations. The remaining callees `check_constraints`
touches — `cursor.execute(...).fetchall()`, `self.introspection.get_primary_key_column`,
`chain.from_iterable` — are NOT changed by the patch and do NOT appear in the
modeled string-construction; they are out of scope (the patch leaves them
byte-identical), so there is nothing to axiomatize or G-AX. Modeling them would
be a dead axiom (SPEC_GUIDE §0.7).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13807`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `fkCheckSql`/`fkListSql`/`selectSql`/`checkStmts`/`violationStmts`
(R/I-tagged concatenation ops) to Python and leaves `quoteIdent`'s callee as the
real `DatabaseOperations.quote_name` (A-tagged → run real callee, not the model);
it diffs the assembled statement strings against `patch.diff`'s `%`-format
templates.
