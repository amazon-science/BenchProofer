# refinement.md — django__django-14170

The operation-by-operation correspondence between `model.py`'s implementation
(the three contracted functions `date_field_year_range`,
`datetime_field_year_range`, `year_lookup_range`) and `patch.diff` (the gold
patch).  Each step is tagged **R** (type refinement), **A** (axiomatized callee
— **A-consumed** where the proof uses the axiom, **A-reference** where a deep
model is validated == the real callee by G-AX) or **I** (identical concrete
operation).  The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit`, the
real correctness oracle, G-RESOLVE).

This is a multi-site change: three patched functions across two files, modeled
as three contracted functions (per-function marker regions repeat; the axioms
and pure regions are single module-level blocks).  The two endpoint sites live
in DIFFERENT carriers — day ordinals for the date field, microsecond instants
for the datetime field (mapping.md §2) — so each site has its own axiom family
and its own postcondition oracle, and the dispatch's postcondition pins the
carrier to the field kind.

## A. `year_lookup_bounds_for_date_field` (`operations.py:529`)

Gold hunk: the signature gains `iso_year=False`; the single endpoint pair is
replaced by an `if iso_year: …fromisocalendar… else: …date(value,1,1)/(,12,31)`.

| # | model.py impl op (`date_field_year_range`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `value: int`, `week_numbering: bool` | `value` (int year), `iso_year=False` kwarg | R | int year identical; the `iso_year` keyword default modeled as an explicit positional bool (mapping.md §2). |
| A2 | `if week_numbering:` … `else:` | `if iso_year:` … `else:` | I | identical control flow / branch condition (after R on the bool). |
| A3 | `first = iso_jan1(value)` | `first = datetime.date.fromisocalendar(value, 1, 1)` | A-consumed | `iso_jan1` is the axiomatized stdlib callee = ordinal of the ISO year's first day (mapping.md §3.2). The proof pins `Result()[0] == date_lower(value, True) == iso_jan1(value)`. |
| A4 | `second = iso_jan1(value + 1) - 1` | `second = datetime.date.fromisocalendar(value+1,1,1) - datetime.timedelta(days=1)` | A-consumed + R | `iso_jan1(value+1)` is the next ISO year's first-day ordinal (axiom); the `- timedelta(days=1)` ↔ `- 1` on the ordinal (mapping.md §3.4). |
| A5 | `first = cal_jan1(value)` | `first = datetime.date(value, 1, 1)` | A-consumed | `cal_jan1` axiomatized = ordinal of Jan 1 (mapping.md §3.1). |
| A6 | `second = cal_dec31(value)` | `second = datetime.date(value, 12, 31)` | A-consumed | `cal_dec31` axiomatized = ordinal of Dec 31 (mapping.md §3.1). |
| A7 | `return [first, second]` | `first = self.adapt_datefield_value(first); second = self.adapt_datefield_value(second); return [first, second]` | R | `adapt_datefield_value` is applied identically in both branches, is unchanged by the patch, and is a lossless order-preserving rendering of the same day (mapping.md §2); modeled as the identity on the day-ordinal. The two-element list is element-wise identical. |

## B. `year_lookup_bounds_for_datetime_field` (`operations.py:543`)

Gold hunk: the same shape, but over `datetime.datetime`: the calendar upper
endpoint is `…12,31,23,59,59,999999` (the year's final microsecond), the ISO
upper endpoint `datetime.fromisocalendar(value+1,1,1) - timedelta(microseconds=1)`,
plus the unchanged `USE_TZ` make-aware block.

| # | model.py impl op (`datetime_field_year_range`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `value: int`, `week_numbering: bool` | `value` (int year), `iso_year=False` kwarg | R | as A1. |
| B2 | `if week_numbering:` … `else:` | `if iso_year:` … `else:` | I | as A2. |
| B3 | `first = dt_iso_jan1(value)` | `first = datetime.datetime.fromisocalendar(value, 1, 1)` | A-consumed | `dt_iso_jan1` is the axiomatized stdlib callee = microsecond instant of the ISO year's first moment (mapping.md §3.3). The proof pins `Result()[0] == dt_lower(value, True) == dt_iso_jan1(value)`. |
| B4 | `second = dt_iso_jan1(value + 1) - 1` | `second = datetime.datetime.fromisocalendar(value+1,1,1) - datetime.timedelta(microseconds=1)` | A-consumed + R | `dt_iso_jan1(value+1)` is the next ISO year's first instant (axiom); the `- timedelta(microseconds=1)` ↔ `- 1` on the instant (mapping.md §3.4). |
| B5 | `first = dt_jan1(value)` | `first = datetime.datetime(value, 1, 1)` | A-consumed | `dt_jan1` axiomatized = the year's first instant (mapping.md §3.3). |
| B6 | `second = dt_dec31(value)` | `second = datetime.datetime(value, 12, 31, 23, 59, 59, 999999)` | A-consumed | `dt_dec31` axiomatized = the year's last instant; `dt_dec31(value) + 1 == dt_jan1(value+1)` (exactness, G-AX). |
| B7 | `return [first, second]` | the `USE_TZ` make-aware block + `adapt_datetimefield_value`, then `return [first, second]` | R | the TZ make-aware and adapt steps apply identically to both branches, are unchanged by the patch, and preserve the instant each endpoint denotes on the order-preserving carrier (mapping.md §2); modeled as the identity on the instant. |

The datetime site is NOT collapsed onto the date site: its endpoints are
microsecond instants (`dt_*` axioms), a different uninterpreted family from
the day-ordinal axioms.  This keeps the sub-day content of the datetime
endpoints (the `999999`-microsecond calendar upper bound, the `-1µs` ISO
upper bound) — and therefore the field-kind routing — observable in the spec:
an implementation that returns day-scale endpoints for a datetime lookup (the
real-world analogue: `year_lookup_bounds_for_datetime_field` returning
`datetime.date` objects, whose BETWEEN range drops the final day's interior
instants) violates `Result()[i] == dt_lower/dt_upper(...)`.

## C. `YearLookup.year_lookup_bounds` (`lookups.py:541`)

Gold hunk:
```
+ from django.db.models.functions import ExtractIsoYear
+ iso_year = isinstance(self.lhs, ExtractIsoYear)
  output_field = self.lhs.lhs.output_field
  if isinstance(output_field, DateTimeField):
-     bounds = connection.ops.year_lookup_bounds_for_datetime_field(year)
+     bounds = connection.ops.year_lookup_bounds_for_datetime_field(year, iso_year=iso_year)
  else:
-     bounds = connection.ops.year_lookup_bounds_for_date_field(year)
+     bounds = connection.ops.year_lookup_bounds_for_date_field(year, iso_year=iso_year)
```

| # | model.py impl op (`year_lookup_range`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `lhs_is_week_numbering: bool` parameter | `iso_year = isinstance(self.lhs, ExtractIsoYear)` | R | the runtime ISO-vs-calendar decision is modeled as the boolean it computes (mapping.md §1): `ExtractIsoYear` registers the same `YearLookup` subclasses as `ExtractYear`, so the lhs type is the only discriminator. |
| C2 | `if is_datetime_field:` … `else:` | `if isinstance(output_field, DateTimeField):` … `else:` | R | the field-kind test modeled as the boolean it computes; routes to the datetime- vs. date-endpoint method — i.e. selects the instant vs. day carrier. |
| C3 | `datetime_field_year_range(year, lhs_is_week_numbering)` | `year_lookup_bounds_for_datetime_field(year, iso_year=iso_year)` | I (under spec) | the callee is itself a modeled function (site B); its spec is used, not an axiom — the `iso_year` flag is forwarded verbatim, and the returned bounds are instant-carrier values. |
| C4 | `date_field_year_range(year, lhs_is_week_numbering)` | `year_lookup_bounds_for_date_field(year, iso_year=iso_year)` | I (under spec) | site A; same forwarding; day-carrier values. |
| C5 | `return bounds` | `return bounds` | I | identical. |

The discriminating content of the change — that the `iso_year` flag is BOTH
computed (C1) AND forwarded to the endpoint computation (C3/C4), which then
selects the ISO endpoints (A3/A4, B3/B4) instead of the calendar endpoints —
is exactly what the frozen spec pins: each endpoint function's postcondition
requires `Result()[0] == date_lower/dt_lower(value, week_numbering)` and
`Result()[1] == date_upper/dt_upper(value, week_numbering)`, where the pure
selectors choose `iso_jan1/dt_iso_jan1(…)` / `…(+1)-1` when `week_numbering`
and `cal_jan1/dt_jan1` / `cal_dec31/dt_dec31` otherwise; and the dispatch's
postcondition requires
`Result()[i] == lookup_lower/lookup_upper(is_datetime_field, year, lhs_is_week_numbering)`,
which pins BOTH the forwarded flag AND the carrier-matching routing (a
dispatch that swaps the field kinds, or a datetime site that returns day
endpoints, fails it — the two axiom families are distinct uninterpreted
functions).

## D. The prepatch failing clause (G-DIFF)

`model_prepatch.py` reproduces the pre-patch bug: both endpoint methods always
compute the **calendar** year (`cal_jan1`/`cal_dec31` at the date site,
`dt_jan1`/`dt_dec31` at the datetime site), ignoring the week-numbering flag —
exactly the pre-patch source, where `year_lookup_bounds_for_*_field(self,
value)` had no ISO branch and the optimisation was applied uniformly to
`__year` and `__iso_year`.  It FAILS on
`Result()[0] == date_lower(value, week_numbering)` of `date_field_year_range`
and `Result()[0] == dt_lower(value, week_numbering)` of
`datetime_field_year_range` (when `week_numbering` is True the spec requires
the ISO first day/instant but the buggy impl returns the calendar one), which
is the spec sensing the regression at both patched endpoint sites.  The
dispatch site C only forwards the flag, so its fix is observable only through
the endpoint sites it feeds, which the prepatch already breaks.

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I.  The operations that genuinely *changed* — the
choice of which day/instant endpoints bound the year, and the forwarding of
the ISO-vs-calendar flag — are modeled directly (the branch + the pinned
endpoint postconditions).  The only axioms are the **unchanged** stdlib
date/datetime constructors the new code calls (`datetime.date`,
`datetime.datetime`, their `.fromisocalendar`); they are **A-consumed** (the
proof pins the endpoints to them) and their membership meaning is validated
against the real standard library by G-AX (axiom_check.py).  There is no
axiom about the function under change.

## F. verify(model) ⇒ resolved

Each modeled endpoint function verifies only if it returns exactly the
endpoints its carrier's selectors pick for the calendar the lookup uses — the
ISO endpoints for a week-numbering lookup, the calendar endpoints otherwise —
and the dispatch verifies only if it forwards the week-numbering flag AND
routes each field kind to its own carrier's endpoint computation.  By R
(int/bool identities, the day-ordinal and microsecond-instant carrier
bijections of the date/datetime objects and the TZ/adapt steps,
`- timedelta(days=1)` ↔ `- 1` on ordinals, `- timedelta(microseconds=1)` ↔
`- 1` on instants) the verified functions equal the gold methods on the tested
inputs; by G-AX the axiomatized constructors really have the membership
meaning (each interval = its year under its calendar in its carrier, carriers
consistent and distinct), so the ISO endpoints select exactly the ISO-year
rows the F2P boundary test demands — for the DateTimeField the test actually
uses, via the instant carrier.  Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE).  The trust points are
exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity
(this document, G-EQ).
