# mapping.md — matplotlib__matplotlib-26113

## Symbol binding (file:line @ base_commit 5ca694b38d861c0e24cd8743753427dda839b90b)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_hexbinAccum` / `problem_spec_hexbinAccum` | the `accum` list-comprehension in `Axes.hexbin` (the `C is not None` branch) | `lib/matplotlib/axes/_axes.py:5009-5018 @ base_commit` |
| `cellSummary` (pure helper) | the per-element body `reduce_C_function(acc) if len(acc) >= mincnt else np.nan` | `_axes.py:5014-5015` |
| `reduceC` (opaque callee) | the user-supplied `reduce_C_function` | argument of `hexbin` |
| `cells : List (List Float)` | `[acc for Cs_at_i in [Cs_at_i1, Cs_at_i2] for acc in Cs_at_i[1:]]` — the per-cell value lists, out-of-range bucket `[0]` already dropped by `[1:]` | `_axes.py:5016-5017` |
| `mincnt : Int` | `mincnt` (defaulted to `0` when `None`, just above) | `_axes.py:5012-5013` |

### What the code does (base_commit)

In `Axes.hexbin`, when the `C` value array is supplied, points are bucketed into
per-cell value lists (`Cs_at_i1`, `Cs_at_i2`; index `0` is the out-of-range
bucket and is dropped via `[1:]`). Each remaining cell is then reduced to a
single number, or left as `np.nan` when it holds too few points:

```python
if mincnt is None:
    mincnt = 0
accum = np.array(
    [reduce_C_function(acc) if len(acc) > mincnt else np.nan      # base_commit
     for Cs_at_i in [Cs_at_i1, Cs_at_i2]
     for acc in Cs_at_i[1:]],  # [1:] drops out-of-range points.
    float)
```

`good_idxs = ~np.isnan(accum)` later selects which cells are drawn, so a cell
reduced to `np.nan` is omitted from the plot.

The patch changes the keep test from `len(acc) > mincnt` to
`len(acc) >= mincnt`. This makes the `C`-supplied path agree with the
`C is None` path (which uses `accum[accum < mincnt] = np.nan`, i.e. keeps cells
with `count >= mincnt`): with `mincnt=1` a cell holding exactly one point is now
summarised rather than dropped.

### Lean modeling

- `cells : List (List Float)` is the flattened list of per-cell value
  collections (after the `[1:]` drop), in iteration order. The order and count of
  cells is preserved by `List.map`, matching the list comprehension.
- `mincnt : Int` is the threshold after the `None → 0` defaulting (modeled by the
  caller passing the resolved value; `Int` so the `>=`/`>` comparison against the
  `Nat` length is faithful and `mincnt = 0` and negative thresholds are
  expressible).
- `reduceC : List Float → Float` is the opaque user-supplied reduction. It is
  applied identically in spec and impl; no property of it is asserted.
- `Option Float` models the `float`-or-`nan` cell value: `some v` ↔ a reduced
  number `v`; `none` ↔ `np.nan` (the dropped sentinel). The fix is purely in the
  count comparison, not in any float arithmetic, so the discriminator
  (`length ≥ mincnt` vs `length > mincnt`) lives entirely in exact `Int`/`Nat`
  arithmetic — no opaque `Float` order is on the proof path (DECISIONS.md).
- `cellSummary mincnt acc = if acc.length ≥ mincnt then some (reduceC acc) else
  none` is the post-patch per-cell body; `problem_spec_hexbinAccum` pins the whole
  result to `cells.map (cellSummary mincnt)`, fully constraining order, length,
  the kept/dropped decision of every cell, and the value of every kept cell.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `acc` (a cell's value list) | `List Float` | element-wise float identity |
| the flattened cell list | `cells : List (List Float)` | order- and length-preserving |
| `mincnt` (after `None→0`) | `mincnt : Int` | integer identity |
| `reduce_C_function` | `reduceC : List Float → Float` | same function, applied identically |
| a cell's `accum` entry | `Option Float` | reduced float `v ↔ some v`; `np.nan ↔ none` |
| `len(acc) >= mincnt` | `(acc.length : Int) ≥ mincnt` | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The behavior the patch changes —
  the keep test `len(acc) >= mincnt` — is modeled DEEPLY in exact integer
  arithmetic. `reduce_C_function` is UNCHANGED by the patch and orthogonal to the
  fix; it is applied identically in `problem_spec` and `implementation`
  (`opaque reduceC`, no `_prop` axiom), so it constrains no output component the
  spec leaves free — `result` is fully pinned to `cells.map (cellSummary mincnt)`.
  Hence the `axioms` region asserts nothing and **G-AX skips**.
- Flag dependency: this branch is taken only when `C is not None`. The `C is None`
  branch (a separate code path using `np.bincount` + `accum[accum < mincnt] =
  np.nan`) is unchanged by the patch and is not modeled; the issue is precisely
  that the two branches disagreed, and the patch aligns the `C is not None`
  branch with the `C is None` one.

## G-CONF fuzz seed

Pinned LCG seed: **26113** (see `conformance_check.py` `SEED`). Corpus:
randomized cell lists (varying number of cells, varying per-cell point counts
including empty cells and cells of size exactly `mincnt`) crossed with thresholds
`mincnt ∈ {-1, 0, 1, 2, 3}`, with emphasis on the discriminating category — cells
whose length equals `mincnt` (kept post-patch, dropped pre-patch) — over ≥1e5
fuzzed inputs. The R/I shadow of `implementation_hexbinAccum` (with `reduceC`
taken as a concrete real reduction, `sum`) is diffed against an in-process replica
of the POST-PATCH comprehension. Hand-picked edge cases pin the discriminator: a
cell of length exactly `mincnt` is summarised; a cell of length `mincnt-1` is
dropped.
