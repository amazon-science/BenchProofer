# mapping.md — matplotlib__matplotlib-25960

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1d0d255b79e84dfc9f2123c5eb85a842d342f72b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `lib/matplotlib/figure.py` (the `subfigures` method).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `axisCellExtents (n : Nat) (s : Rat)` | the spacing-aware placement of subfigures introduced into `Figure.subfigures` — `lib/matplotlib/figure.py:1544` (the post-patch block at body lines ~1593-1601) | the modeled changed behaviour: each grid cell's `(low, high)` extent along one axis |
| `axisExtents (n s)` *(deep model — A-reference)* | `GridSpec.get_grid_positions(fig)` — `lib/matplotlib/gridspec.py:145`, evaluated with the patch-supplied full-figure margins `left=0, right=1, bottom=0, top=1` and equal cell ratios | pure spec: the per-cell edge positions along one axis; deep model of the unchanged callee `get_grid_positions`, validated `axisExtents == get_grid_positions` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `cellSize n s` | `cell_w = tot_width/(ncols + wspace*(ncols-1))` and `cell_h = tot_height/(nrows + hspace*(nrows-1))` with `tot_width = tot_height = 1` — `gridspec.py:184,189` | size of one cell as a fraction of the axis |
| `cellPitch n s` | `cell_w*(1+wspace)` (resp. `cell_h*(1+hspace)`): the cell plus its trailing separation `sep_w = wspace*cell_w`, the stride between consecutive `cell_ws`/`cell_hs` entries — `gridspec.py:185-186,190-191` | low-edge-to-low-edge stride |

The pre-patch state the change fixes (refinement audit only, not in the consumer
spec view): `subfigures` created the `GridSpec` **without** `left/right/bottom/top`
and **never** applied the grid positions, so subfigure relative bboxes came from
`SubFigure._redo_transform_rel_fig()`'s default `wr/hr`-ratio split
(`figure.py:2275-2287`) — an even, gap-free tiling that ignores `wspace`/`hspace`
entirely. That even split is the prepatch skeleton's `evenSize = 1/n`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| number of grid rows `nrows` / columns `ncols` (`int ≥ 1`) | `n : Nat`, `n ≥ 1` | identity on naturals |
| `wspace` / `hspace` gap fraction (`float ≥ 0`; `None` ⇒ `0` with no layout engine) | `s : Rat`, `s ≥ 0` | exact rational ↔ float; the placement is an exact ratio computation (no cross-cell round-off accumulation — see below), so the boundary `s = 0` and every positive `s` are represented exactly |
| `lefts, rights` arrays returned by `get_grid_positions` (the **column** axis) | `axisExtents ncols wspace : List (Rat × Rat)` | `lefts[i] ↔ (axisExtents ncols wspace)[i].1`, `rights[i] ↔ …[i].2`; one `(low, high)` pair per column, in column order |
| `bottoms, tops` arrays (the **row** axis) | `(axisExtents nrows hspace).reverse` | the row axis is the SAME spacing computation, but `get_grid_positions` indexes rows from the **top** (`fig_tops, fig_bottoms = (top - cell_hs)…`, `gridspec.py:202`). With `top = 1` this is exactly the bottom-origin `axisExtents` list **reversed**: row `0` (topmost) ↔ the last extent. An order-only R-refinement; the spacing values are unchanged. |
| `Bbox.from_extents(left, bottom, right, top)` (`transforms.py:811`) then `sf._redo_transform_rel_fig(bbox=bbox)` (`figure.py:2271-2273`) | identity (omitted) | both only *carry* the four extent numbers: `from_extents` packs them into a `Bbox`; `_redo_transform_rel_fig(bbox=…)` copies `bbox.p0/p1` into `bbox_relative`. Identity on the `(low, high)` content. |
| the absolute `sub_figs[j,i].bbox.min/.max` the F2P test reads (figure `w×h` px) | `(w·low, h·bottom) … (w·right, h·top)` | the figure's `transSubfigure` scales the **relative** extents by the figure size `(w, h) = (640, 480)`. A fixed affine R-refinement applied identically pre/post patch; it does not alter which relative extents are produced, which is the behaviour under spec. |

**Why `Rat` is faithful (float-band justification).** `get_grid_positions`
computes each edge as `i·cell + i·sep` (cumulative sum of equal `cell`/`sep`
increments). The model `cellPitch · i` is the same closed form. There is no
iterative accumulation of heterogeneous magnitudes and no transcendental step;
the result is a rational function of `(n, s)`. The discriminating behaviour the
F2P test observes — that a positive gap *separates* cells (`high i < low (i+1)`)
versus the buggy even split where they abut — is an exact order/identity property,
precision-independent. So an exact ordered carrier (`Rat`) is faithful and the
G-CONF equality predicate is exact up to a tiny ULP tolerance for the float
oracle (§4).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `axisExtents` deep model ↔ `GridSpec.get_grid_positions` (A-reference)
**Callee:** `matplotlib.gridspec.GridSpec.get_grid_positions(fig, raw=False)`
(`lib/matplotlib/gridspec.py:145`). This callee is **unchanged** by the patch;
the patch newly *calls* it from `subfigures` after constructing the `GridSpec`
with the full-figure margins `left=0, right=1, bottom=0, top=1`. The changed
placement behaviour is modeled **deeply** by `axisExtents` (with `cellSize`,
`cellPitch`) in the `pure` region; there is **no consumed axiom** about it.

With the patch-supplied margins the GridSpec's own non-`None` `left/right/
bottom/top` override the figure's subplotpars (`get_subplot_params`,
`gridspec.py:412-432`), so `tot_width = right-left = 1` and `tot_height =
top-bottom = 1`. With default (equal) `width_ratios`/`height_ratios` the `norm`
factor is `1`, every `cell_widths[k] = cell_w` and `cell_heights[k] = cell_h`,
and the interleaved cumulative sums reduce to:

```
cell_w = 1/(ncols + wspace*(ncols-1));  sep_w = wspace*cell_w
lefts[i]  = i*(cell_w + sep_w) = i*cell_w*(1+wspace)   = i*cellPitch
rights[i] = lefts[i] + cell_w                          = i*cellPitch + cellSize
```

which is exactly `axisExtents ncols wspace`. The row axis is identical with
`hspace`, then top-indexed (`top - cell_hs`) ⇒ `(axisExtents nrows hspace).reverse`
(see §2). The single F2P test `test_subfigures_wspace_hspace` (`nrows=2, ncols=3,
hspace=0.5, wspace=1/6`) is reproduced exactly by this model — verified below.

**Soundness check (G-AX):** `axiom_check.py` constructs a real
`matplotlib.figure.Figure` and `GridSpec(..., left=0, right=1, bottom=0, top=1)`,
calls the **real** `get_grid_positions` on boundary configurations
(`n ∈ {1,2,3,5}`, `s ∈ {0, 1/6, 1/2, 1, …}`) plus randomized fuzz, and asserts
`lefts/rights == axisExtents(ncols, wspace)` and `bottoms/tops ==
reverse(axisExtents(nrows, hspace))` to a tight float tolerance. Imports only
`matplotlib` (available in-container). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`25960`** so the
consumer-side verdict is reproducible. It transliterates the model's R/I shadow
(`cellSize`/`cellPitch`/`axisExtents`) to Python and diffs against an ORACLE that
transliterates the reduced `get_grid_positions` arithmetic VERBATIM (the same
closed form the patched code path evaluates with `left=0,right=1,bottom=0,top=1`
and equal ratios), over ≥10⁵ fuzzed `(nrows, ncols, wspace, hspace)`. Equality is
asserted with a `1e-9` relative tolerance (float oracle vs exact-rational shadow).
Exit 0 iff zero disagreements.
