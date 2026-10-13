# mapping.md — django__django-16429

## Symbol binding (file:line @ base_commit 6c86495bcee22eac19d7fb040b2988b830707cbd)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_anchor` / `problem_spec_anchor` | the `pivot` datetime construction inside `timesince` (the `if years or months:` branch) | `django/utils/timesince.py:87-100` |
| `Instant` (structure) | a `datetime.datetime` value, restricted to the fields the pivot construction reads/writes | — |
| `monthLengths` / `monthLength` | `MONTHS_DAYS = (31, 28, …, 31)` and `MONTHS_DAYS[pivot_month - 1]` | `django/utils/timesince.py:25`, `:96` |

The modeled function is the **pivot construction** in `timesince`. It is the only
code the patch changes, and the only place whose output (the `pivot` datetime)
feeds the subsequent `(now - pivot).total_seconds()` subtraction that the
FAIL_TO_PASS tests exercise.

### What the code does (base_commit)

```python
# total_months computed; years, months = divmod(total_months, 12)
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
    )
else:
    pivot = d
remaining_time = (now - pivot).total_seconds()
```

The pivot is `d` shifted forward by `years` years and `months` months. Its
year/month are `d`'s advanced by the request (rolling a month past December into
the next year); its day is `d.day` clamped to the last valid day of the resulting
month; its `hour`/`minute`/`second` are copied from `d`.

At base_commit the `datetime.datetime(...)` call omits the `tzinfo` argument, so
the constructed pivot is **timezone-naive** regardless of `d`. When `d` is
timezone-aware (the `USE_TZ=True` configuration), the later `now - pivot`
subtracts a naive `pivot` from an aware `now`, which raises
`TypeError: can't subtract offset-naive and offset-aware datetimes`. The defect in
the issue. The post-fix code passes `tzinfo=d.tzinfo`, so the pivot carries the
same timezone designation as `d` and the subtraction is well typed.

The modeled scope is exactly the pivot's field-by-field construction, including
the timezone designation it must carry. The surrounding arithmetic
(`total_months`, `divmod`, the `now - pivot` subtraction, the chunk loop) is
unchanged by the patch and out of the modeled function.

### Inputs ↔ Python expression bijection

`problem_spec_anchor` / `implementation_anchor` take `(d : Instant) (years months
: Int)`. This branch is reached only when `years or months` is truthy, with
`years, months = divmod(total_months, 12)` so `0 ≤ months ≤ 11` (the binder
preconditions). `1 ≤ d.month ≤ 12` because `d.month` is a real calendar month.

| Lean input/field | Python expression | type | notes |
|---|---|---|---|
| `d.year` | `d.year` | `Int` | the starting instant's year. |
| `d.month` | `d.month` | `Int` | calendar month 1‥12 (precondition). |
| `d.day` | `d.day` | `Int` | day of month. |
| `d.hour` | `d.hour` | `Int` | copied into the pivot unchanged. |
| `d.minute` | `d.minute` | `Int` | copied unchanged. |
| `d.second` | `d.second` | `Int` | copied unchanged. |
| `d.offset` | `d.tzinfo`, abstracted to its fixed UTC offset in seconds (`None` when naive) | `Option Int` | `none` ↔ naive datetime; `some k` ↔ aware datetime at offset `k`. The pivot must carry the SAME value. |
| `years` | `years` (from `divmod(total_months, 12)`) | `Int` | whole years to add. |
| `months` | `months` (from `divmod(total_months, 12)`) | `Int` | `0 ≤ months ≤ 11`. |

### result bijection

| Lean | Python | bijection |
|---|---|---|
| `result : Instant` | the `pivot` `datetime.datetime` value | field-by-field identity on year/month/day/hour/minute/second plus the timezone designation (`result.offset` ↔ `pivot.tzinfo`'s offset). |

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| `datetime.datetime` (the pivot-relevant fields) | `Instant` structure | identity on the seven modeled fields. |
| `d.tzinfo` | `offset : Option Int` | `None ↔ none`; a fixed-offset tzinfo at `k` seconds ↔ `some k`. The pivot's `tzinfo` MUST equal `d`'s, which is exactly `result.offset = d.offset`. |
| `MONTHS_DAYS[m-1]` | `monthLength m` | identity on the 12-entry table; `monthLength` = `monthLengths.getD (m.toNat-1) 31`. |
| `min(MONTHS_DAYS[pivot_month-1], d.day)` | `min (monthLength result.month) d.day` | identity (`min` of two ints). |

`datetime` ↔ `Instant`: the pivot construction reads only year/month/day/hour/
minute/second and `tzinfo` from `d`, and writes only those; modeling the value as
a structure with exactly those fields is exact for the observable behavior (§2
cheatsheet, "rich object → structure with only the touched fields").

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The pivot construction is pure structure assembly
  over `d`'s fields plus the constant `MONTHS_DAYS` table and integer `min` /
  arithmetic. It is modeled DEEPLY (SPEC_GUIDE §3: a changed op is modeled, never
  axiomatized), so there is no `opaque`/`axiom` callee whose contract the proof
  consumes. `axiom_check.py` is therefore a skip stub and G-AX skips.
- **`datetime.datetime(...)` constructor** is not a repo callee under spec; it is
  the value constructor whose argument list the patch edits. Its effect — build a
  datetime from the supplied fields, with the supplied (or absent) `tzinfo` — is
  reproduced by the `Instant` record construction in the impl. The patch's edit
  (adding `tzinfo=d.tzinfo`) is exactly the `offset := d.offset` field.
- **`MONTHS_DAYS`** is a module-level constant tuple, unchanged by the patch;
  reproduced verbatim as `monthLengths`.
- **Flag dependency.** The observable failure depends on `USE_TZ` only insofar as
  it makes `d` timezone-aware (`is_aware(d)` true ⇒ `now` is aware too). In the
  model this is `d.offset = some k`; the discriminating spec clause
  `result.offset = d.offset` is exactly what distinguishes aware from naive. The
  conformance differential fuzzes both `offset = none` and `offset = some k`.

## G-CONF fuzz seed

Pinned LCG seed: **16429** (see `conformance_check.py` `SEED`). Corpus: random
`Instant` field values (year, month 1‥12, day 1‥31, hour/minute/second in range),
`offset ∈ {None} ∪ {random signed second offsets}`, and `years ∈ [0,5]`, `months
∈ [0,11]`, over ≥1e5 fuzzed inputs, diffed against an in-process replica of the
post-patch pivot construction (a `datetime`-free field-level replica that builds
the same seven output fields, INCLUDING the carried-over timezone designation).
