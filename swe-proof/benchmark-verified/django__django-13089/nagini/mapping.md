# mapping.md — django__django-13089

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 27c09043da52ca1f02605bf28600bfd5ace95ae4`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/core/cache/backends/db.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `boundary_for_prune(row)` | the prune-boundary handling inside `DatabaseCache._cull(self, db, cursor, now)` — `django/core/cache/backends/db.py:255` (changed hunk at body lines 270-272) | the modeled changed behaviour: decide whether to issue the prune DELETE from the fetched boundary row, and with what key |
| parameter `row: Optional[List[int]]` | `cursor.fetchone()` — the result of executing `connection.ops.cache_key_culling_sql() % table` (`db.py:267-269`) | the fetched boundary row: `None` when the culling SELECT returns no row, else a present DB-API row (a tuple/sequence of column values) |
| `Result(): Optional[int]` | the `cache_key` value bound into the `DELETE ... WHERE cache_key < %s` statement (`db.py:270-272`), or "no DELETE issued" | the produced boundary key (the parameter the prune is bound to), absent when no prune is issued |

There is **no separate change site**: the gold patch is a single hunk that wraps
the boundary subscript-and-DELETE in a presence guard. The surrounding
`_cull` logic (`DELETE ... expires < now`, `SELECT COUNT(*)`, the
`num > self._max_entries` test, `cull_num = num // self._cull_frequency`, the
`cache_key_culling_sql()` execute) is UNCHANGED and is not modeled — it carries
no behavioural discrimination for the fixed defect.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `cursor.fetchone()` result: `None`, or a DB-API row (a non-empty sequence whose `[0]` is the `cache_key` boundary value) | `Optional[List[int]]` | `None` ↔ `None`; a present row ↔ a non-empty `List[int]`; `row[0]` (the boundary `cache_key`) ↔ `row[0]`; `len(row) > 0` holds because the culling `SELECT` projects exactly one column (`cache_key`), so a returned row always has at least that column |
| the `cache_key` value (a string) bound into the DELETE | `int` (a single column value) | the modeled defect is presence/absence of the row, not the lexical content of the key; a single `int` column value is the faithful carrier for "the boundary value passed to DELETE" |
| `if last_cache_key:` (DB-API row truthiness) | `if row is not None:` | a `cursor.fetchone()` result is either `None` or a non-empty row; a DB row is never an empty tuple here (it always carries the `cache_key` column), so truthiness ↔ `is not None`. The empty/falsy-but-not-None case does not arise for a single-column fetch, so `is not None` is the faithful refinement of the guard. |
| "issue the DELETE with key `last_cache_key[0]`" vs "issue no DELETE" | `Result() == row[0]` (a present key) vs `Result() is None` (no prune) | the produced `Optional[int]` records whether the prune ran and the value it ran with |

`str` column content is irrelevant to the fixed behaviour (the defect is the
unguarded subscript of a possibly-`None` row), so columns are modeled as `int`
values rather than `List[int]` code points.

## 3. Callee provenance

**None.** No `@ContractOnly` axiom is shipped (the `axioms` region is empty).
The changed behaviour — guard the subscript of the fetched row on its presence —
is modeled **deeply** as optional-row logic over the input `row`. The
`cursor.fetchone()` callee that produces the row is the *source* of the
`Optional[List[int]]` value, not a callee whose contract the proof consumes:
the model takes the (possibly-`None`) row as its parameter and reasons about it
directly. There is therefore no A-consumed axiom and no A-reference deep model
to validate against a real callee, and consequently no `axiom_check.py`
obligation beyond documenting that the DB-API `fetchone()` contract
(`None` on empty result set, otherwise a row sequence) is the standard one the
refinement relies on (see refinement.md).
