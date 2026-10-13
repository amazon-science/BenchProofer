# mapping.md — django__django-14170

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6efc35b4fe3009666e56a60af0675d7d532bf4ff`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo files under change:
* `django/db/backends/base/operations.py`
* `django/db/models/lookups.py`

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `date_field_year_range(value, week_numbering)` | `BaseDatabaseOperations.year_lookup_bounds_for_date_field(self, value)` — `django/db/backends/base/operations.py:529` | modeled changed function (DateField year-lookup endpoints, DAY carrier); the patch adds the `iso_year` parameter and its ISO branch |
| `datetime_field_year_range(value, week_numbering)` | `BaseDatabaseOperations.year_lookup_bounds_for_datetime_field(self, value)` — `django/db/backends/base/operations.py:543` | modeled changed function (DateTimeField year-lookup endpoints, INSTANT carrier); same change |
| `year_lookup_range(is_datetime_field, lhs_is_week_numbering, year)` | `YearLookup.year_lookup_bounds(self, connection, year)` — `django/db/models/lookups.py:541` | modeled changed function (the dispatch that decides the calendar, routes to the field-kind endpoint computation — each field kind has its own carrier — and forwards the flag) |
| `cal_jan1(year)` *(axiom — A-consumed)* | `datetime.date(value, 1, 1).toordinal()` (CPython stdlib, called at `operations.py:537` post-patch) | unchanged stdlib callee: first day of the calendar year (day carrier) |
| `cal_dec31(year)` *(axiom — A-consumed)* | `datetime.date(value, 12, 31).toordinal()` (CPython stdlib, called at `operations.py:538` post-patch) | unchanged stdlib callee: last day of the calendar year (day carrier) |
| `iso_jan1(year)` *(axiom — A-consumed)* | `datetime.date.fromisocalendar(value, 1, 1).toordinal()` (CPython stdlib, called at `operations.py` post-patch ISO branch) | unchanged stdlib callee: first day of the ISO week-numbering year (day carrier) |
| `dt_jan1(year)` *(axiom — A-consumed)* | microsecond instant of `datetime.datetime(value, 1, 1)` (CPython stdlib, called at `operations.py:557` post-patch `else` branch) | unchanged stdlib callee: first instant of the calendar year (instant carrier) |
| `dt_dec31(year)` *(axiom — A-consumed)* | microsecond instant of `datetime.datetime(value, 12, 31, 23, 59, 59, 999999)` (`operations.py:558` post-patch) | unchanged stdlib callee: last instant of the calendar year (instant carrier) |
| `dt_iso_jan1(year)` *(axiom — A-consumed)* | microsecond instant of `datetime.datetime.fromisocalendar(value, 1, 1)` (`operations.py:551` post-patch ISO branch) | unchanged stdlib callee: first instant of the ISO week-numbering year (instant carrier) |
| `date_lower/date_upper(value, wk)` | the `if iso_year: … else: …` endpoint selection in the patched date-field method | pure spec: the DAY endpoint chosen by the calendar the lookup uses |
| `dt_lower/dt_upper(value, wk)` | the `if iso_year: … else: …` endpoint selection in the patched datetime-field method | pure spec: the INSTANT endpoint chosen by the calendar the lookup uses |
| `lookup_lower/lookup_upper(is_dt, value, wk)` | the whole dispatch+endpoint pipeline of `YearLookup.year_lookup_bounds` | pure spec: the endpoint the lookup as a whole must produce — the field kind selects the carrier, the flag the calendar |

The decision being modeled by `year_lookup_range`'s `lhs_is_week_numbering`
parameter is the patch's `iso_year = isinstance(self.lhs, ExtractIsoYear)`
(`django/db/models/lookups.py` post-patch).  `ExtractIsoYear`
(`django/db/models/functions/datetime.py:93`, `lookup_name = 'iso_year'`)
registers the same `YearExact/YearGt/YearGte/YearLt/YearLte` lookups as
`ExtractYear` (`functions/datetime.py:167-171`), so the only thing that
distinguishes an `__iso_year` filter from a `__year` filter inside the shared
`YearLookup` optimisation is the runtime type of `self.lhs`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `datetime.date` endpoint | `int` day-ordinal | `d` ↔ `d.toordinal()`; strictly order-preserving, so `BETWEEN` semantics are exact.  The patch's `- datetime.timedelta(days=1)` upper-endpoint subtraction ↔ `- 1` on the next-year first-day ordinal (§3.4) |
| a naive `datetime.datetime` endpoint | `int` microsecond instant since `datetime.min` | `t` ↔ `(t - datetime(1,1,1)) // timedelta(microseconds=1)`; strictly order-preserving.  The patch's `- datetime.timedelta(microseconds=1)` subtraction ↔ `- 1` on the next-ISO-year first-instant (§3.4) |
| the `iso_year` boolean kwarg (`year_lookup_bounds_for_*_field(value, iso_year=False)`) | `week_numbering: bool` positional parameter | identity on the boolean; kwargs modeled as explicit positional params (SPEC_GUIDE §2) |
| `output_field` being a `DateTimeField` vs. not (`lookups.py:543`) | `is_datetime_field: bool` | identity on the boolean; routes to the datetime- vs. date-endpoint computation, i.e. selects the CARRIER (instants vs. days) |
| `isinstance(self.lhs, ExtractIsoYear)` (`lookups.py` post-patch) | `lhs_is_week_numbering: bool` | identity on the boolean: True iff the extracted year is the ISO week-numbering year |
| the returned two-element `[first, second]` list | `List[int]` of two ordinals/instants | element-wise: `Result()[0]` ↔ `first`, `Result()[1]` ↔ `second`, each via its field kind's carrier bijection |
| `self.adapt_datefield_value` / `self.adapt_datetimefield_value` / TZ handling (`operations.py:539-540/553-558`) | identity (omitted) | these adapt the endpoint objects for the driver and (for datetime) apply the connection timezone; they are applied identically to BOTH branches, are unchanged by the patch, and are lossless order-preserving renderings of the same date/datetime — they do not change which day/instant each endpoint denotes.  Modeled as the identity on the carrier. |

The two field kinds deliberately live in **different carriers**: a date column
is bounded by whole days, a datetime column by microsecond instants.  The
datetime endpoints genuinely carry sub-day content (`23:59:59.999999` for the
calendar upper bound, `fromisocalendar(value+1,1,1) - 1µs` for the ISO upper
bound), so collapsing them to day-ordinals would equate the two field kinds'
bounds and admit implementations that route a datetime lookup through the
date-field endpoints (returning whole-day bounds that drop the final day's
interior instants).  The two-carrier model keeps that behaviour observable:
`dt_*` and `cal_*/iso_*` are distinct uninterpreted axiom families, and the
dispatch postcondition (`lookup_lower/lookup_upper`) demands the carrier that
matches the field kind.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All six axioms are unchanged stdlib date/datetime constructors the patched
code calls.  Each is the WEAKEST contract the proof consumes — `model.py`
only pins the returned endpoints to these constructor applications; the
membership *meaning* of each constructor (that its interval is exactly one
year under its calendar in its carrier) is documented here and validated
executably by `axiom_check.py` against the real standard library.  No axiom
is stronger than the real callee.

### 3.1 `cal_jan1` / `cal_dec31` ↔ `datetime.date`
**Callee:** `datetime.date(year, m, d).toordinal()` (CPython, every supported
3.x).  `cal_jan1(year) = date(year,1,1).toordinal()` is the smallest ordinal of
calendar year `year`; `cal_dec31(year) = date(year,12,31).toordinal()` the
largest.  Hence the closed ordinal interval `[cal_jan1(year), cal_dec31(year)]`
is exactly the set of days whose proleptic-Gregorian year is `year`.  This is
the pre-existing (`__year`) behaviour the patch leaves unchanged in the
`else` branch.  Docs: https://docs.python.org/3/library/datetime.html#datetime.date.

### 3.2 `iso_jan1` ↔ `datetime.date.fromisocalendar`
**Callee:** `datetime.date.fromisocalendar(year, week, weekday).toordinal()`
(CPython ≥ 3.8 — the gold patch itself calls it, so the eval interpreter for
Django 4.0 provides it).  `iso_jan1(year) = fromisocalendar(year,1,1).toordinal()`
is the first day (Monday of week 1) of ISO week-numbering year `year`, the
smallest ordinal whose `isocalendar()[0]` equals `year`.  The next ISO year
begins at `iso_jan1(year+1)`, so the closed interval
`[iso_jan1(year), iso_jan1(year+1) - 1]` is exactly the set of days whose ISO
year is `year`.  Docs:
https://docs.python.org/3/library/datetime.html#datetime.date.fromisocalendar
and `.isocalendar()`.

### 3.3 `dt_jan1` / `dt_dec31` / `dt_iso_jan1` ↔ `datetime.datetime`
**Callee:** `datetime.datetime(year, …)` and
`datetime.datetime.fromisocalendar(year, week, weekday)` (CPython ≥ 3.8),
projected onto the microsecond-instant carrier
`t ↦ (t - datetime(1,1,1)) // timedelta(microseconds=1)`.
`dt_jan1(year)` is the instant of `datetime(year,1,1)` — the smallest instant
of calendar year `year`; `dt_dec31(year)` the instant of
`datetime(year,12,31,23,59,59,999999)` — the largest
(`dt_dec31(year) + 1 == dt_jan1(year+1)`), so
`[dt_jan1(year), dt_dec31(year)]` is exactly calendar year `year` in instant
space.  `dt_iso_jan1(year)` is the instant of
`datetime.fromisocalendar(year,1,1)` — the smallest instant whose ISO year is
`year`; `[dt_iso_jan1(year), dt_iso_jan1(year+1) - 1]` is exactly ISO year
`year` in instant space.  Each `dt_*` landmark's instant lies on the very day
its day-carrier counterpart names (validated by G-AX's cross-carrier check).

### 3.4 The upper-endpoint subtraction
The patch computes the ISO upper endpoint as
`datetime.date.fromisocalendar(value+1, 1, 1) - datetime.timedelta(days=1)`
(date field) and
`datetime.datetime.fromisocalendar(value+1, 1, 1) - datetime.timedelta(microseconds=1)`
(datetime field).  Under the carrier bijections both denote the last
day/instant of ISO year `value`: `iso_jan1(value+1) - 1` =
`date_upper(value, True)` in ordinal space, and `dt_iso_jan1(value+1) - 1` =
`dt_upper(value, True)` in microsecond space.

**Soundness check (G-AX):** `axiom_check.py` runs the real `datetime.date` /
`datetime.datetime` / their `.fromisocalendar` / `fromordinal().year` /
`.isocalendar()[0]` over 15 named years (including the F2P years 2014/2015,
year 1, leap years, and years whose ISO week 1 starts in the prior December)
plus 2000 random years, and asserts for each that: the calendar interval is
exactly the calendar year and the ISO interval exactly the ISO year in the DAY
carrier (full per-day sweep with a margin on both sides); the same in the
INSTANT carrier (endpoint years + `dt_dec31(y)+1 == dt_jan1(y+1)` exactness +
the `-1µs` identity replayed on the real callee); the two calendars genuinely
differ (so the calendar choice is observable); and the two carriers are
consistent (each instant landmark lies on its day-carrier day) yet distinct
(no numeral collision, so field-kind routing is observable).  It then replays
the FAIL_TO_PASS boundary days (2014-12-27 → ISO 2014, 2014-12-31 → ISO 2015,
2015-12-31 → ISO 2015) in BOTH carriers and asserts the ISO bounds select
exactly the right rows for `iso_year=2015` and `iso_year__lte=2014`, while the
buggy calendar bounds do not.  Imports only the stdlib `datetime`.  Exit 0 iff
sound.
