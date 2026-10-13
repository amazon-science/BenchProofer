# refinement.md — django__django-14170

Operation correspondence between the two `implementation_*` skeletons and the
gold `patch.diff`. Tags: **R** (type refinement; bijection stated),
**A-consumed** (proof uses a declared axiom's property), **A-reference** (deep
model validated == real callee by G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The only behavior the patch introduces — the
`iso_year=True` branch selecting ISO-8601 week-numbering bounds instead of
calendar bounds — is modeled DEEPLY (the `isoYearStart` / `gregJan1` / `gregDec31`
arithmetic spelled out in `pure`), so the two calendar callees are
**A-reference**s validated against the real stdlib `datetime` by G-CONF, never
axiomatized. Every row below is **R**, **A-reference**, or **I**. The R/I/A-ref
legs are differential-tested by G-CONF; G-AX is a skip stub (no consumed axiom).

The gold patch edits three sites:
1. `year_lookup_bounds_for_date_field(value, iso_year=False)` — adds the ISO branch.
2. `year_lookup_bounds_for_datetime_field(value, iso_year=False)` — adds the ISO branch.
3. `YearLookup.year_lookup_bounds(connection, year)` — computes
   `iso_year = isinstance(self.lhs, ExtractIsoYear)` and threads it into (1)/(2).

Sites (1) and (2) are the two modeled triples. Site (3) is the caller that
produces the `isoYear : Bool` input and dispatches on column type; modeling
Django's expression/lookup class hierarchy is out of scope, so the flag is taken
as an input and site (3) is carried verbatim by `patch.diff` as **R** glue.

## `implementation_yearBoundsDate` ↔ `year_lookup_bounds_for_date_field`

Post-patch source:
```python
if iso_year:
    first = datetime.date.fromisocalendar(value, 1, 1)
    second = datetime.date.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(days=1)
else:
    first = datetime.date(value, 1, 1)
    second = datetime.date(value, 12, 31)
first = self.adapt_datefield_value(first)     # = str(first)
second = self.adapt_datefield_value(second)   # = str(second)
return [first, second]
```

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `if isoYear then …` branch selector | `if iso_year:` | I | identical boolean branch on the input flag |
| `first := isoYearStart value` | `first = datetime.date.fromisocalendar(value, 1, 1)` | A-reference | ISO week-1 Monday modeled deeply as `gregJan1 y + 3` rounded back to Monday; validated == `fromisocalendar` by G-CONF |
| `second := isoYearStart (value+1) - 1` | `datetime.date.fromisocalendar(value+1,1,1) - timedelta(days=1)` | A-reference | day before next ISO year's first day; `- 1` on the ordinal ↦ `- timedelta(days=1)` |
| `first := gregJan1 value` (else) | `first = datetime.date(value, 1, 1)` | A-reference | Gregorian ordinal of Jan 1st; deep day-count model validated == `date.toordinal` by G-CONF |
| `second := gregDec31 value` (else) | `second = datetime.date(value, 12, 31)` | A-reference | `gregDec31 y = gregJan1 (y+1) - 1` = ordinal of Dec 31st |
| `return (first, second)` | `first = adapt_…(first); second = adapt_…(second); return [first, second]` | R | bound objects ↦ ordinals; `adapt_datefield_value = str` is an injective per-bound serialization applied identically in both branches (R glue, recovered via `date.fromordinal` in G-CONF) |

## `implementation_yearBoundsDatetime` ↔ `year_lookup_bounds_for_datetime_field`

Post-patch source (the `USE_TZ=False` path; `USE_TZ=True` adds `make_aware`):
```python
if iso_year:
    first = datetime.datetime.fromisocalendar(value, 1, 1)
    second = datetime.datetime.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(microseconds=1)
else:
    first = datetime.datetime(value, 1, 1)
    second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)
# (if settings.USE_TZ: make_aware both)
first = self.adapt_datetimefield_value(first)
second = self.adapt_datetimefield_value(second)
return [first, second]
```

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `if isoYear then …` | `if iso_year:` | I | identical branch |
| `first := isoYearStart value * usPerDay` | `datetime.datetime.fromisocalendar(value,1,1)` | A-reference | midnight of ISO year's first day; ordinal * 86400000000 µs |
| `second := isoYearStart (value+1) * usPerDay - 1` | `datetime.datetime.fromisocalendar(value+1,1,1) - timedelta(microseconds=1)` | A-reference | one µs before next ISO year's midnight = `23:59:59.999999` of last day |
| `first := gregJan1 value * usPerDay` (else) | `datetime.datetime(value, 1, 1)` | A-reference | midnight Jan 1st in µs |
| `second := gregJan1 (value+1) * usPerDay - 1` (else) | `datetime.datetime(value, 12, 31, 23, 59, 59, 999999)` | A-reference | `(dec31_ordinal+1)*usPerDay - 1` = `gregJan1(value+1)*usPerDay - 1` (last µs of the calendar year) |
| `return (first, second)` | `make_aware`?/`adapt_…`; `return [first, second]` | R | naive bound ↦ µs-since-epoch; `make_aware` (USE_TZ=True) is an order-preserving tz attachment applied identically to both bounds in both branches — does not change the chosen year, so R glue (G-CONF fuzzes the `USE_TZ=False` naive path) |

## Caller (site 3) — `YearLookup.year_lookup_bounds`

| patch.diff op | tag | note |
|---|---|---|
| `iso_year = isinstance(self.lhs, ExtractIsoYear)` | R | produces the `isoYear : Bool` input; class-hierarchy plumbing carried verbatim, not modeled |
| `if isinstance(output_field, DateTimeField): … _for_datetime_field(year, iso_year=iso_year) else: … _for_date_field(year, iso_year=iso_year)` | R | column-type dispatch selects which modeled triple applies; the threaded `iso_year` kwarg is the input bridge |

## G-DIFF correspondence

- `Solution_prepatch.lean`: `implementation_yearBoundsDate` ignores `isoYear`
  (always calendar bounds) ⇒ violates the `isoYear = true` clause of
  `problem_spec_yearBoundsDate` ⇒ `correct_yearBoundsDate` unprovable. This is
  the real pre-patch bug for date columns.
- `Solution_prepatch_2.lean`: same for `implementation_yearBoundsDatetime` ⇒
  `correct_yearBoundsDatetime` unprovable. The real pre-patch bug for timestamp
  columns. (The F2P test exercises a `DateTimeField`, matching variant 2.)
