# mapping.md — django__django-11138

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c84b91b7603e488f7171fdff8f08368ef3d6b856`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo files under change (gold patch.diff): `django/db/backends/mysql/operations.py`,
`django/db/backends/oracle/operations.py`, `django/db/backends/sqlite3/base.py`,
`django/db/backends/sqlite3/operations.py`.

The modeled site is the MySQL `_convert_field_to_tz` — the SQL-expression
builder the problem statement explicitly cites (the line that forces `'UTC'`).
It carries the *complete* discriminating logic of the fix in a single,
self-contained, pure string computation (see §3).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildTzAdjustedExpr` | `DatabaseOperations._convert_field_to_tz(self, field_name, tzname)` — `django/db/backends/mysql/operations.py:71` (body lines 72-74) | the modeled changed function (builds the SQL field expression, converting the stored timestamp's zone when needed) |
| `tzAdjustedExpr` (pure deep model) | the `if … : field_name = "CONVERT_TZ(%s, '%s', '%s')" % (...)` body of `_convert_field_to_tz` post-patch | pure spec: the conversion-wrapping decision + the wrapped SQL string |
| `active : Bool` | `settings.USE_TZ` (read inside `_convert_field_to_tz`) | flag: time-zone support active |
| `storedZone : List Char` | `self.connection.timezone_name` — `django/db/backends/base/base.py:137` | source zone (the database connection's zone) |
| `queryZone : List Char` | `tzname` arg of `_convert_field_to_tz` | target zone (the zone the query is evaluated in) |
| `expr : List Char` | `field_name` arg of `_convert_field_to_tz` | the SQL field expression to wrap |

`self.connection.timezone_name` (base.py:137) is `settings.TIME_ZONE` when
`USE_TZ` is off, `'UTC'` when the connection's `TIME_ZONE` setting is `None`,
else the connection's `TIME_ZONE` setting. Inside `_convert_field_to_tz` the
relevant call only happens under `settings.USE_TZ` (the `active` branch), where
`timezone_name` is the connection zone (`'UTC'` if unset) — exactly what the
gold pre-patch hardcoded as `'UTC'` and the fix replaces with the real
connection zone.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `field_name : str`, `tzname : str`, `timezone_name : str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat (`%`-format) ↔ `List` `++`; string literals ↔ `"…".toList`; `==`/`!=` on zone names ↔ `=`/`≠` on `List Char` |
| `settings.USE_TZ` (truthy bool) | `Bool` | `True ↔ true`, `False ↔ false`; the `and` of `USE_TZ` with the inequality ↔ `active ∧ storedZone ≠ queryZone` |
| `"CONVERT_TZ(%s, '%s', '%s')" % (field_name, storedZone, queryZone)` | `"CONVERT_TZ(".toList ++ expr ++ ", '".toList ++ storedZone ++ "', '".toList ++ queryZone ++ "')".toList` | the `%`-interpolation is concatenation of the literal fragments around the three substituted strings |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation builds a string by concatenation and compares
zone names for equality.

## 3. Callee provenance & multi-site handling

### 3.1 No axioms — fully deep model (band: pure-data)
`buildTzAdjustedExpr` calls NO unchanged callee inside the modeled decision: the
result is computed entirely from the four inputs (`active`, `expr`, `queryZone`,
`storedZone`). The `%`-format and the `settings.USE_TZ` / `timezone_name` reads
are transliterated R/I ops, not delegated behaviour. Hence **`deep_model_references = []`,
`axioms = []`**, and there is **no `axiom_check.py`** (G-AX = skip — the
django__django-14376 no-axiom precedent). The flag dependency is `settings.USE_TZ`
(the `active` parameter) and the equality of the two zone names; both are inputs
exercised directly by G-CONF.

### 3.2 The three additional change sites (shipped, not modeled)
The gold patch.diff also changes the Oracle `_convert_field_to_tz`
(`oracle/operations.py:97`) and the SQLite path
(`sqlite3/base.py` `_sqlite_datetime_parse` + the five `_sqlite_datetime_*`
functions, and `sqlite3/operations.py` `_convert_tznames_to_sql` + four
`datetime_*_sql`). All three implement the **same** conceptual fix — use the
connection's stored zone as the conversion source instead of forcing UTC, and
skip the conversion when the stored zone equals the query zone. They are shipped
verbatim in `patch.diff` (required for G-RESOLVE — the single F2P test
`test_query_convert_timezones` runs on the **SQLite** backend) but are **not**
separately modeled and have **no** `Solution_prepatch_<k>.lean`: they express no
behaviour independent of the modeled MySQL decision (same predicate: convert
from `connection.timezone_name` to `tzname`, identity when equal). See
refinement.md §B. This mirrors the django__django-14376 precedent (a second
shipped-but-unmodeled change site with no independently-observable behaviour).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11138`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `tzAdjustedExpr`/`buildTzAdjustedExpr` (R/I-tagged ops) to Python
and runs the *patched* real MySQL `_convert_field_to_tz` as the oracle (no
A-tagged callee to leave un-substituted — this bundle has none).
