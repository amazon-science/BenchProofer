# mapping.md — matplotlib__matplotlib-25960

## Instance
- repo: matplotlib/matplotlib
- base_commit: `1d0d255b79e84dfc9f2123c5eb85a842d342f72b` (v3.7)
- changed file: `lib/matplotlib/figure.py`
- changed function:
  `FigureBase.subfigures(self, nrows=1, ncols=1, squeeze=True, wspace=None,
  hspace=None, width_ratios=None, height_ratios=None, **kwargs)`
  (def at `lib/matplotlib/figure.py:1545` @ base_commit)

## What the fix does
Pre-patch, the `wspace`/`hspace` arguments to `subfigures` were silently ignored:
the subfigures were instantiated from a `GridSpec` and the gridspec spacing is
NOT applied at subfigure instantiation, so the panels always tiled the figure
with no gaps. The fix (a) constructs the `GridSpec` spanning the whole figure
(`left=0, right=1, bottom=0, top=1`) and (b) when there is no layout engine and a
spacing was requested, recomputes each subfigure's relative bounding box from
`GridSpec.get_grid_positions(self)` — which DOES honor the spacing — and applies
it via `SubFigure._redo_transform_rel_fig(bbox=…)`.

The modeled behavior is the resulting **per-panel relative rectangle in
figure-fraction coordinates** `[0,1]×[0,1]` (left/bottom/right/top), as a function
of `(nrows, ncols, wspace, hspace)` with equal width/height ratios — exactly what
the F2P test `test_subfigures_wspace_hspace` observes (it reads each subfigure's
`bbox.min`/`bbox.max`, which equal the figure size times the relative rectangle).

## Symbol binding

| Lean | Python | provenance (file:line @ base_commit) |
|---|---|---|
| `implementation_subfigureGrid` / `problem_spec_subfigureGrid` / `correct_subfigureGrid` | the per-subfigure relative-bbox layout produced by `subfigures` for a requested spacing (no layout engine) | `lib/matplotlib/figure.py:1580-1597` (fix region) |
| `gridRects nrows ncols wspace hspace` | `bottoms, tops, lefts, rights = gs.get_grid_positions(self)` assembled into per-panel `Bbox.from_extents(left, bottom, right, top)` | `GridSpec.get_grid_positions` `lib/matplotlib/gridspec.py:144-205`; assembly `figure.py:1589-1596` |
| `panelExtent k s = 1/(k + s·(k-1))` | `cell_w = tot_width/(ncols + wspace·(ncols-1))` (and `cell_h` analogously), with `tot_width = right-left = 1`, equal ratios so `norm·ratio = cell` | `gridspec.py:187-194` (w), `:182-185` (h) |
| `panelGap k s = s·panelExtent k s` | `sep_w = wspace·cell_w` (and `sep_h = hspace·cell_h`) | `gridspec.py:189`, `:183` |
| `colLeft/colRight` | `cell_ws = cumsum([sep,cell,sep,cell,…])`; `fig_lefts, fig_rights = (left + cell_ws).reshape(-1,2).T`; `left=0` | `gridspec.py:191-198,201` |
| `rowTop/rowBottom` | `cell_hs` analogous; `fig_tops, fig_bottoms = (top - cell_hs).reshape(-1,2).T`; `top=1` | `gridspec.py:184-186,200` |
| `nrows`, `ncols` | `nrows`, `ncols` args | params `figure.py:1545` |
| `wspace`, `hspace : ℚ` | `wspace`, `hspace` args (a fraction of the average panel size; requested, non-`None`) | params `figure.py:1546` |
| result `List (List Rect)`, row-major (row 0 topmost) | `sfarr[j, i]` relative bbox; the F2P reads `sf.bbox.min/max = figsize ⊙ (x0,y0)/(x1,y1)` | `figure.py:1593-1596`, test `test_figure.py:1452-1479` |

## Closed-form derivation (G-CONF / spec basis)
With `left=0, right=1, bottom=0, top=1` (set by the fix), equal ratios, and
`get_grid_positions` (raw=False, but the constructed GridSpec pins margins to the
full square so `tot_width = tot_height = 1`):

- `cell = 1/(k + s·(k-1))`, `sep = s·cell`  (panel extent / gap).
- With equal ratios `norm·ratio_i = cell` for every i, so `cell_widths` are all
  `cell` and the cumulative `cell_ws` are `0, cell, cell+sep, 2cell+sep, …`.
- Column i: `left_i = i·(cell+sep)`, `right_i = left_i + cell`.
- Row j (from the top): `top_j = 1 - j·(cell+sep)`, `bottom_j = top_j - cell`.

Numerically verified against the F2P (`nrows=2, ncols=3, wspace=1/6, hspace=1/2`):
lefts `[0, 7/20, 7/10]`, rights `[3/10, 13/20, 1]`, tops `[1, 2/5]`,
bottoms `[3/5, 0]` — matches `test_subfigures_wspace_hspace` expectations exactly
(`w·0.3, h·0.6`, …).

## Type bijection (Lean ↔ Python) — used by G-CONF
- `nrows, ncols : Nat` (≥1)  ↔  the `subfigures` row/column counts.
- `wspace, hspace : ℚ` (≥0)  ↔  the requested spacing floats. Exact `ℚ` models
  the real-valued division of `get_grid_positions` without `Float` opacity
  (DECISIONS.md: float order/arith is opaque to the kernel). G-CONF bridges via
  `Fraction` ↔ float with an absolute tolerance.
- result `Rect (x0,y0,x1,y1)`  ↔  subfigure relative bbox; bridged to the real
  artifact through `sf.bbox.min == [W·x0, H·y0]`, `sf.bbox.max == [W·x1, H·y1]`
  (W,H = figure size in pixels). The factor `figsize` is the comparison
  normalizer, NOT part of the modeled algorithm.

## Callee provenance + flag deps
- `GridSpec.get_grid_positions(fig)` — the unchanged geometry routine the fix
  newly CALLS. Modeled DEEPLY as the closed-form `gridRects` (equal ratios, full
  `[0,1]` extents). A-reference, validated == real by G-CONF. NOT axiomatized.
- `Bbox.from_extents(left, bottom, right, top)` — stdlib-trivial constructor of a
  rectangle from its 4 extents; modeled as `Rect.ofExtents`. I (identical op).
- `SubFigure._redo_transform_rel_fig(bbox=bbox)` — with `bbox` given, simply sets
  `bbox_relative.p0 = bbox.p0`, `.p1 = bbox.p1` (`figure.py:2273-2276`). So the
  per-panel relative rectangle IS the `bbox` passed in; modeled as storing the
  `Rect`. I (identical op).
- Flag deps: the modeled configuration is **no layout engine + spacing requested**
  (`get_layout_engine() is None and (wspace is not None or hspace is not None)`),
  the branch the fix adds and the F2P test exercises. With a constrained-layout
  engine the spacing flows through `get_grid_positions(raw=True)` instead (out of
  model scope). Recorded so G-CONF builds figures with the default (no) engine.

## G-CONF fuzz seed
- pinned seed: `20250630` (see `conformance_check.py` `SEED`).
