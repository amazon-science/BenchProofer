# mapping.md — django__django-12039

## Symbol binding (file:line @ base_commit 58c1acb1d6)

| Lean symbol | Python symbol | file:line @ base |
|---|---|---|
| `implementation_renderColumns` / `problem_spec_renderColumns` / `correct_renderColumns` | `Columns.__str__` (its inner `col_str` generator) | `django/db/backends/ddl_references.py:84-91` |
| `implementation_renderIndexColumns` / `problem_spec_renderIndexColumns` / `correct_renderIndexColumns` | `IndexColumns.__str__` (its inner `col_str` generator) | `django/db/backends/ddl_references.py:111-122` |
| `appendSuffix` | the `col_suffixes[idx]` lookup + conditional append (the changed block) | both `col_str` bodies |
| `quoteName : String → String` | `self.quote_name` (bound callable) | passed into `Columns.__init__` at `:79-82`, `IndexColumns.__init__` at `:107-109` |

## Type bijection (Lean ↔ Python)

| Lean | Python | notes |
|---|---|---|
| `columns : List String` | `self.columns` (`list[str]`) | per-element column names, in order |
| `suffixes : List String` | `self.col_suffixes` (tuple/list of `str`, default `()`) | positional render hints; `''` for ascending order, `'DESC'`/`' DESC'`-style token otherwise |
| `opclasses : List String` | `self.opclasses` (`list[str]`, default `()`) | per-column operator-class annotation; `Index.__init__` guarantees `len(opclasses) == len(columns)` |
| `quoteName : String → String` | `self.quote_name` | identifier-quoting callable; UNCHANGED collaborator, universally quantified |
| result `String` | the `', '.join(...)` return value of `__str__` | rendered column clause |

### Positional-lookup bijection (the soundness-critical R leg)

Python `col_str(column, idx)` indexes `self.col_suffixes[idx]` inside a
`try/except IndexError`. Lean models this total-ly as `suffixes[idx]?`:

- `idx < suffixes.length`  ↔ `self.col_suffixes[idx]` succeeds → `some suffix`.
- `idx ≥ suffixes.length`  ↔ `IndexError` raised → `none` (the `except` branch /
  Lean `none` arm, leaving the entry unchanged).

`enumerate(self.columns)` ↔ `columns.zipIdx` (0-based index paired with element).

For `IndexColumns`, `self.opclasses[idx]` is indexed WITHOUT a guard (the comment
at `:113-114` asserts `len(opclasses) == len(columns)`, so the index is always in
range for real inputs). Lean models it total-ly as `opclasses[idx]?.getD ""`; on
the in-range domain that the real code exercises this equals `opclasses[idx]`,
and out of range it contributes `""` (never reached for real Index objects).
Because Python indexes `self.opclasses[idx]` OUTSIDE the `try` (so an out-of-range
access would raise, not yield `""`), the modeled domain is pinned explicitly:
`correct_renderIndexColumns` carries the precondition binder
`columns.length ≤ opclasses.length`, exactly the `Index.__init__` invariant. The
G-CONF oracle replicates the real (length-guaranteed) behavior; G-CONF fuzzes
only `len(opclasses) == len(columns)`.

## Callee provenance + flag deps

- `self.quote_name` — UNCHANGED collaborator (a backend identifier-quoter, e.g.
  `BaseDatabaseSchemaEditor.quote_name`). NOT on the fix list, NOT axiomatized:
  modeled as an arbitrary `quoteName : String → String` universally quantified in
  both `correct_*` statements, so the contract holds for every quoting behavior.
  No `axiom`/`opaque` declared (no consumed axiom, no A-reference).
- No flag-dependent callee. The only behavioral switch is the per-entry
  emptiness of the positional hint (`if suffix:`), modeled directly.

## G-CONF fuzz seed

Pinned seed: **12039** (also recorded in meta.json `verifier_pins.conf_seed`).
