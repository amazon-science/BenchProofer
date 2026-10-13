# mapping.md — django__django-14170

## Symbol binding (file:line @ base_commit 6efc35b4fe)

| Lean symbol | Python | location |
|---|---|---|
| `implementation_yearBoundsDate` / `problem_spec_yearBoundsDate` / `correct_yearBoundsDate` | `year_lookup_bounds_for_date_field(self, value, iso_year=False)` | `django/db/backends/base/operations.py:526-541` @ base_commit (gold adds the `iso_year` branch) |
| `implementation_yearBoundsDatetime` / `problem_spec_yearBoundsDatetime` / `correct_yearBoundsDatetime` | `year_lookup_bounds_for_datetime_field(self, value, iso_year=False)` | `django/db/backends/base/operations.py:543-563` @ base_commit (gold adds the `iso_year` branch; the `USE_TZ=False` path) |
| `isoYear : Bool` (input flag of both modeled functions) | `iso_year` parameter; set by the caller as `isinstance(self.lhs, ExtractIsoYear)` | caller `YearLookup.year_lookup_bounds`, `django/db/models/lookups.py:540-555` |
| `gregJan1 value` | proleptic-Gregorian ordinal of `datetime.date(value, 1, 1)` (`= datetime.date(value,1,1).toordinal()`) | stdlib `datetime` |
| `isoYearStart value` | ordinal of `datetime.date.fromisocalendar(value, 1, 1)` (Monday of ISO week 1) | stdlib `datetime` |
| `result.1` / `result.2` (date) | the lower / upper element of the returned two-element list, BEFORE `adapt_datefield_value` (= `str`) | `[first, second]` |
| `result.1` / `result.2` (datetime) | lower / upper bound expressed in microseconds since the proleptic-Gregorian ordinal epoch, BEFORE `make_aware`/`adapt_datetimefield_value` | `[first, second]` |

## What the modeled functions compute

`year_lookup_bounds_for_date_field(value, iso_year)` returns the inclusive
`[lower, upper]` date bounds used by a `BETWEEN`-style range query for a year
lookup on a date column:

- **calendar year** (`iso_year=False`): `lower = date(value,1,1)`,
  `upper = date(value,12,31)`.
- **ISO-8601 week-numbering year** (`iso_year=True`):
  `lower = date.fromisocalendar(value,1,1)` (the Monday starting ISO week 1),
  `upper = date.fromisocalendar(value+1,1,1) - 1 day` (the day before the next
  ISO year starts).

`year_lookup_bounds_for_datetime_field(value, iso_year)` returns the analogous
timestamp bounds: `lower` is midnight of that first day, `upper` is the last
microsecond of that last day (`23:59:59.999999`). In microseconds since the
ordinal epoch: `lower = first_ordinal * 86400000000`,
`upper = next_period_start_ordinal * 86400000000 - 1`.

The bridge to the date model: `date(value,12,31).toordinal() = date(value+1,1,1).toordinal() - 1`,
so `upper` (date) `= gregJan1(value+1) - 1` and `upper` (datetime)
`= gregJan1(value+1) * usPerDay - 1`; the ISO `upper` uses `isoYearStart(value+1)`.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `value : int` (looked-up year) | `value : Int` | identity; the deep calendar models (`gregJan1` / `gregDec31` / `isoYearStart`) are total integer arithmetic, so the `correct_*` obligations are stated for every `value : Int` with no domain side-condition — a conservative total extension of the real callees, which agree with the model wherever they are defined (the stdlib constructors raise outside year 1..9999, resp. 1..9998 for the ISO branch since it evaluates `value+1` as a year; G-CONF differentials cover that defined range) |
| `iso_year : bool` | `isoYear : Bool` | `True ↦ true`, `False ↦ false` |
| date bound `d` (a `datetime.date`) | `Int` ordinal | `d ↦ d.toordinal()`; recovered by `datetime.date.fromordinal` for the differential string comparison |
| datetime bound `dt` (naive `datetime.datetime`, `USE_TZ=False`) | `Int` microseconds | `dt ↦ dt.toordinal_date()*86400000000 + intraday_micros`; recovered by `date.fromordinal` + `timedelta(microseconds=…)` |
| returned `[first, second]` | `result : Int × Int` | `first ↦ result.1`, `second ↦ result.2` |

`adapt_datefield_value` / `adapt_datetimefield_value` on the base backend are
`str(value)` — an injective serialization of the bound object; it is applied
identically in both branches and is **R** refinement glue, not modeled behavior.
The `USE_TZ=True` path wraps each bound with `make_aware` (an order-preserving
tz attachment applied identically to both bounds in both branches); it does not
alter which calendar/ISO bound is chosen, so it too is R glue (mapping the naive
bound to the same instant) and is out of the modeled scope.

## Caller provenance + flag dependency

- `YearLookup.year_lookup_bounds` (caller) dispatches on the output-field type
  (datetime column ⇒ `year_lookup_bounds_for_datetime_field`, else the date
  variant) and computes `iso_year = isinstance(self.lhs, ExtractIsoYear)`. The
  type-dispatch selects which of the two modeled triples applies; the
  `isinstance` test is the source of the `isoYear : Bool` input. Modeling
  Django's lookup/expression class hierarchy is out of scope; the flag is taken
  as an input and the `isinstance` plumbing is carried verbatim by `patch.diff`
  (an **R** leg). G-CONF fuzzes both `isoYear` values against both real callees.
- No consumed callee axiom: `gregJan1` / `isoYearStart` are spelled out as
  arithmetic on `value` (deep **A-reference** models of the stdlib `datetime`
  ordinal/ISO-calendar computations), validated == the real callees by G-CONF.
  `datetime.date.toordinal` / `fromisocalendar` are unchanged stdlib callees.

## G-CONF fuzz seed

`SEED = 20210323` (pinned in `conformance_check.py`).
