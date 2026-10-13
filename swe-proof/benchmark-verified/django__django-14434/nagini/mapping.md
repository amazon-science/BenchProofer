# mapping.md — django__django-14434

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5e04e84d67da8163f365e9f5fcd169e2630e2873`, states the type
abstraction, and gives the provenance of each deep-model reference (the
unchanged framework helper the deep model is validated against, with source).

Repo file under change: `django/db/backends/base/schema.py`
(`BaseDatabaseSchemaEditor._create_unique_sql`).
Unchanged helpers the change wires together:
`django/db/backends/ddl_references.py` (`Table`, `TableColumns`, `Columns`,
`Statement`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_constraint_columns(db_table, columns)` | the column-bearing-part construction inside `_create_unique_sql` — `django/db/backends/base/schema.py:1244,1254,1256` (the `table = …` assignment and the `columns = self._index_columns(table, …)` / `Expressions(…)` call that records the table against the columns) | the modeled changed function: what value (table name vs. handle) the constraint's columns part records as its table |
| `ConstraintPart` | `Columns` / `TableColumns` — `django/db/backends/ddl_references.py:77-96` / `60-74` | minimal class with only the two touched facets: the recorded table identifier (`table`) and the constrained column set (`columns`), plus `plain` discriminating bare-name vs. decorated handle |
| `constrains_column(plain, table, cols, q_table, q_col)` | `TableColumns.references_column` — `django/db/backends/ddl_references.py:67-68` (`return self.table == table and column in self.columns`) | pure spec: exact semantics of the column-reference test on a column-bearing part |
| `constrains_table(table, q_table)` | `Table.references_table` — `django/db/backends/ddl_references.py:49-50` (`return self.table == table`) | pure spec: exact semantics of the table-reference test |
| `member(c, cols)` *(deep model — A-reference)* | the Python membership operator `column in self.columns` used by `TableColumns.references_column` (`ddl_references.py:68`) | pure spec: column-code membership in the recorded column set; the deep model of the unchanged `in` callee, validated `member == in` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo construct the change removes (for the refinement audit, not
referenced from the consumer spec view): `table = Table(model._meta.db_table,
self.quote_name)` (`schema.py:1244`) — a `Table` **wrapper instance** — was
passed as the `table` argument of `_index_columns(table, …)`
(`schema.py:1254`) and `Expressions(model._meta.db_table, …)`
(`schema.py:1256` used the raw name there but the index branch used the
wrapper). The gold sets `table = model._meta.db_table` (the bare name) and only
wraps it in `Table(table, self.quote_name)` for the `table=` keyword of the
emitted `Statement` (`schema.py:1259` post-patch).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `model._meta.db_table` (a `str`) | `List[int]` of code points (carrier), `PSeq[int]` (spec) | `s[k]` ↔ `db_table[k] == ord(s[k])`; `len(s)` ↔ `len(db_table)`; `str ==` ↔ `PSeq ==` via `ToSeq`; an empty `str` ↔ `[]` |
| the column names `self.columns` (a sequence of `str`) | `PSeq[int]` of column-identifier codes | each distinct column name ↦ a distinct `int` code; `column in self.columns` ↔ `member(code, cols)`; the membership/equality the F2P test observes is preserved under any injective name→code map (the test asks only "is column `name` referenced") |
| `Table(table, quote_name)` wrapper instance vs. bare `table` string, as the value recorded against the columns | `ConstraintPart.plain` (`bool`) + `ConstraintPart.table` (`List[int]`) | `plain == True` ↔ recorded value is the bare `str` (value-comparable to a queried bare name); `plain == False` ↔ recorded value is a `Table` instance, which defines no `__eq__`, so `self.table == <bare name>` is identity comparison ⇒ always `False`. This boolean IS the pre-/post-patch distinction. |
| `quote_name` callable carried by `Table`/`Columns` | omitted | `quote_name` affects only `__str__` (SQL rendering); it does not affect `references_column` / `references_table`, the only behaviour the F2P test observes. |
| `Statement` container `any(part.references_column(...) for part in parts)` (`ddl_references.py:184-188`) | the single column-bearing part's test | for a unique constraint the column reference can only come from the columns part (the `table=` part is a `Table`, whose `references_column` is the inherited `False` from `Reference`); the disjunction reduces to the columns part. |

`str` indexing/iteration is banned in Nagini, so identifiers are `List[int]`;
column names are abstracted to integer codes (only their equality/membership is
observed). The specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `member` deep model ↔ Python `in` (A-reference)
**Callee:** the membership operator `column in self.columns` inside
`TableColumns.references_column` (`ddl_references.py:68`). It is unchanged by
the patch. The membership is modeled **deeply** by the `@Pure` front-recursive
`member` (pure region); there is **no consumed `@ContractOnly` axiom**. The
deep model is validated **== Python `in`** out-of-band by axiom_check.py
(G-AX): `member(c, cols) == (c in cols)` on boundary + 20 000 fuzz inputs.

### 3.2 `constrains_column` / `constrains_table` ↔ real `ddl_references` (A-reference)
**Callees:** `TableColumns.references_column` (`ddl_references.py:67-68`) and
`Table.references_table` (`ddl_references.py:49-50`), both unchanged. Their
exact semantics

```python
def references_column(self, table, column):
    return self.table == table and column in self.columns   # TableColumns
def references_table(self, table):
    return self.table == table                              # Table
```

are reproduced by `constrains_column` / `constrains_table`. axiom_check.py
constructs the REAL `Columns` / `Table` objects two ways — (post) recording the
**bare** `db_table` string, (pre) recording a `Table(...)` **handle** — and
asserts:
  * post: `Columns(db_table, cols, q).references_column(db_table, c)` equals
    `constrains_column(True, db_table, cols, db_table, c)` (and is `True`
    for `c ∈ cols`);
  * pre: `Columns(Table(db_table, q), cols, q).references_column(db_table, c)`
    is **always `False`** (a `Table` instance never `==` the bare name — it
    defines no `__eq__`), equal to `constrains_column(False, …)`.

This is the decisive behaviour the F2P test `test_unique_constraint` observes:
`sql.references_column(table, 'name')` must be `True`. The single behavioural
change — recording the **bare table name** rather than the **`Table` handle**
against the columns — lives in `ConstraintPart.plain` (model) ⇔ `table =
model._meta.db_table` rather than `Table(model._meta.db_table, …)` (real).
Docs/source: Django `django/db/backends/ddl_references.py` (BSD-licensed,
in-repo). The `Table` class defining no `__eq__` is verified directly against
the class in axiom_check.py.

**Soundness check (G-AX):** axiom_check.py imports only the standard library
(it reproduces the unchanged `ddl_references` value semantics verbatim from the
cited source and exercises the real Python `==`/`in` operators) and exits 0 iff
every observation matches the model. No repo-specific or network import.

## 4. Conformance (G-CONF)

conformance_check.py runs the contract-stripped impl region (shadow) against
the real patched `_create_unique_sql` construction in-container over the
section-2 bridge (`str` ↔ code points; column names ↔ per-scenario injective
int codes), comparing `references_column` / `references_table` on the
column-bearing part and the whole `Statement`. Pinned fuzz seed: **14434**
(the instance number); ≥1e5 reference-query checks.
