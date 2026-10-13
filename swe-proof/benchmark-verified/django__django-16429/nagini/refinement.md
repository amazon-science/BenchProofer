# refinement.md — django__django-16429

The operation-by-operation correspondence between `model.py`'s implementation
(the `pivot_remaining` impl region, plus the deep `well_defined_diff` /
disposition model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee/semantics by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The pivot-construction site — `timesince()` (`django/utils/timesince.py:93-100`)

Gold hunk (the only change):
```
             d.hour,
             d.minute,
             d.second,
+            tzinfo=d.tzinfo,
         )
```
i.e. the `pivot = datetime.datetime(pivot_year, pivot_month, min(...), d.hour,
d.minute, d.second)` construction in the `if years or months:` branch gains
`tzinfo=d.tzinfo`.

| # | model.py impl op (`pivot_remaining`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameters `d: Moment`, `now: Moment` | the `d` argument and the `now` local of `timesince` | R | a `datetime.datetime` ↔ a `Moment` carrying only the touched fields; the time-zone object ↔ `tz: Optional[int]` (offset in minutes, `None` = naive). Only the aware/naive distinction + carried offset is observed (mapping.md §2). |
| A2 | `same_disposition(now.tz, d.tz)` precondition | `now = now or datetime.datetime.now(utc if is_aware(d) else None)` (timesince.py:66) | R + I | the current moment is established offset-aware iff `d` is; modelled as the precondition that `now` and `d` share a disposition. (`is_aware(x)` ↔ `is_offset_aware(x.tz)`; mapping.md §3.) |
| A3 | `Moment(pivot_year, pivot_month, pivot_day, d.hour, d.minute, d.second, d.tz)` | `datetime.datetime(pivot_year, pivot_month, min(MONTHS_DAYS[...], d.day), d.hour, d.minute, d.second, tzinfo=d.tzinfo)` | R + I | field-for-field the same constructor. The calendar/clock fields are ints (I). The discriminating argument `tzinfo=d.tzinfo` ↔ the seventh constructor argument `d.tz`: the pivot carries the source's disposition. `pivot_day` ↔ `min(MONTHS_DAYS[pivot_month-1], d.day)` is an unrelated already-correct day clamp passed through as a parameter (R; not under change). |
| A4 | `remaining = well_defined_diff(now, pivot)` | `remaining_time = (now - pivot).total_seconds()` (timesince.py:103) | A-reference | the leftover-span difference is modelled **deeply** as a guarded operation with an ordered-value claim: `well_defined_diff` `Requires(same_disposition(now.tz, pivot.tz))` and `Ensures(Result() == moment_span(now, pivot))`, where `moment_span` is the **uninterpreted** abstract ordered span. The real `(now - pivot)` is defined (no `TypeError`) **exactly** when `now` and `pivot` share a disposition, and its value is a function of the two operands **in order** (`a - b` is not `b - a`) — both facts are the real `datetime` subtraction semantics, validated == the deep model out-of-band by G-AX (axiom_check.py), NOT consumed as a `@ContractOnly` axiom. The magnitude of the difference is abstract (the bug is a crash, not a wrong number), but the measured span IS load-bearing: it is consumed downstream (`partials = remaining_time // chunk`) to render the residual string, so the impl must **measure and return** exactly the ordered `now`-minus-`pivot` span. First positional argument ↔ left operand. |
| A5 | `return pivot, remaining` | `pivot = datetime.datetime(...)` and `remaining_time = ...` then used downstream | R | the constructed pivot, with EVERY field an F2P test transitively observes pinned by a postcondition: `Result()[0].year == pivot_year`, `Result()[0].month == pivot_month`, `Result()[0].day == pivot_day`, `Result()[0].hour/minute/second == d.hour/minute/second`, and `Result()[0].tz is d.tz`; PLUS the measured span pinned to the ordered difference of the current moment and that pivot: `Result()[1] == moment_span(now, Result()[0])`. The pivot is the source advanced to the supplied calendar position carrying the source clock fields and disposition — exactly `datetime.datetime(pivot_year, pivot_month, min(MONTHS_DAYS[...], d.day), d.hour, d.minute, d.second, tzinfo=d.tzinfo)`; the span is exactly `(now - pivot).total_seconds()`. (Pinning the full carrier AND the span source is required for soundness: the rendered elapsed-time string depends on the pivot's calendar position and on the measured residual span, so leaving year/month/day free — or the span's operands/order free — would admit a refining impl that verifies yet renders the wrong leftover span.) |

## B. The discriminating clause and `model_prepatch`

The behavioural change is: the constructed `pivot` must carry the source's
time-zone disposition, so that the subsequent `now - pivot` is well-defined for
an offset-aware source. The pre-patch built the pivot from the bare fields
(naive); with an aware source the `now`/`pivot` mix is undefined — the real
`TypeError: can't subtract offset-naive and offset-aware datetimes`.

`model_prepatch.py` reproduces exactly that: it constructs the pivot with `None`
for the disposition (the bare-fields, naive construction). It **fails**
verification on
```
The precondition of method well_defined_diff might not hold.
Assertion same_disposition(now.tz, pivot.tz) might not hold.
```
which is the spec sensing the bug (G-DIFF): with an aware `now` and a naive
pivot, the leftover-span difference is undefined. (The postcondition
`Result().tz is d.tz` is an independent second witness of the same change.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely *changed*
— passing the source's time-zone information into the pivot constructor so the
later difference stays well-defined — is modelled **deeply**: the `Moment`'s
`tz` field carried through the constructor (A3) and the disposition-guarded
`well_defined_diff` (A4, an **A-reference** validated against the real
`datetime` subtraction semantics by G-AX). There is **no consumed
`@ContractOnly` axiom** — nothing about an unchanged callee is needed; the whole
delta is the one constructor argument and its effect on subtraction
definedness, both modelled directly.

## D. verify(model) ⇒ resolved

`pivot_remaining` verifies only if (A3/A5) the constructed pivot is the source
advanced to the supplied calendar position carrying the source's clock fields
and disposition — every observed result field pinned: `Result()[0].year ==
pivot_year`, `Result()[0].month == pivot_month`, `Result()[0].day ==
pivot_day`, `Result()[0].hour/minute/second == d.hour/minute/second`,
`Result()[0].tz is d.tz` — AND (A4) the returned span equals
`moment_span(now, Result()[0])`, the abstract ordered difference of the current
moment and that pivot. Because `moment_span` is uninterpreted, the ONLY way an
impl can discharge the span clause is to actually invoke the guarded difference
on precisely the ordered pair `(now, pivot)` — which in turn is provable only
when `now` and `pivot` share a disposition, established because the pivot
carries `d.tz` and `now` agrees with `d` (A2). This pinning is what makes
verify ⇒ resolve:
  * a pivot at any other calendar position (e.g. the un-advanced
    `d.year/d.month/d.day`) renders the wrong leftover span (the F2P
    `test_thousand_years_ago` / `test_long_interval_with_tz` failures) —
    REJECTED by the `Result()[0]` field pins;
  * an impl that measures the difference with the operands REVERSED
    (`well_defined_diff(pivot, now)`) obtains `moment_span(pivot, now)`, which
    is not provably `moment_span(now, pivot)` — its faithful patch sign-flips
    `remaining_time` and does not resolve — REJECTED by the span clause;
  * an impl that drops the measurement (returns a constant span) refines to a
    patch with no `remaining_time` assignment (NameError downstream) —
    REJECTED by the span clause (no constant proves equal to the
    uninterpreted span).
By R (`datetime` ↔ `Moment`, tz object ↔ `Optional[int]` disposition, the int
clock fields, the day-clamp parameter) the verified construction equals the
gold `datetime.datetime(pivot_year, pivot_month, min(MONTHS_DAYS[...], d.day),
d.hour, d.minute, d.second, tzinfo=d.tzinfo)` and the verified span equals the
gold `remaining_time = (now - pivot).total_seconds()` on the tested inputs; by
G-AX the disposition-compatibility guard equals the real `datetime` subtraction
rule and the ordered-operand functionality of the span matches the real
subtraction (A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited
semantics — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: A-reference soundness (G-AX) and refinement
fidelity (this document, G-EQ); there is no consumed axiom.
