# mapping.md — django__django-14007

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 619f26d2895d121854b1bed1b535d42b722e2eba`, states the type
abstraction, and gives the provenance of the one axiom + the deep-model
reference.

Repo file under change: `django/db/models/sql/compiler.py`
(class `SQLInsertCompiler`, method `execute_sql`, line 1403 @ base_commit).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `execute_returning(rows, chains, ncols)` | `SQLInsertCompiler.execute_sql(returning_fields)` — `django/db/models/sql/compiler.py:1403` (patched tail, lines 1412–1421) | the modeled changed function: the row-returning insert path, whose returned raw rows must be passed through the per-column converter pipeline before return |
| `apply_row(row, chains, ncols)` | the per-row body of `SQLCompiler.apply_converters` — `compiler.py:1110` (inner `for pos … for converter in convs` loops) | helper: applies each column's converter chain to one row |
| `fold_chain(chain, value)` *(deep model — A-reference)* | the innermost converter fold `for converter in convs: value = converter(value, expression, connection)` inside `SQLCompiler.apply_converters` — `compiler.py:1116-1117` | pure spec: left-fold of one column's converter chain over the raw value (empty chain = identity) |
| `step(converter_id, value)` *(axiom — A-consumed, weakest)* | one element of `convs` — a single value converter, i.e. an entry of `field.get_db_converters(connection)` / `connection.ops.get_db_converters(expression)` (`fields/__init__.py:746-749`, e.g. a field's `from_db_value`) | unchanged callee: one converter applied to one value; opaque (`Ensures(True)`) |

Supporting unchanged callees the patch invokes but the model does not need to
name (their results are inputs to `execute_returning` in the model):
`self.query.get_meta()` (the `opts`), `field.get_col(opts.db_table)` (builds the
`cols`, `compiler.py` patched line `cols = [...]`), and
`SQLCompiler.get_converters(cols)` (`compiler.py:1100`, builds the
`pos -> (convs, expression)` dict). In the model the converter chains per column
(`chains`) and the raw rows (`rows`) are the abstracted inputs; `ncols` is the
number of returning columns (`len(self.returning_fields)`).

The three raw-row sources the pre-patch `execute_sql` selects between
(`fetch_returned_insert_rows`, `[fetch_returned_insert_columns(...)]`,
`[(last_insert_id(...),)]`, `compiler.py:1414-1421`) are backend-feature-gated
and UNCHANGED by the patch; they only produce the raw `rows` the model takes as
input. The patch's edit is solely the addition, after the row-source branches,
of `cols`/`converters`/`apply_converters` and returning the converted rows.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| returned rows: an iterable of row tuples, each a tuple of DB column values | `PSeq[PSeq[int]]` (rows of int column values) | `rows[j][p]` ↔ column `p` of row `j`; `len(rows)` ↔ number of returned rows; `len(rows[j])` ↔ number of returning columns |
| one DB column value (e.g. an integer primary key) | `int` | the F2P case returns an integer auto/primary key; the value carrier is `int` |
| a field's converter list `convs` (from `get_db_converters`) | `PSeq[int]` of opaque converter ids (`chains[p]`) | each id ↔ one converter callable; `len(chains[p])` ↔ `len(convs)`; an empty chain ↔ a column with no converter (`get_converters` omits it; the `else`/no-op path) |
| applying one converter `converter(value, expression, connection)` | `step(converter_id, value)` | the converter is a pure value→value map for the tested fields (it ignores `expression`/`connection` for `from_db_value` wrappers); modeled opaquely |
| `list(apply_converters(rows, converters))` | `execute_returning(rows, chains, ncols)` result | the materialized converted rows |

Rows/values are pure sequences; the spec quantifies over rows and columns
directly (no heap permission needed). `int` column values stand in for arbitrary
DB scalars on the tested path (integer primary keys).

## 3. Axiom + deep-model provenance (checked by G-AX / axiom_check.py)

### 3.1 `step` axiom (A-consumed, weakest contract)
**Callee:** one value converter — an element of the `convs` list that
`SQLCompiler.get_converters` assembles from `field.get_db_converters(connection)`
and `connection.ops.get_db_converters(expression)`. For the field in the issue
this list is `[field.from_db_value]` (`Field.get_db_converters`,
`django/db/models/fields/__init__.py:746-749`: returns `[self.from_db_value]`
when the field defines `from_db_value`).

**Contract:** `Ensures(True)` — the WEAKEST possible. The model makes NO
assumption about what a converter returns; crucially it does NOT assume the
converter is the identity. This is exactly what soundness requires: the model's
postcondition is `Result()[j][p] == fold_chain(chains[p], rows[j][p])`, i.e. the
result is whatever the real converter fold produces, with no claim that it
equals the raw value. The pre-patch (raw passthrough) cannot prove the result
equals the fold precisely because `step` is opaque (not provably identity) — the
discriminating clause. An `Ensures(True)` axiom cannot over-claim, so it is
trivially sound for any real total converter; G-AX confirms representative real
converters (including a `from_db_value` wrapper) return a value.

### 3.2 `fold_chain` / `execute_returning` deep model ↔ `apply_converters` (A-reference)
**Callee:** `SQLCompiler.apply_converters(rows, converters)`,
`django/db/models/sql/compiler.py:1110-1119` @ base_commit — an UNCHANGED method
the patch newly calls on the returned insert rows. Source:

```python
def apply_converters(self, rows, converters):
    connection = self.connection
    converters = list(converters.items())
    for row in map(list, rows):
        for pos, (convs, expression) in converters:
            value = row[pos]
            for converter in convs:
                value = converter(value, expression, connection)
            row[pos] = value
        yield row
```

This is, per row, per converter-bearing column, the LEFT FOLD of that column's
converter chain over the raw value, leaving every other column untouched —
exactly `execute_returning` / `apply_row` / `fold_chain` in model.py (empty
chain = identity = an untouched column, matching `get_converters` omitting
no-converter columns and the patch's `if converters:` guard being a no-op when
there is nothing to apply). The changed operation (whether the conversion runs
at all on the insert-returning path) is modeled DEEPLY (the spelled-out nested
fold), NOT behind a consumed axiom about `apply_converters`; G-AX validates the
deep model `== apply_converters`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`SQLCompiler.apply_converters` (imported from Django in-container; verbatim
transcription as a stdlib-only fallback) on boundary cases — 0 rows, the issue's
single-row single-`from_db_value`-column `create` case, the multi-row
`bulk_create` case, empty chains (identity passthrough), multi-column mixed,
order-sensitive multi-step chains, zero columns — plus 20 000 randomized
(rows × columns × per-column chain) fuzz cases, asserting the deep model
`execute_returning` equals the real callee on every observation, and that the
exercised converters meet the `step` axiom (`Ensures(True)`). Exit 0 iff sound.
No flag dependency (the fold is connection/expression-agnostic for the modeled
converters).
