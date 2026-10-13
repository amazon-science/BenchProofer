# mapping.md — django__django-13089

## Symbol binding (file:line @ base_commit 27c09043da)
Modeled function: the size-bounding maintenance pass
`BaseDatabaseCache._cull`, `django/core/cache/backends/db.py:255-272` (the
`else` arm, `:258-272`). The gold patch rewrites the final delete: the
culling-boundary row fetched by `cursor.fetchone()` is bound to a local and the
`DELETE ... WHERE cache_key < %s` is performed only when that fetch returned a
row.

Lean modeled function name: `cull` (neutral — it names the *behavior* "trim the
store back under capacity", not a patched private symbol; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `cull` (modeled pass) | `BaseDatabaseCache._cull`, `db.py:255-272` |
| `frequency` | `self._cull_frequency`, `db.py:256,266` |
| `capacity` | `self._max_entries`, `db.py:265` |
| `now` | the reference instant passed to `_cull` (`db.py:255`); the `DELETE ... WHERE expires < now` cutoff at `db.py:261-262` |
| `entries` | the stored rows of the cache table (each a `cache_key` + `expires`) |
| `keepUnexpired now entries` | the rows surviving `DELETE FROM <t> WHERE expires < now`, `db.py:261-262` |
| `remaining.length` | `num = cursor.fetchone()[0]` after `SELECT COUNT(*)`, `db.py:263-264` (the count of survivors) |
| `cullBoundary remaining (len/frequency)` | `cursor.execute(cache_key_culling_sql() % table, [cull_num]); cursor.fetchone()` — the boundary `cache_key`, `db.py:266-269`/post `:267-270` |
| `keepAboveKey k remaining` | `DELETE FROM <t> WHERE cache_key < <k>`, `db.py:270-272`/post `:271-273` |
| result | the set of rows remaining in the table after the pass |

`cache_key_culling_sql()` (`django/db/backends/base/operations.py:77-85`) =
`"SELECT cache_key FROM %s ORDER BY cache_key LIMIT 1 OFFSET %%s"` — it returns
the first cache_key after the `cull_num` smallest, i.e. the key at ascending
offset `cull_num`, or NO ROW when `cull_num >= count`. `cull_num = num //
self._cull_frequency` (`db.py:266`).

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self._cull_frequency : int` (≥ 0) | `frequency : Nat` |
| `self._max_entries : int` (may be set negative to force culling) | `capacity : Int` |
| reference instant / expiry cutoff (a monotone `datetime`) | `now : Int` (order-only surrogate; the only operation is `expires < now`) |
| a stored row `(cache_key : str, expires : datetime)` | `Entry := { key : String, expires : Int }` |
| the stored rows (a set, keyed by distinct `cache_key`) | `entries : List Entry` (distinct keys) |
| `[e for e in rows if e.expires >= now]` | `keepUnexpired now entries = entries.filter (now ≤ ·.expires)` |
| `sorted(cache_key)[offset]` else no-row | `cullBoundary xs offset = ((xs.map (·.key)).mergeSort (· ≤ ·))[offset]?` |
| `DELETE ... WHERE cache_key < k` | `keepAboveKey k xs = xs.filter (¬ ·.key < k)` |
| exception / completes | `Option (List Entry)` — `some survivors` = pass completes; (`none` is the pre-patch crash, used only in the prepatch impl) |

### datetime surrogate note
`now` and `expires` are compared by `<` / `≥` ONLY (the expiry filter). No
arithmetic on instants is performed, so an `Int` order-surrogate is an exact
model of the `datetime` comparison (DECISIONS.md float/order rule applied to a
totally-ordered instant type). G-CONF drives integer instants directly.

### string ordering note
The boundary lookup orders `cache_key` strings ascending and the final delete
compares `cache_key < k`. Python `str` ordering and Lean `String.<` are both
lexicographic by Unicode code point and agree exactly. G-CONF draws keys from a
lowercase-ASCII pool, the regime where the two orderings provably coincide, so
the boundary computation is differential-tested soundly.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `cache_key_culling_sql()` is the
  ordering+offset SELECT; its observable result (the offset-th ascending key, or
  no row) is modeled deeply as `mergeSort` + `[offset]?`, an I/R op, not an
  axiom. `SELECT COUNT(*)` enters as `remaining.length`. The expiry/boundary
  `DELETE`s enter as `filter`s.
- Flag dependency: the `self.clear()` short-circuit fires iff
  `self._cull_frequency == 0` (`db.py:256`); modeled as `frequency = 0 →
  result = some []`. The boundary delete fires iff the survivor count exceeds
  capacity (`num > self._max_entries`, `db.py:265`) AND the boundary fetch
  returned a row (the patched guard `if last_cache_key:`).

## G-LEAK
The problem_statement names `_cull`, `cache.backends.db`, `cursor`,
`fetchone`, `cache_key_culling_sql`, `cull_num`, and the `DELETE`/`NoneType`
text. The spec view deliberately avoids ALL of these: it speaks of a
"size-bounded key/value store", a "maintenance pass", a "culling boundary", and
records with a `key`/`expires` — neutral behavioral vocabulary. The modeled
identifiers (`cull`, `Entry`, `keepUnexpired`, `cullBoundary`, `keepAboveKey`,
`frequency`, `capacity`) share no patched def/class name as a substring (the
patch touches no `def`/`class` line — it edits the body of `_cull`).

## Pinned G-CONF fuzz seed
`13089`.
