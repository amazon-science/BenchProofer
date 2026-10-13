# mapping.md — django__django-11138

## Instance
- repo: django/django
- base_commit: c84b91b7603e488f7171fdff8f08368ef3d6b856
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change (one behavior, applied at several sites)
The gold patch makes timezone-aware datetime conversion in SQL honor the database
connection's configured time zone instead of always assuming the stored datetimes
are in UTC, and additionally skips the conversion entirely when the connection's
time zone already equals the target time zone. The IDENTICAL logical
transformation is applied at three backend sites:

| backend | function (file @ base_commit) | role |
|---|---|---|
| mysql  | `_convert_field_to_tz` — `django/db/backends/mysql/operations.py:71` | **modeled representative** |
| oracle | `_convert_field_to_tz` — `django/db/backends/oracle/operations.py:~99` | same logic, FROM_TZ form |
| sqlite | `_sqlite_datetime_parse` + `_convert_tznames_to_sql` — `django/db/backends/sqlite3/base.py:398`, `django/db/backends/sqlite3/operations.py:87` | same logic, threaded as extra callback arg |

All three share the decision rule: *use the connection time zone as the source of
the conversion, and convert only when source ≠ target (and TZ support is on)*. I
model the **mysql `_convert_field_to_tz`** site because it is (a) the site the
problem statement explicitly points at, and (b) a pure, total `str → str`
function whose entire observable behavior is the SQL fragment it returns — no I/O,
no live connection object, no `pytz` runtime. The other two sites are the same
predicate over the same two time-zone inputs; refinement.md records them as
identical-logic siblings, and `patch.diff` (gold verbatim) fixes all three so the
harness resolves.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_tzConvertSql` | `DatabaseOperations._convert_field_to_tz` (mysql/operations.py:71) |
| `problem_spec_tzConvertSql`   | the post-condition this function must satisfy |
| `convertTzFragment`           | the `"CONVERT_TZ(%s, '%s', '%s')" % (...)` string builder |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `useTz : Bool` | `settings.USE_TZ` (bool) | `true ↔ True` |
| `connTz : String` | `self.connection.timezone_name` (str) | name of the connection's time zone; never `None` at this call site (the `timezone_name` cached property returns `'UTC'` or a real name) |
| `tzname : String` | `tzname` (str) | the target time zone the caller wants the value in |
| `fieldName : String` | `field_name` (str) | the SQL expression for the column |
| result `: String` | return value (str) | the SQL expression after optional wrapping |

`String` ↔ Python `str` is the identity bijection (byte-for-byte). `!=` on Lean
`String` ↔ Python `!=` on `str`.

## Callee provenance / flag deps
- No unchanged repo callee is consumed. `settings.USE_TZ` and
  `self.connection.timezone_name` are read as plain data (mapped to the `Bool` /
  `String` inputs above); the only operation performed is Python `%`-formatting,
  which is modeled directly as Lean string concatenation (an **I** op). Hence the
  `axioms` region is empty and `axiom_check.py` is a skip stub.
- Flag dependency: the wrapping is gated on `settings.USE_TZ` (the `useTz` input).
  G-CONF fuzzes `useTz ∈ {True, False}`.

## G-CONF fuzz seed
- pinned seed: `11138`
- ≥10^5 fuzzed `(useTz, connTz, tzname, fieldName)` tuples; time-zone strings drawn
  from a pool that includes equal/unequal pairs and `'UTC'`, plus random strings.
