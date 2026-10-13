# mapping.md — django__django-16429

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6c86495bcee22eac19d7fb040b2988b830707cbd`, states the type
abstraction, and gives the provenance of the one A-reference (the real
`datetime` subtraction semantics the deep model is validated against).

Repo file under change: `django/utils/timesince.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `pivot_remaining(d, now, pivot_year, pivot_month, pivot_day) -> Tuple[Moment, int]` | the `if years or months:` branch of `timesince` that builds `pivot` and then computes `remaining_time = (now - pivot).total_seconds()` — `django/utils/timesince.py:87-103` | the modeled changed flow: pivot construction + the leftover-span difference; the returned pair is (the constructed pivot, the measured `remaining_time` span) |
| `Moment` | a `datetime.datetime` instance (`d`, `now`, `pivot`) restricted to the touched fields | minimal carrier class |
| `Moment.tz` | a `datetime.datetime`'s time-zone disposition (`d.tzinfo` / aware-vs-naive) | `Optional[int]`: offset-in-minutes when offset-aware, `None` when offset-naive |
| `is_offset_aware(tz)` | `django.utils.timezone.is_aware(value)` = `value.utcoffset() is not None` — `django/utils/timezone.py:246-256` | pure spec: the aware/naive disposition test |
| `same_disposition(a, b)` *(deep model — A-reference)* | the well-definedness condition of `datetime.__sub__` (CPython): two datetimes subtract iff both aware or both naive | pure spec: the subtraction-compatibility predicate |
| `well_defined_diff(now, pivot)` *(deep model — A-reference)* | `(now - pivot).total_seconds()` — `django/utils/timesince.py:103` | the leftover-span difference, guarded by `same_disposition`; its value is pinned to the abstract ordered span `moment_span(now, pivot)`; validated == the real `datetime` subtraction semantics (definedness + ordered-operand functionality) by axiom_check.py (G-AX), NOT a consumed axiom |
| `moment_span(a, b)` *(abstract measure)* | the value of the real ordered difference `(a - b).total_seconds()` | `@Pure @ContractOnly` uninterpreted function naming the ordered span of a pair of moments; its magnitude is unconstrained, but it is a function of the two operands IN ORDER — this is what forces the impl to measure exactly `now - pivot` (not `pivot - now`, not nothing) to discharge the span postcondition |

The pre-patch construction the change repairs (for the refinement audit, not
referenced from the consumer spec view): `pivot = datetime.datetime(pivot_year,
pivot_month, min(MONTHS_DAYS[pivot_month - 1], d.day), d.hour, d.minute,
d.second)` at `timesince.py:93-100` — a constructor with **no** `tzinfo`
argument, hence a naive pivot.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `datetime.datetime` (`d`, `now`, `pivot`) | `Moment` with int fields `year/month/day/hour/minute/second` + `tz: Optional[int]` | each component is the same int; the constructor `datetime.datetime(y, mo, da, h, mi, s, tzinfo=...)` ↔ `Moment(y, mo, da, h, mi, s, tz)` |
| a `tzinfo` object / aware-vs-naive disposition | `Optional[int]` (`None` = naive; an int offset = aware) | only the aware/naive distinction and the carried offset are observed; `is_aware(x)` ↔ `is_offset_aware(x.tz)` (`x.tz is not None`). Nagini bans real `tzinfo`/`datetime` objects, so the disposition is the carrier. |
| `min(MONTHS_DAYS[pivot_month - 1], d.day)` (the pivot day clamp) | the `pivot_day` parameter | an already-correct, unrelated day computation passed in as an int; not under change |
| `(now - pivot).total_seconds()` magnitude | the returned span component `Result()[1]`, pinned to the abstract `moment_span(now, pivot)` | the numeric magnitude is abstract (the change is a crash, not a wrong number), but WHICH ordered difference is measured is observed: the span consumed downstream must be exactly the difference of the current moment and the constructed pivot, in that order |

`datetime` arithmetic and `tzinfo` objects are not expressible in Nagini's
fragment, so the disposition is modelled as `Optional[int]` and the subtraction
as the guarded `well_defined_diff` whose value is the abstract ordered
`moment_span(now, pivot)`; the specification observes the property the bug
concerns — that the difference is well-defined — AND that the span the flow
produces is the difference of exactly that ordered operand pair (the span is
consumed downstream to render the residual string, so it is observable).

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

**No `@ContractOnly` axiom is consumed.** The single A-reference is the
disposition-compatibility rule for `datetime` subtraction, modelled deeply by
`same_disposition` / `well_defined_diff`.

**Semantics:** CPython `datetime.datetime.__sub__` is defined (returns a
`timedelta`, no exception) exactly when both operands are offset-aware or both
offset-naive; an aware/naive mix raises
`TypeError: can't subtract offset-naive and offset-aware datetimes`. An aware
datetime is one whose `utcoffset()` is not `None` (the same predicate
`django.utils.timezone.is_aware` uses). Docs:
https://docs.python.org/3/library/datetime.html#datetime.datetime
("Supported operations … `datetime2 = datetime1 - timedelta`" and the
aware/naive subtraction rules).

**The change's relevance:** `timesince` establishes `now` as offset-aware iff
`d` is (`datetime.datetime.now(timezone.utc if is_aware(d) else None)`,
timesince.py:66). The fix makes `pivot` carry `d.tzinfo` (so it is aware iff `d`
is), making `now` and `pivot` share a disposition, so `now - pivot` is defined.
Pre-patch, `pivot` was always naive; for an aware `d` (the new
`TZAwareTimesinceTests` F2P inputs with `USE_TZ=True`) this is the aware/naive
mix that raised.

**Conformance (G-CONF):** `conformance_check.py` runs the contract-stripped
impl region (shadow, with the difference delegated to the real ordered stdlib
`datetime` subtraction per the binding above) against the patched
`timesince` flow in-container on >= 1e5 branch-reaching probes; pinned fuzz
seed **16429**.

**Soundness check (G-AX):** `axiom_check.py` runs the real `datetime`
subtraction across all aware/naive disposition pairs (6×6 time-zone choices)
and asserts `same_disposition` == the real definedness; and on 30 boundary + 20
000 fuzz source moments asserts that the fixed construction (`tzinfo=d.tzinfo`)
yields a pivot sharing the source's disposition so `now - pivot` is defined,
while the pre-patch construction breaks it for every aware source. Imports only
the standard-library `datetime` module (the very module the patched code uses);
nothing repo-specific. Exit 0 iff sound.
