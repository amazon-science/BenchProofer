# mapping.md — django__django-14007

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 619f26d2895d121854b1bed1b535d42b722e2eba`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `transformedResultRows (rows convs)` | `SQLInsertCompiler.execute_sql(self, returning_fields=None)` — `django/db/models/sql/compiler.py:1402` (body lines 1403-1425 post-patch) | the modeled changed function: the rows assembled from the DB cursor and the result it returns |
| `convertRow (convs row)` | the body of `apply_converters` for a single row (`compiler.py:1110`), applied with the converter list built by `get_converters`/`get_col` (`compiler.py:1100`, fields `get_db_converters`) | pure spec: per-column transform of one row |
| `convertRows (convs rows)` *(deep model — A-reference)* | `apply_converters(rows, converters)` — `django/db/models/sql/compiler.py:1110` | pure spec: the whole result is the per-row transform; deep model of the unchanged callee `apply_converters`, validated `convertRows == apply_converters` by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo behavior the change removes (refinement audit only, not in
the consumer spec view): `execute_sql` returned the freshly-fetched cursor rows
**directly** (`return self.connection.ops.fetch_returned_insert_rows(cursor)`,
`return [...fetch_returned_insert_columns...]`, `return [(last_insert_id...,)]`)
without ever calling `get_converters`/`apply_converters` — so a field's
`from_db_value` hook never ran on an INSERT-returned value.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the assembled `rows` (a `list` of row tuples, each a tuple of column values returned by the INSERT) | `List (List Int)` | `rows` (Python `list[tuple]`) ↔ `List (List Int)`; row `i` ↔ `rows[i]`; column `j` of row `i` ↔ `rows[i][j]`; `len(rows)` ↔ `rows.length` |
| one returned column value (an integer the DB produced for a returning field, e.g. an autoincrement pk) | Lean `Int` | the test's `MyWrapper(v)` and the bare `v` compare `==` to the same int (`MyWrapper.__eq__`), so the *carried integer* is the observable; the wrapper is the transform's TAG (see §3) |
| the per-column converter chain `converters[pos] = (convs, expression)` produced by `get_converters`(`get_col`,`get_db_converters`) | `List (Int → Int)` | column `j`'s converter chain ↔ `convs[j]`, an `Int → Int`; a column with no converter ↔ a position past the end of `convs` (identity by `convertRow`'s short-list clause). The integer-valued model of `from_db_value`/backend converters: see §3 |
| `cursor`, `self.connection`, `self.query`, `as_sql()`, SQL execution | omitted (effectful preamble) | the loop that runs the SQL and the branch that *assembles* `rows` are effectful I and structurally unchanged by the patch; the modeled, behavior-changing step is the conversion now applied to the assembled `rows` (mapping.md §3, refinement.md) |

Modeling note (grounding, directive 8): the spec pins `out = convertRows convs
rows` — the result is *produced by* applying the actual per-column transformers
to the actual assembled rows, not equated to any opaque oracle. With an empty
`convs` (no field defines a converter) `convertRows` is the identity, matching
the patch's `if converters:` guard (no converters ⇒ rows returned unchanged).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `convertRows`/`convertRow` deep model ↔ `apply_converters` (A-reference)
**Callee:** `SQLCompiler.apply_converters(rows, converters)`
(`django/db/models/sql/compiler.py:1110`), an UNCHANGED method the patch newly
*calls*. Its body:

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

Each `converters` entry keys a column position `pos` to a chain of converter
callables; `apply_converters` replaces `row[pos]` with the left-to-right
composition of that chain applied to the original value, and leaves every column
without an entry untouched. That is exactly `convertRow`: walk the row, apply
`convs[j]` (the composed chain for column `j`) to column `j`, pass columns past
the end of the converter list through unchanged; `convertRows` maps it over
every row. The converter chain for a returning field is
`backend_converters + field_converters` where `field_converters =
[field.from_db_value]` when the field defines `from_db_value`
(`Field.get_db_converters`, `fields/__init__.py:746`).

The F2P observable is a *type tag*: the test field's `from_db_value` wraps the
integer in `MyWrapper`, and `assertIsInstance(obj.id, MyWrapper)` checks the
wrapper is present. Because `MyWrapper.__eq__` compares equal to the underlying
int, the carried integer is preserved; the converter's effect that the test
observes is "the value went through the converter at all." We model a converter
faithfully as an arbitrary `Int → Int` (G-AX fuzzes integer-valued converters,
including identity and `+k`/`*k`/wrapper-preserving maps); the *structural*
claim G-AX validates is positional: `convertRows convs rows ==
apply_converters(rows, converters)` for converter chains presented as the
column→callable map, over boundary and fuzzed `rows`/`convs`.

**Soundness check (G-AX):** `axiom_check.py` constructs the real
`apply_converters` (lifted out of the compiler so it runs stdlib-only) and
asserts `convertRows == apply_converters` on boundary cases (empty rows, empty
converters, short converter list, single column, ragged rows) plus randomized
fuzz over integer converters. Exit 0 iff sound. There is **no consumed axiom**:
the conversion is modeled deeply, so its callee is an A-reference, not an oracle.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14007`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `convertRow`/`convertRows` (R/I-tagged ops) to Python over the
real `list[tuple]`/converter-map types and diffs against the patched
`execute_sql`'s conversion behaviour (`get_converters` + `apply_converters`
applied to the assembled rows). The conversion callee `apply_converters` is
A-reference (deep-modeled) — G-CONF runs the real `apply_converters` as the
oracle for the conversion leg.
