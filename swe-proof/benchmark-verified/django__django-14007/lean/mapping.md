# mapping.md — django__django-14007

## Symbol binding (file:line @ base_commit 619f26d2895d121854b1bed1b535d42b722e2eba)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_insertReturnedRows` / `problem_spec_insertReturnedRows` / `correct_insertReturnedRows` | `SQLInsertCompiler.execute_sql(returning_fields=None)` (the rows it returns) | `django/db/models/sql/compiler.py:1402-1421` |
| `RetField` (pure helper) | a field in `self.returning_fields`, with its converter chain | `compiler.py:1421` (`self.returning_fields`); converters via `get_converters` |
| `RetField.converters` | the combined backend + field converter chain for that field's column expression | `compiler.py:1100-1108` (`get_converters` → `backend_converters + field_converters`) |
| `Row` (`List Int`) | one returned tuple of raw cell values | the tuples in `rows` |
| `applyChain` / `convertRow` (pure helpers) | the inner loops of `apply_converters` (each cell run through its converter chain) | `compiler.py:1110-1118` |
| `anyConverter` (pure helper) | `if converters:` truthiness guard | `compiler.py` (patched line: `if converters:`) |

The modeled function is `SQLInsertCompiler.execute_sql` — specifically the rows
it returns for a creating write. It is the behavior the patch changes and the
behavior the FAIL_TO_PASS test observes:

- `custom_pk.tests.CustomPKTests::test_auto_field_subclass_create` creates an
  object whose PK field is a `BigAutoField` subclass with a `from_db_value` hook
  wrapping the raw integer in `MyWrapper`, and asserts the created object's `id`
  is a `MyWrapper` instance (was a plain `int`).

### What the function does (base_commit, the touched region)

```python
def execute_sql(self, returning_fields=None):
    assert not (...)
    self.returning_fields = returning_fields
    with self.connection.cursor() as cursor:
        for sql, params in self.as_sql():
            cursor.execute(sql, params)
        if not self.returning_fields:
            return []
        if self.connection.features.can_return_rows_from_bulk_insert and len(self.query.objs) > 1:
            return self.connection.ops.fetch_returned_insert_rows(cursor)      # batch pathway
        if self.connection.features.can_return_columns_from_insert:
            assert len(self.query.objs) == 1
            return [self.connection.ops.fetch_returned_insert_columns(cursor, self.returning_params)]  # columns pathway
        return [(self.connection.ops.last_insert_id(
            cursor, self.query.get_meta().db_table, self.query.get_meta().pk.column),)]  # last-id pathway
```

Pre-patch, each of the three pathways `return`s its raw rows immediately; the
fetched values never pass through `get_converters` / `apply_converters`, so a
field's `from_db_value` hook is skipped on a creating write. Post-patch, each
pathway instead assigns to `rows`, and after the cursor block the code builds the
column expressions for the returning fields, computes their converter chains via
`get_converters`, and — when any converter exists — maps `apply_converters` over
the rows before returning. This is exactly what an ordinary read query already
does in `results_iter` (`compiler.py:1120-1133`), so the returned values get the
same post-processing as read values.

### Lean modeling

- The raw rows produced by the three backend pathways are **grounded inputs**
  (`batchRows`, `columnsRow`, `lastIdRow`), selected by the capability flags
  `canBatch` (`can_return_rows_from_bulk_insert and len(objs) > 1`) and
  `canColumns` (`can_return_columns_from_insert`). Producing them
  (`fetch_returned_insert_rows`, `fetch_returned_insert_columns`,
  `last_insert_id`) is upstream of and orthogonal to the fix — unchanged by the
  patch — so their results enter as data rather than being re-derived.
- Each returned field's converter chain is grounded as `RetField.converters`
  (`List (Int → Int)`). `get_converters` (combining backend + field converters)
  is unchanged; the chain it yields enters as data.
- The post-processing the patch ADDS — applying the converter chains to the
  fetched rows — is modeled DEEPLY: `convertRow` maps each field's
  `applyChain` (a left-fold of the converters) over the matching cell, and the
  impl maps it over the selected rows only when `anyConverter` holds (the
  `if converters:` guard). SPEC_GUIDE §3 forbids axiomatizing the changed op, so
  this is spelled out, not axiomatized.
- A cell value is modeled as `Int` (a raw database scalar such as a primary-key
  integer); a converter that "wraps" the value is modeled by the `Int → Int`
  function it applies. The F2P `from_db_value` wrap-in-`MyWrapper` corresponds to
  a non-identity converter; the assertion "the result is wrapped" corresponds to
  "the cell was passed through the chain".

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| a returned field's converter chain (`backend_converters + field_converters`) | `RetField.converters : List (Int → Int)` | ordered list; empty ⇔ no converters declared |
| one returned tuple of raw cells | `Row = List Int` | positional; cell `i` ↔ field `i` |
| `self.returning_fields` | `returningFields : List RetField` | positional list |
| `can_return_rows_from_bulk_insert and len(self.query.objs) > 1` | `canBatch : Bool` | identity |
| `can_return_columns_from_insert` | `canColumns : Bool` | identity |
| `fetch_returned_insert_rows(cursor)` | `batchRows : List Row` | the batch-pathway raw rows |
| `[fetch_returned_insert_columns(cursor, returning_params)]` | `[columnsRow]` | one-row columns pathway |
| `[(last_insert_id(...),)]` | `[lastIdRow]` | one-cell last-id pathway |
| `if converters:` | `anyConverter returningFields` | true ⇔ some field has a non-empty chain |
| `list(self.apply_converters(rows, converters))` | `rows.map (convertRow returningFields)` | per-cell converter application |
| `return rows` | `return rows` | the returned list |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — applying the
  returning fields' converter chains to the fetched rows — is modeled DEEPLY
  (`convertRow`/`applyChain`/`anyConverter`). SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op, so the `axioms` region is empty and **G-AX skips**.
- `fetch_returned_insert_rows`, `fetch_returned_insert_columns`, `last_insert_id`
  produce the raw returned rows; they are UNCHANGED by the patch and orthogonal
  to it. Their results are carried as grounded inputs (`batchRows`, `columnsRow`,
  `lastIdRow`); they constrain no output component the spec leaves free.
- `get_converters` (combining `connection.ops.get_db_converters(expression)` with
  `expression.get_db_converters(connection)`) is UNCHANGED; the per-field chain it
  yields is carried as `RetField.converters`.
- **Flag dependency:** the selected pathway depends on
  `can_return_rows_from_bulk_insert` (with `len(objs) > 1`) and
  `can_return_columns_from_insert`; the converter application is unconditional on
  the pathway and gated only by `if converters:`. G-CONF fuzzes all flag/pathway
  combinations and both converter presence/absence.

## G-CONF fuzz seed

Pinned LCG seed: **14007** (see `conformance_check.py` `SEED`). Corpus: randomized
returning-field counts (0..4), each field's converter chain drawn from a small
pool of integer converters (identity, +1000-wrap, ×, …) including empty chains;
all `(canBatch, canColumns)` combinations; randomized raw rows for each pathway.
Hand-picked edge cases pin the discriminating behaviour: a single field with a
wrapping converter over a last-id row must yield the wrapped value, and a field
with no converter must leave the row untouched.
