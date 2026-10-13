# refinement.md — django__django-14170

Maps every operation in `Solution.lean`'s `impl` regions to its `patch.diff`
counterpart. Tags: **R** (type refinement; bijection in mapping.md §2),
**A-reference** (deep/opaque model validated == real callee by G-AX),
**A-consumed** (proof consumes an axiom's `ensures` — none here), **I**
(identical concrete op). Every step is R, A, or I. There is no kind-3 (a changed
op Velvet cannot express).

The three modeled functions correspond to the three patch hunks:
`year_lookup_bounds_for_date_field` (date helper),
`year_lookup_bounds_for_datetime_field` (datetime helper), and
`YearLookup.year_lookup_bounds` (dispatcher).

## `yearBoundsDate` ↔ `year_lookup_bounds_for_date_field`

| # | Solution.lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if isoYear then …` | `if iso_year:` | I | the new branch selector the patch introduces; `isoYear : Bool` ↔ `iso_year` bool (mapping §2) |
| 2 | `isoFirst value` | `datetime.date.fromisocalendar(value, 1, 1)` | A-reference | first day of ISO year; ordinal carrier (mapping §3) |
| 3 | `isoFirst (value + 1) - 1` | `datetime.date.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(days=1)` | A-reference + R | `value + 1` is integer succ (I); `- timedelta(days=1)` ↔ ordinal `- 1` (R, mapping §3) |
| 4 | `gregJan1 value` | `datetime.date(value, 1, 1)` | A-reference | first day of calendar year (unchanged `else` branch) |
| 5 | `gregDec31 value` | `datetime.date(value, 12, 31)` | A-reference | last day of calendar year (unchanged `else` branch) |
| 6 | `[ … , … ]` | `return [first, second]` | R | two-element list ↔ `List Int` element-wise (mapping §2) |

The patch tail `first = self.adapt_datefield_value(first); second = …` is the
unchanged, order-preserving `str(value)` rendering — identity on the carrier
(mapping §2), outside the modeled region.

## `yearBoundsDatetime` ↔ `year_lookup_bounds_for_datetime_field`

| # | Solution.lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if isoYear then …` | `if iso_year:` | I | same branch selector |
| 2 | `dtIsoFirst value` | `datetime.datetime.fromisocalendar(value, 1, 1)` | A-reference | first instant of ISO year; microsecond carrier (mapping §3) |
| 3 | `dtIsoFirst (value + 1) - 1` | `datetime.datetime.fromisocalendar(value + 1, 1, 1) - datetime.timedelta(microseconds=1)` | A-reference + R | `- timedelta(microseconds=1)` ↔ instant `- 1` (R, mapping §3) |
| 4 | `dtJan1 value` | `datetime.datetime(value, 1, 1)` | A-reference | first instant of calendar year (unchanged `else`) |
| 5 | `dtDec31 value` | `datetime.datetime(value, 12, 31, 23, 59, 59, 999999)` | A-reference | last instant of calendar year (unchanged `else`) |
| 6 | `[ … , … ]` | `return [first, second]` | R | as above |

The patch tail (`USE_TZ` `make_aware`, then `adapt_datetimefield_value`) is
unchanged and applied identically to both bounds — identity on the carrier
(mapping §2), outside the modeled region.

## `yearLookupBounds` ↔ `YearLookup.year_lookup_bounds`

| # | Solution.lean op | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if isDateTimeField then …` | `if isinstance(output_field, DateTimeField):` | I | column-type dispatch (`lookups.py:546`); `isDateTimeField : Bool` ↔ the isinstance result |
| 2 | `yearBoundsDatetime value isoYear` | `connection.ops.year_lookup_bounds_for_datetime_field(year, iso_year=iso_year)` | I (callee-under-spec) | calls the modeled datetime helper; `prove_correct` applies `yearBoundsDatetime_correct` |
| 3 | `yearBoundsDate value isoYear` | `connection.ops.year_lookup_bounds_for_date_field(year, iso_year=iso_year)` | I (callee-under-spec) | calls the modeled date helper; `yearBoundsDate_correct` |
| 4 | (the `isoYear` argument) | `iso_year = isinstance(self.lhs, ExtractIsoYear)` then `iso_year=iso_year` | R | the flag the dispatcher computes and **forwards** — the heart of the fix; bool ↔ bool (mapping §2). Modeled as a free input forwarded unchanged. |

The pre-patch defect: the dispatcher computed no ISO flag and the helpers had no
`iso_year` parameter, so an ISO-year lookup silently used calendar-year bounds.
In `Solution_prepatch.lean` the helper impls ignore `isoYear` and return the
calendar bounds — which violates the `isoYear = true → …` postcondition exactly
when the lookup is an ISO-year lookup (G-DIFF).

## Soundness legs

- **R/I legs** (the branch selection, `value + 1`, the minus-one-unit upper
  bound, the `[lower, upper]` assembly, the type dispatch, the two callee
  invocations) — mechanically refuted by G-CONF (`conformance_check.py`) over the
  ordinal / microsecond carrier vs the patched helper behaviour.
- **A-reference legs** (the six `datetime` landmark callees + the two
  minus-one-unit refinement identities) — validated == the real stdlib
  `datetime` callees by G-AX (`axiom_check.py`).
- **A-consumed:** none. No equational axiom is consumed by the proof; the
  landmarks are opaque and the postconditions are structural.
