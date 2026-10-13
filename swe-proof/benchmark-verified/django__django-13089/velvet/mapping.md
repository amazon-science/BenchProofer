# mapping.md — django__django-13089

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 27c09043da52ca1f02605bf28600bfd5ace95ae4`, states the type
abstraction (the Lean↔Python bijection), and records why G-CONF is skipped.

Repo file under change: `django/core/cache/backends/db.py`.
Changed method: `DatabaseCache._cull(self, db, cursor, now)`
(`db.py:259`; the touched step is `db.py:267–272` post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `cullStep (fetched : Option (List Int))` | the final cull step inside `DatabaseCache._cull` — `django/core/cache/backends/db.py:269–271` | the modeled changed behavior: the single-row lookup → conditional boundary delete |
| `fetched` | `cursor.fetchone()` result of the `cache_key_culling_sql()` SELECT (`db.py:270` pre-patch / `last_cache_key`, `db.py:270` post-patch) | the single-row lookup: one DB row (`tuple` of columns) or `None` |
| `out` (`Option Int`) | the boundary key passed to `cursor.execute('DELETE … WHERE cache_key < %s', [last_cache_key[0]])` (`db.py:271` post-patch) — or "no delete issued" | the observable: which boundary the trim uses, or none |

No callee is axiomatized. The lookup result is taken AS the modeled input; the
follow-up DELETE is observed only through the boundary key it targets, modeled
deeply as the returned `Option Int`. There is no consumed axiom (no `axiom`
declarations) and no A-reference deep model of an external callee.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `cursor.fetchone()` result | `Option (List Int)` | a DB row `(c0, c1, …)` ↔ `some [c0, c1, …]`; `None` (no row) ↔ `none`. A genuine result row has ≥1 column ⇒ `require ∀ row, fetched = some row → row ≠ []`. |
| one DB column value | `Int` | column values are opaque comparables; only the FIRST column (`row[0]` ↔ `row.head!`) is read by the operation. |
| `last_cache_key[0]` (the boundary key) | `row.head!` (first element) | present-row ⇒ `out = some (row.head!)` ↔ the key passed to the DELETE. |
| "the DELETE was issued / not issued" | `out.isSome` / `out = none` | a delete is issued iff a boundary key exists; `none` ⇔ no row ⇔ no delete attempted. The DELETE's row-level side effect is abstracted to the boundary it would use. |

The Python truthiness guard `if last_cache_key:` is modeled as
`if fetched.isSome` — `require row ≠ []` makes the two coincide: a present row is
truthy (non-empty tuple), an absent row is falsy (`None`). Empty-tuple truthiness
is excluded by the precondition, matching a real single-column SELECT result.

## 3. Callee provenance

None. `cursor.fetchone()` is the input boundary (its result is the modeled
input, not a consumed contract); `cursor.execute(DELETE …)` is observed through
the boundary key (the returned value). Neither is axiomatized or deep-modeled as
an A-reference — the control flow between them is the entire modeled behavior,
tagged I/R in refinement.md.

## 4. G-CONF — SKIPPED (conf_skip = true)

There is no pure, DB-free R/I shadow to differential-test. The two operations
the control flow sequences — `cursor.fetchone()` and `cursor.execute('DELETE …')`
— are live DB-API cursor operations whose behavior only exists relative to a real
backend mid-`_cull` (a populated cache table inside the cull transaction):

* `fetchone()` returns a meaningful empty-vs-nonempty row only after the
  preceding `cache_key_culling_sql()` SELECT runs against real rows;
* `execute(DELETE …)`'s only observable is the rows it removes from that same
  backend.

Reproducing the empty-result case (the bug trigger: `_max_entries = -1` forces a
cull on an effectively empty store) requires standing up the full Django cache
backend + DB connection — i.e. the F2P integration test itself
(`test_cull_delete_when_store_empty`), not a fuzzed pure transliteration. The
abstraction the spec pins (the boundary key) has no DB-free oracle to diff
against. Therefore `meta.json conf_skip = true` and `conformance_check.py` is a
`status=skip` stub (exit 0). Soundness of the modeled None-guard control flow is
carried by **G-VERIFY** (the guard provably yields `none` on the absent branch,
never subscripting an absent row) and **G-DIFF** (the prepatch, which subscripts
unconditionally, fails exactly the `fetched = none → out = none` clause — the
'NoneType is not subscriptable' bug the issue reports).
