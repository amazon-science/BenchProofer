# refinement.md — matplotlib__matplotlib-25960

Maps every op in `implementation_subfigureGrid` to its `patch.diff` counterpart.
Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's property),
**A-reference** (deep model validated == real callee by G-CONF/G-AX), **I**
(identical concrete op).

## Scope
The fix makes `Figure.subfigures` honor the requested `wspace`/`hspace`: it builds
the `GridSpec` over the full figure (`left=0, right=1, bottom=0, top=1`) and, when
no layout engine is active and a spacing was requested, recomputes each
subfigure's relative bounding box from `gs.get_grid_positions(self)` and applies
it. Modeled behavior: the **per-panel relative rectangle** `(x0,y0,x1,y1)` in
figure-fraction coordinates as a function of `(nrows, ncols, wspace, hspace)` with
equal ratios — exactly what the F2P test `test_subfigures_wspace_hspace` reads
(`sf.bbox.min/max`). Preconditions `1 ≤ nrows`, `1 ≤ ncols`, `0 ≤ wspace`,
`0 ≤ hspace` pin the no-layout-engine, spacing-requested branch.

## Operation correspondence

| # | Lean op (`implementation_subfigureGrid`) | patch.diff counterpart | tag |
|---|---|---|---|
| 1 | `wspace hspace : ℚ`, `nrows ncols : Nat` | the `wspace`/`hspace` floats and `nrows`/`ncols` ints passed to `subfigures` | R — float spacing refined to exact `ℚ` (kernel-sound division; G-CONF bridges via tolerance). |
| 2 | result `List (List Rect)`, row `j` topmost | the `sfarr[j,i]` grid of subfigure relative bboxes | R — a `SubFigure`'s touched geometry refined to its relative rectangle `(x0,y0,x1,y1)`; bijection in mapping.md. |
| 3 | `lefts/rights/bottoms/tops` via `colLeft/colRight/rowBottom/rowTop` (closed form of `panelExtent`/`panelGap`) | `bottoms, tops, lefts, rights = gs.get_grid_positions(self)` with the gridspec built `left=0,right=1,bottom=0,top=1` and equal ratios | A-reference — `get_grid_positions` modeled deeply as the equal-extent/proportional-gap tiling; validated == real by G-CONF. |
| 4 | `for j in [0:nrows] do … for i in [0:ncols] do … Rect.ofExtents left bottom right top` | nested `for sfrow,bottom,top in zip(sfarr,bottoms,tops): for sf,left,right in zip(sfrow,lefts,rights): Bbox.from_extents(left,bottom,right,top)` | I — same nested row/col walk building each panel's rectangle from the four extents (`Bbox.from_extents` ↔ `Rect.ofExtents`). |
| 5 | the built `Rect` IS the panel's stored rectangle | `sf._redo_transform_rel_fig(bbox=bbox)` with `bbox` given sets `bbox_relative.p0/p1 = bbox.p0/p1` | I — applying the bbox stores exactly that rectangle as the subfigure's relative bbox. |

No changed op is left inexpressible. No op is axiomatized: the only nontrivial
callee (`get_grid_positions`) is modeled DEEPLY as `gridRects`, hence an
A-reference (validated by G-CONF), not a consumed axiom.

## Prepatch (the bug)
`Solution_prepatch.lean` drops the requested spacing: it computes every panel
rectangle as though `wspace = hspace = 0` (the pre-patch reality, where the
gridspec spacing is ignored at subfigure instantiation and no gaps are left). For
any positive spacing this produces gap-free panels — e.g. on the F2P
`(2,3,wspace=1/6,hspace=1/2)` the columns become `0/3̄, 1/3̄/…` with no gaps,
disagreeing with the spec target `gridRects` (lefts `0, 7/20, 7/10`). Hence the
carried gold proof is unclosable → G-DIFF fires. Confirmed: `implementation =
gridRects` evaluates `false` for the prepatch on the F2P input, `true` for the
patched impl.
