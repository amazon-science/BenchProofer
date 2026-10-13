# mapping.md — django__django-11138

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c84b91b7603e488f7171fdff8f08368ef3d6b856`, states the type
abstraction, and gives the provenance of each axiom / deep-model reference.

Repo files under change (one issue, parallel hunks across backends):
`django/db/backends/sqlite3/base.py`, `django/db/backends/sqlite3/operations.py`,
`django/db/backends/mysql/operations.py`, `django/db/backends/oracle/operations.py`.

The official SWE-Bench harness for this Django version runs on the **SQLite**
backend (`DATABASES.default.ENGINE = sqlite3`), so the single FAIL_TO_PASS test
`test_query_convert_timezones (timezones.tests.NewDatabaseTests)` exercises the
SQLite read path — the in-process Python callback `_sqlite_datetime_parse`
(`sqlite3/base.py`). That is the behaviour the model pins. The MySQL/Oracle and
the SQLite SQL-builder hunks are the same abstract behaviour expressed as SQL
strings; they share the discriminator (convert from the connection time zone,
not from UTC) and are covered in refinement.md, but are never *executed* by the
harness, so the load-bearing differential model is the SQLite arithmetic.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `local_walltime(stored, conn_off, target_off, has_target, use_tz)` | `_sqlite_datetime_parse(dt, tzname, conn_tzname)` — `django/db/backends/sqlite3/base.py:401` (post-patch signature) | the modeled changed function: read-side time-zone normalisation of a stored naive datetime |
| `result wall-clock minutes` (`Result()`) | the wall-clock fields of the returned `datetime` (`dt`) that `.date()/.time()/getattr(dt, lookup_type)` read in `_sqlite_datetime_cast_date/_time/_extract/_trunc` | the observable the F2P date lookup compares |
| `conn_off` (param) | UTC offset (minutes) of `pytz.timezone(conn_tzname)`; `conn_tzname == connection.timezone_name` | the database connection time zone the stored wall-clock is expressed in |
| `target_off` (param) | UTC offset (minutes) of `pytz.timezone(tzname)`; `tzname == current active time zone` | the time zone the lookup converts the value into |
| `has_target` (param) | `tzname is not None` | whether a target-time-zone conversion is requested |
| `use_tz` (param) | `settings.USE_TZ` | whether time-zone normalisation is active at all |

`connection.timezone_name` provenance (the new source time zone): defined in
`django/db/backends/base/base.py:137` as a `cached_property` returning
`settings_dict['TIME_ZONE']` when set (else `'UTC'` / `settings.TIME_ZONE`).
The write path `adapt_datetimefield_value` (`sqlite3/operations.py:208`) stores
the value as `make_naive(value, self.connection.timezone)`, i.e. the **wall
clock in the connection time zone** — so a faithful read must reinterpret the
stored wall clock in that same connection time zone before converting to the
active one. This round-trip consistency is the whole point of the fix.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a naive `datetime` (year…second, µs) viewed as an instant on a fixed numbering line | `int` `stored` = wall-clock instant in **minutes** | the lookup only observes a calendar component (date/time/extract) of the resulting wall clock; minute-granular integer arithmetic preserves every component the F2P test reads (dates differ by whole hours here). `dt.date()` etc. are monotone functions of this instant. |
| `pytz.timezone(name)` UTC offset | `int` offset in minutes | `conn_off` = the offset `dt.replace(tzinfo=pytz.timezone(conn))` attaches (for a pytz zone this is its base/LMT offset, e.g. Asia/Bangkok → +402, not +420 — an artefact of `replace` vs `localize` that the real gold code inherits); `target_off` = the offset `dt.astimezone(pytz.timezone(target))` yields for the instant (e.g. Africa/Nairobi → +180). The model abstracts over **the actual offsets the real operations use**; axiom_check.py extracts them from the live datetime objects (no idealisation), so the integer arithmetic is exact on every observed wall-clock component. The only operation is the fixed offset add/subtract these two calls perform. |
| `dt.replace(tzinfo=pytz.timezone(conn))` (relabel, no shift) | reinterpret `stored` as a wall clock in `conn_off`: absolute = `stored - conn_off` | `replace(tzinfo=...)` keeps the wall-clock numbers and changes only the labelled zone — so the absolute instant moves by `-conn_off`. |
| `timezone.localtime(dt, pytz.timezone(target))` (= `dt.astimezone(target)`) | wall clock in target = `absolute + target_off` | `astimezone` keeps the absolute instant and re-expresses the wall clock in the target zone. |
| `dt is None` short-circuit (parse failure) | not modeled — `local_walltime` is the non-None branch; the `dt is None: return None` guard is identical pre/post-patch (refinement I) and the F2P value parses successfully | the only line the patch changes is the tz logic after a successful parse. |

Under `USE_TZ` the offsets are the real `pytz` offsets; under `not USE_TZ` no
conversion occurs (`use_tz = False` ⇒ identity), mirroring the SQL builder’s
`NULL, NULL` and `_sqlite_datetime_parse`’s `conn_tzname`/`tzname` both being
`None`.

## 3. Callee provenance

There is **no consumed `@ContractOnly` axiom** in this bundle. The changed
operation — the time-zone normalisation — is modeled **deeply** as integer
wall-clock arithmetic (`local_walltime`), spelled out in the impl. The two
stdlib/Django helpers it stands on are *unchanged identity-style relabel/shift*
operations that the refinement expresses directly as `±offset`:

### 3.1 `dt.replace(tzinfo=...)` and `dt.astimezone(...)` (A-reference, arithmetic)
**Callees:** `datetime.replace` (CPython) and `datetime.astimezone` (via
`django.utils.timezone.localtime`, `django/utils/timezone.py:191`, body
`return value.astimezone(timezone)`). `replace(tzinfo=z)` keeps the wall-clock
fields and relabels the zone (absolute instant shifts by the new zone’s offset);
`astimezone(z)` keeps the absolute instant and re-expresses the wall clock in
`z`. The composition the patch performs — relabel-to-conn then (if target≠conn)
convert-to-target — has net effect on the observed wall clock of
`+(target_off − conn_off)` minutes, i.e. `stored − conn_off + target_off`.
`axiom_check.py` validates this arithmetic against the **real** CPython
`datetime` + `pytz` on boundary and fuzz offsets (incl. the test’s
Nairobi/Bangkok/UTC zones and the day-boundary crossing), exit 0 iff every
observed `.date()`/wall component matches the model. Flag dependency: holds for
fixed-offset zones; the F2P test uses fixed offsets (the model is offset-based,
which is exactly what `pytz`/`astimezone` compute for these inputs).

### 3.2 `connection.timezone_name` (A-reference, value provenance)
The new source-zone value, `django/db/backends/base/base.py:137`. Under
`USE_TZ` with a per-database `TIME_ZONE` it is that name; its offset is
`conn_off`. `axiom_check.py` confirms `pytz.timezone(connection-TIME_ZONE)`’s
offset is the `conn_off` the model subtracts.
