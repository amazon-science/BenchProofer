# mapping.md — matplotlib__matplotlib-22871

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`a7b7260bf06c20d408215d95ce20a1a01c12e5b1`). No prior twin/spec consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_tickOffset` / `problem_spec_tickOffset` / `correct_tickOffset` | the level-selection + offset-display decision loop inside `ConciseDateFormatter.format_ticks` (the `for level in range(5, -1, -1):` loop computing `level` and `show_offset`) | `lib/matplotlib/dates.py:796-807` |

The CHANGED method is `ConciseDateFormatter.format_ticks`. The single modeled
behavior is the loop that scans the per-tick calendar components from finest to
coarsest, picks the `level` to label at, and decides `show_offset` (whether the
separate offset/summary string — e.g. the year — is displayed).

## The changed code (dates.py, format_ticks)

Each tick datetime is broken into its `timetuple()[:6]` =
`(year, month, day, hour, minute, second)`; `tickdate` is the array of these
rows (one row per tick). The loop at base_commit:

```python
for level in range(5, -1, -1):
    if len(np.unique(tickdate[:, level])) > 1:
        if level < 2:
            show_offset = False
        break
    elif level == 0:
        # all tickdate are the same, so only micros might be different
        level = 5
```

`tickdate[:, level]` is the column of the `level`-th calendar component across
all the ticks; `np.unique(...)` are its distinct values. The loop walks
`level = 5,4,3,2,1,0` (second → year) and stops at the first component that
VARIES (`> 1` distinct values). If that varying component is year (`level 0`) or
month (`level 1`), the pre-patch code sets `show_offset = False`. If no component
varies (the `elif level == 0` arm at the end of the scan), `level` is set to `5`.

The gold patch:

```python
for level in range(5, -1, -1):
    unique = np.unique(tickdate[:, level])
    if len(unique) > 1:
        # if 1 is included in unique, the year is shown in ticks
        if level < 2 and np.any(unique == 1):
            show_offset = False
        break
    elif level == 0:
        level = 5
```

i.e. the `show_offset = False` branch additionally requires `np.any(unique == 1)`
— the distinct values of the varying coarse component must include `1`. For the
month component (`level 1`), value `1` is January; for the year component
(`level 0`), value `1` would be year 1. The intent: only suppress the separate
year/summary label when a start-of-period tick (January, day 1) is already shown
in the ticks themselves. When a sub-year span varies in month but skips January
(F2P: Feb–Aug), `unique` for the month column has no `1`, so `show_offset`
remains `True` and the year is shown in the offset.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| `tickdate` (array of per-tick `timetuple()[:6]` rows) | `td : List (List Nat)` | one inner list per tick; `td[n][j] ↔ tickdate[n][j]`, component order `0=year,…,5=second`. Calendar components are non-negative integers → `Nat`. |
| `tickdate[:, level]` (a column) | `colVals td level = td.map (·.getD level 0)` | the `level`-th component across all ticks |
| `np.unique(tickdate[:, level])` then `len(...)` | `colDistinct td level = (colVals td level).dedup.length` | number of DISTINCT values; `len(np.unique(c))` = number of distinct elements of column `c` (only the COUNT and membership of `c` are used, never the sorted order `np.unique` also produces) |
| `len(np.unique(...)) > 1` | `1 < colDistinct td level` | the component varies across the ticks |
| `np.any(unique == 1)` | `colHasOne td level = (colVals td level).contains 1` | value `1` occurs in that component (`1 ∈ np.unique(c) ↔ 1 ∈ c`) |
| `level < 2` | `decide (level < 2)` | varying component is year or month |
| `range(5, -1, -1)` | `levels = [5,4,3,2,1,0]` | scan finest → coarsest |
| `show_offset` (running flag, init from `self.show_offset`) | `s0 : Bool` (default) → `result.2` | the display flag |
| chosen `level` (after the loop / `elif` fixups) | `result.1 : Nat` | the label level |

### value modeling
Calendar components (year/month/day/hour/minute/second) are non-negative
integers, so `Nat` is exact and order/`decide`-friendly. Only two observations of
each column are consumed: (1) its number of distinct values (`> 1` ?), modeled by
`List.dedup.length`, and (2) whether it contains `1`, modeled by `List.contains`.
`np.unique` ALSO returns the values sorted, but the loop never reads that order —
only the count and the `== 1` membership — so `dedup` (which preserves nothing
about order but agrees on the SET) is a faithful stand-in for both reads. The
inner `getD … 0` default is never exercised on conformant input (every tick row
has all six components); it only makes the Lean lookup total.

## Callee provenance / flag deps

- `np.unique` and `np.any` are UNCHANGED numpy callees. The patch does not change
  them; it changes how their RESULTS are combined (`len(unique) > 1` and the new
  `np.any(unique == 1)` conjunct). Both reads are modeled DEEPLY (`dedup.length`,
  `contains 1`) over the column taken as input, so neither is an axiomatized
  callee contract nor an A-reference — there is no `opaque`/`axiom` declaration,
  and **G-AX skips**.
- The per-tick decomposition `num2date(value).timetuple()[:6]` is an UNCHANGED
  upstream step; its OUTPUT (the calendar rows) is the opaque INPUT `td`. The
  patch touches only the level/offset decision over those rows.
- No flag dependency in the modeled decision: the branch is governed by the
  per-component distinct-count and the `== 1` membership only. (`self.show_offset`
  is the default `s0`; it is set in `__init__` from the `show_offset` ctor arg,
  default `True`.)

## G-CONF fuzz seed

Pinned seed: **22871**. `conformance_check.py` builds the R/I shadow of
`implementation_tickOffset` in Python (the deep models of `dedup.length` /
`contains 1` over each column), and the ORACLE by transliterating the REAL
post-patch decision loop (`np.unique` / `np.any(unique == 1)` over
`tickdate[:, level]`). It feeds both the SAME fuzzed `tickdate` arrays (random
counts of ticks, random per-component calendar values drawn to frequently hit the
discriminating boundaries: month/year columns that do vs. don't include `1`,
constant columns, multi-level variation) plus a discrete edge matrix, and diffs
`(level, show_offset)` over the edge matrix + ≥1e5 randomized draws. Exit 0 iff
zero disagreements.
