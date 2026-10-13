# mapping.md — django__django-14170

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6efc35b4fe3009666e56a60af0675d7d532bf4ff`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of each axiom.

Repo files under change:
- `django/db/backends/base/operations.py` (the two bound-computing helpers)
- `django/db/models/lookups.py` (the dispatcher that forwards the ISO flag)

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `yearBoundsDate (value isoYear)` | `BaseDatabaseOperations.year_lookup_bounds_for_date_field` — `django/db/backends/base/operations.py:529` | modeled changed function: lower/upper day bounds for a year-valued lookup on a date column |
| `yearBoundsDatetime (value isoYear)` | `BaseDatabaseOperations.year_lookup_bounds_for_datetime_field` — `django/db/backends/base/operations.py:543` | modeled changed function: lower/upper instant bounds on a datetime column |
| `yearLookupBounds (isDateTimeField isoYear value)` | `YearLookup.year_lookup_bounds` — `django/db/models/lookups.py:541` | modeled changed function: dispatch by column type and forward the ISO flag |
| `gregJan1` *(axiom — A-reference)* | `datetime.date(value, 1, 1)` — `operations.py:537` (post-patch `else` branch) | first day of calendar year |
| `gregDec31` *(axiom — A-reference)* | `datetime.date(value, 12, 31)` — `operations.py:538` | last day of calendar year |
| `isoFirst` *(axiom — A-reference)* | `datetime.date.fromisocalendar(value, 1, 1)` — `operations.py:532` (post-patch `iso_year` branch) | first day of ISO week-numbering year |
| `dtJan1` *(axiom — A-reference)* | `datetime.datetime(value, 1, 1)` — `operations.py:557` | first instant of calendar year |
| `dtDec31` *(axiom — A-reference)* | `datetime.datetime(value, 12, 31, 23, 59, 59, 999999)` — `operations.py:558` | last instant of calendar year |
| `dtIsoFirst` *(axiom — A-reference)* | `datetime.datetime.fromisocalendar(value, 1, 1)` — `operations.py:551` | first instant of ISO week-numbering year |

The `iso_year` boolean that drives the new branch is produced at the dispatcher
(`lookups.py:543`, `iso_year = isinstance(self.lhs, ExtractIsoYear)`) and threaded
as the `iso_year=` keyword into both bound helpers (`lookups.py:545,549`
post-patch). `isDateTimeField` is `isinstance(output_field, DateTimeField)`
(`lookups.py:546`). The downstream tail of each helper — `adapt_datefield_value`
/ `adapt_datetimefield_value` (`str(value)`), and the `USE_TZ` `make_aware`
wrapping — is **unchanged** by the patch and lies outside the modeled region
(identity on the order-preserving carrier; see §2).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a `datetime.date` | `Int` (proleptic-Gregorian day **ordinal**) | `d` ↔ `d.toordinal()`; strictly order-preserving, so `BETWEEN` semantics are exact. `d - timedelta(days=1)` ↔ ordinal `- 1`. |
| a `datetime.datetime` (naive) | `Int` (integer **microsecond** instant since `datetime(1,1,1)`) | `t` ↔ `(t - datetime.min) // timedelta(microseconds=1)`; strictly order-preserving. `t - timedelta(microseconds=1)` ↔ instant `- 1`. |
| the looked-up year `value` (a Python `int`) | `Int` | identity |
| `iso_year` / `isinstance(output_field, DateTimeField)` (Python `bool`) | `Bool` | identity |
| the returned `[first, second]` two-element list | `List Int` (`[lower, upper]`) | element-wise via the date/datetime bijection above |
| `adapt_datefield_value` / `adapt_datetimefield_value` (`str(value)`) | identity (omitted) | the adapter is a lossless, order-preserving string rendering of the same date/datetime; it does not alter which rows the bound matches and is unchanged by the patch |
| `make_aware(…, tz)` under `USE_TZ` | identity (omitted) | tz attachment is unchanged by the patch and applied identically to both bounds; it does not change the modeled selection/arithmetic |

Both notions of "year" (calendar vs ISO-8601 week-numbering) name a contiguous
day range; the only behaviour the patch changes is **which landmarks** delimit
that range and the **`value + 1` then minus-one-unit** computation of the ISO
upper bound. The carrier `Int` makes the minus-one-unit step exact in both day
and microsecond space (see §3).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

All six landmark symbols are **A-reference**: opaque (uninterpreted) Lean
functions whose *documented meaning* is the corresponding unchanged
`datetime`-library landmark. The proof consumes no equational axiom about them;
the postconditions hold structurally (the impl returns the very expression the
spec names). G-AX validates that this documented meaning matches the real callee
**and** that the patch's minus-one-unit arithmetic refines to the Lean `- 1`:

- `gregJan1 y`   == `datetime.date(y, 1, 1).toordinal()`
- `gregDec31 y`  == `datetime.date(y, 12, 31).toordinal()`
- `isoFirst y`   == `datetime.date.fromisocalendar(y, 1, 1).toordinal()`
- `dtJan1 y`     == microsecond-instant of `datetime.datetime(y, 1, 1)`
- `dtDec31 y`    == microsecond-instant of `datetime.datetime(y, 12, 31, 23, 59, 59, 999999)`
- `dtIsoFirst y` == microsecond-instant of `datetime.datetime.fromisocalendar(y, 1, 1)`

and the two refinement identities the patch relies on:

- (date)     `datetime.date.fromisocalendar(y + 1, 1, 1) - timedelta(days=1)`
             ↔ `isoFirst (y + 1) - 1` in ordinal space.
- (datetime) `datetime.datetime.fromisocalendar(y + 1, 1, 1) - timedelta(microseconds=1)`
             ↔ `dtIsoFirst (y + 1) - 1` in microsecond space.

These are the *unchanged* stdlib `datetime` constructors — the patch only selects
between them and subtracts one unit; it never reshapes them. `axiom_check.py`
imports only the stdlib `datetime`, over boundary years (ISO-long years 2004,
2009, 2015, 2020, 2026; ordinary years; min/max supported years) plus randomized
fuzz. Exit 0 iff every identity holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`14170`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl region (the branch selection, the `value + 1` offset, the minus-one-unit
upper bound, the `[lower, upper]` assembly) to Python over the ordinal /
microsecond carrier, leaving the A-tagged landmark callees as the real
`datetime` constructors. The oracle is `patch.diff`'s behaviour: the patched
`year_lookup_bounds_for_date_field` / `_datetime_field` first/second computation
(the modeled region), mapped to the same carrier. They must agree on every fuzzed
`(value, iso_year, is_datetime)`.
