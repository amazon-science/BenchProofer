# refinement.md — django__django-16429

Maps every operation in `implementation_anchor` to its `patch.diff` /
base-commit counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `anchor` (the `pivot` construction in `timesince`)

Post-patch repo code (`django/utils/timesince.py`, the fix adds `tzinfo=d.tzinfo`):
```python
if years or months:
    pivot_year = d.year + years
    pivot_month = d.month + months
    if pivot_month > 12:
        pivot_month -= 12
        pivot_year += 1
    pivot = datetime.datetime(
        pivot_year,
        pivot_month,
        min(MONTHS_DAYS[pivot_month - 1], d.day),
        d.hour,
        d.minute,
        d.second,
        tzinfo=d.tzinfo,          # <-- the fix
    )
```

Lean impl (`implementation_anchor`):
```lean
def implementation_anchor
    (d : Instant) (years months : Int) : Instant := Id.run do
  let mut anchorYear := d.year + years
  let mut anchorMonth := d.month + months
  if anchorMonth > 12 then
    anchorMonth := anchorMonth - 12
    anchorYear := anchorYear + 1
  return {
    year := anchorYear, month := anchorMonth,
    day := min (monthLength anchorMonth) d.day,
    hour := d.hour, minute := d.minute, second := d.second,
    offset := d.offset
  }
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `d : Instant`, `years months : Int` inputs | `d` (datetime), `years`, `months` (from `divmod`) | **R** | `datetime` modeled as the `Instant` record over the seven pivot-relevant fields; `d.tzinfo` ↦ `offset : Option Int` (mapping.md). Exact for the pivot construction, which reads only those fields. |
| 2 | `let mut anchorYear := d.year + years` | `pivot_year = d.year + years` | **I** | integer addition of the year shift. |
| 3 | `let mut anchorMonth := d.month + months` | `pivot_month = d.month + months` | **I** | integer addition of the month shift. |
| 4 | `if anchorMonth > 12 then anchorMonth := anchorMonth - 12; anchorYear := anchorYear + 1` | `if pivot_month > 12: pivot_month -= 12; pivot_year += 1` | **I** | the December roll-over, line-for-line. |
| 5 | `year := anchorYear` | first arg `pivot_year` | **I** | the pivot's year. |
| 6 | `month := anchorMonth` | second arg `pivot_month` | **I** | the pivot's month. |
| 7 | `day := min (monthLength anchorMonth) d.day` | third arg `min(MONTHS_DAYS[pivot_month - 1], d.day)` | **I** | day clamped to the resulting month's length; `monthLength` reproduces `MONTHS_DAYS[m-1]` (mapping.md). |
| 8 | `hour := d.hour` | fourth arg `d.hour` | **I** | clock field copied. |
| 9 | `minute := d.minute` | fifth arg `d.minute` | **I** | clock field copied. |
| 10 | `second := d.second` | sixth arg `d.second` | **I** | clock field copied. |
| 11 | `offset := d.offset` | `tzinfo=d.tzinfo` | **I** (the fixed op) | **the fix.** The post-patch constructor carries `d`'s timezone designation onto the pivot; pre-patch the `tzinfo` argument was absent, producing a naive pivot. `offset := d.offset` reproduces this exactly (`d.tzinfo` ↦ `d.offset`). |
| 12 | `return { … }` / `Id.run do` | `pivot = datetime.datetime(...)` | **I** | the constructed pivot value is the result. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process field-level
replica of the post-patch pivot construction.

Refinement equivalence (R/I): the pivot construction is pure arithmetic + a
constant table lookup + record assembly; the Lean impl performs the identical
operations on the `Instant` carrier. The only behavior the patch alters is which
timezone designation the pivot carries — `tzinfo=d.tzinfo` (post-fix) vs absent
(pre-fix, i.e. `None`); modeled exactly by `offset := d.offset` vs `offset :=
none`. The downstream `(now - pivot).total_seconds()` is an unchanged consumer of
the pivot and not part of the modeled function; it succeeds iff `pivot` and `now`
share a timezone designation, which holds iff the pivot copies `d`'s designation.

## Soundness check (verify ⟹ correct)

- `problem_spec_anchor` pins EVERY output field of the pivot to its input (frame
  discipline, directive 5): `year`/`month` to the rolled-over shift, `day` to the
  clamped `min`, `hour`/`minute`/`second` to `d`'s, and crucially `result.offset =
  d.offset`. No component is left unconstrained; no ungrounded oracle (directive
  8) — every field is a structural/arithmetic relation on `d`, `years`, `months`,
  so the result must be *produced by* the modeled construction.
- The prepatch impl sets `offset := none` (the absent-`tzinfo` base-commit
  behavior), returning a pivot that drops the timezone designation. It violates
  the spec on the discriminating clause `result.offset = d.offset` for any input
  with `d.offset = some k` (a timezone-aware datetime — the `USE_TZ=True` case).
  Its carried gold proof leaves the unprovable goal `none = some k` and fails to
  typecheck (G-DIFF/G-PANEL).
- This discriminating case is exactly what the FAIL_TO_PASS tests exercise: the
  `TZAwareTimesinceTests` subclass runs the suite with `USE_TZ=True` and
  timezone-aware datetimes. With a naive pivot (prepatch) the `now - pivot`
  subtraction raises `TypeError` on any interval ≥ 1 month (which forces the
  `years or months` branch); with the timezone designation carried over (gold)
  the subtraction is well typed and the suite passes. The spec's `result.offset =
  d.offset` clause is precisely the property whose absence triggers the crash.
- G-CONF confirms the R/I shadow == an in-process field-level replica of the
  patched pivot construction over hand-picked edge cases (`offset = None`, `offset
  = some k`, December roll-over, day clamping into a short month, leap-ish
  boundaries) plus ≥1e5 fuzzed inputs.
