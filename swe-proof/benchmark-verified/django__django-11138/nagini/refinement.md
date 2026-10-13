# refinement.md — django__django-11138

The operation-by-operation correspondence between `model.py`'s implementation
(`local_walltime` + the deep `normalised_walltime` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (proof
uses an axiom's `Ensures`), **A-reference** (a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
No step is a *changed operation Nagini cannot express* (kind-3): the one
operation that changed — the time-zone normalisation — is modelled **deeply** as
integer wall-clock arithmetic.

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`,
confirmed; it is the real correctness oracle, G-RESOLVE).

The claim: *any implementation that verifies against this frozen spec, refined
per the map below, computes the connection-sourced time-zone normalisation the
gold patch computes on the tested inputs, so it resolves.*

## 0. Which hunk the harness executes

The SWE-Bench Django environment runs on **SQLite**. The single FAIL_TO_PASS
test `test_query_convert_timezones (timezones.tests.NewDatabaseTests)` therefore
drives the SQLite read path — the in-process callback `_sqlite_datetime_parse`
(`sqlite3/base.py`) — and the SQLite SQL builder that supplies its third
argument. The MySQL and Oracle hunks (§B) are the *same abstract behaviour*
emitted as SQL strings for engines the harness does not run; they are part of
the faithful gold patch and are documented here, but the load-bearing
differential model is the SQLite arithmetic (§A).

## A. The SQLite read path — `_sqlite_datetime_parse` (`sqlite3/base.py:401`)

Gold hunk (the discriminator):
```
-def _sqlite_datetime_parse(dt, tzname=None):
+def _sqlite_datetime_parse(dt, tzname=None, conn_tzname=None):
     ...
-    if tzname is not None:
+    if conn_tzname:
+        dt = dt.replace(tzinfo=pytz.timezone(conn_tzname))
+    if tzname is not None and tzname != conn_tzname:
         dt = timezone.localtime(dt, pytz.timezone(tzname))
     return dt
```
(plus the four `_sqlite_datetime_*` callbacks gaining a `conn_tzname` argument
they forward unchanged, and `get_new_connection` registering them with arity
+1; these are pure plumbing — tag **I/R** below.)

| # | model.py impl op (`local_walltime`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `stored:int`, `conn_off:int`, `target_off:int`, `has_target:bool`, `use_tz:bool` | `dt`, `conn_tzname`, `tzname`, `settings.USE_TZ` | R | a naive `datetime` ↔ integer wall-clock minutes; a `pytz` zone ↔ its integer UTC offset; `tzname is not None` ↔ `has_target`; `settings.USE_TZ` ↔ `use_tz` (mapping.md §2). |
| A2 | `result = stored` (start) | `dt = typecast_timestamp(dt)` (naive wall clock, tz=UTC) | R | the successful-parse branch; the `dt is None: return None` guard above it is byte-identical pre/post-patch and excluded from the modelled branch (mapping.md §2). |
| A3 | `if use_tz:` then `result = result - conn_off` | `if conn_tzname: dt = dt.replace(tzinfo=pytz.timezone(conn_tzname))` | A-reference | relabelling the stored wall clock to the **connection** zone moves the underlying instant by `-conn_off`. Modelled deeply as `-conn_off`; validated `== dt.replace(...)` using the **actual** offset that `replace` attaches (pytz base/LMT), G-AX §3.1. Under `USE_TZ`, `conn_tzname` is always truthy (`timezone_name` is `'UTC'`/the configured name, never empty — mapping.md §1), matching the `if use_tz:` guard. |
| A4 | `if has_target and target_off != conn_off: result = result + target_off` | `if tzname is not None and tzname != conn_tzname: dt = timezone.localtime(dt, pytz.timezone(tzname))` | A-reference | `localtime(dt, tz) == dt.astimezone(tz)` re-expresses the instant as a wall clock in the target zone: `+target_off`. The `tzname != conn_tzname` guard ↔ `target_off != conn_off` (distinct zones ⇒ distinct offsets for these inputs); validated by G-AX §3.1 against the actual `astimezone` offset. |
| A5 | `elif has_target: result = result + conn_off` (restore) | (no localtime call: `dt` keeps its connection-zone wall clock) | I | when the target zone equals the connection zone the real code skips `localtime`, leaving the wall clock untouched; the model's relabel-then-restore is the same observed identity (`-conn_off + conn_off`). |
| A6 | `else: result = result + conn_off` (restore) | (the `tzname is None` case: no localtime) | I | no target zone requested ⇒ wall clock returned untouched; relabel restored to identity. (Reachable only with `use_tz` true here; under the precondition `use_tz or not has_target`.) |
| A7 | `return result` | `return dt` | R | the returned wall clock the `.date()/.time()/getattr` lookups read ↔ `Result()` minutes (mapping.md §1). |

The discriminating content — **source zone = the connection zone, not a
hard-wired UTC** — lives in A3 (`- conn_off`). `model_prepatch.py` reverts to the
pre-patch skeleton (no relabel; `result + target_off` only, i.e. source offset
hard-wired to `0`) and **fails** the postcondition
`Result() == normalised_walltime(...)` whenever `conn_off != 0` — exactly the
spec sensing the change (G-DIFF). The second discriminator (skip conversion when
zones coincide) is subsumed: with `conn_off == target_off` the arithmetic
already yields `stored` (A5), so the optimisation is observationally the
identity and needs no separate clause.

## B. The SQL-builder sites (same behaviour, non-executed engines)

These hunks emit the *same* connection-sourced behaviour as SQL strings; the
harness (SQLite) never executes MySQL/Oracle SQL, so they are not differentially
observable, but they are part of the faithful gold patch:

* **SQLite `operations.py`** `_convert_tzname_to_sql` → `_convert_tznames_to_sql`
  now returns **both** `('target', 'conn')` quoted names (or `NULL, NULL` when
  `not USE_TZ`), threaded into the `django_datetime_*` SQL as the new third/
  fourth argument that becomes `_sqlite_datetime_parse`'s `conn_tzname`. **R/I**:
  this is the value-provenance plumbing of `conn_off`/`has_target`/`use_tz` into
  §A (the connection-zone name = `self.connection.timezone_name`, mapping.md §1).
* **MySQL `_convert_field_to_tz`** : `'UTC'` → `self.connection.timezone_name`
  as the `CONVERT_TZ` source, guarded by `and self.connection.timezone_name !=
  tzname` (skip when equal). **A-reference/I**: identical abstract behaviour to
  §A (source = connection zone; identity when source == target). Same `conn_off`
  vs hard-wired-UTC discriminator.
* **Oracle `_convert_field_to_tz`** : `FROM_TZ(%s, '0:00')` → `FROM_TZ(%s,
  '<conn>')`, returning `field_name` unchanged when `timezone_name == tzname`.
  **A-reference/I**: same abstract behaviour as §A.

All three are the SQL face of the §A arithmetic; the SQLite `_sqlite_datetime_
parse` model is their common, executed differential witness.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The single operation that genuinely
*changed* — sourcing the conversion from the connection time zone (and skipping
it when source == target) — is modelled **deeply** (the integer offset
arithmetic `normalised_walltime`, consumed by `local_walltime`, steps A3–A6),
not hidden behind an axiom about the function under change. There is **no
consumed `@ContractOnly` axiom**: the relabel/convert helpers (`datetime.replace`,
`datetime.astimezone` via `timezone.localtime`) are unchanged ±offset operations
expressed directly, and validated == reality by axiom_check.py (A-reference,
G-AX §3.1).

## D. verify(model) ⇒ resolved

`local_walltime` verifies only if its result equals the connection-sourced
normalisation `stored - conn_off + target_off` (A3–A4) — source = the connection
offset, never a hard-wired zero. By R (datetime ↔ minutes, pytz zone ↔ offset)
and G-AX (the deep model == the real `replace`/`astimezone` over F2P instants +
boundary + 20000 fuzz, using the actual pytz offsets), the verified arithmetic
equals what the gold `_sqlite_datetime_parse` computes on the tested input;
hence the `.date()` the F2P lookup reads is 2016-01-01 (gold) rather than the
UTC-sourced pre-patch's 2016-01-02. The MySQL/Oracle/SQLite-builder hunks (§B)
are the same behaviour for engines the harness does not run. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited references — and the gold patch resolves (G-RESOLVE). The
trust points are exactly the two of PLAN §1.1: A-reference soundness (G-AX) and
refinement fidelity (this document, G-EQ).
