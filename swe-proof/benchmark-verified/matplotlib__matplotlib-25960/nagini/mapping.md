# mapping.md — matplotlib__matplotlib-25960

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1d0d255b79e84dfc9f2123c5eb85a842d342f72b`, states the type
abstraction, and gives the provenance of the kind-A reference (the deep geometry
model validated against the real callee by G-AX).

Repo file under change: `lib/matplotlib/figure.py` (`Figure.subfigures`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `grid_cell_placement(nrows, ncols, j, i, wspace, hspace, cw, ch)` | `Figure.subfigures` — `lib/matplotlib/figure.py:1543` (the added gap-honouring placement, body lines 1583-1601 post-patch) | the modeled changed function: the per-cell placement the change introduces |
| `col_left / col_right / row_top / row_bottom` *(deep model — A-reference)* | `GridSpec.get_grid_positions` — `lib/matplotlib/gridspec.py:145` (the `cell_ws`/`cell_hs` cumsum → `lefts/rights`, `tops/bottoms`, lines 183-204) | pure spec: the closed-form cell extents for equal ratios; the deep model of the (unchanged) routine the patch calls `gs.get_grid_positions(self)`, validated `== get_grid_positions` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `cw` (input, pinned by `cw*(ncols+wspace*(ncols-1))==1`) | `cell_w = tot_width/(ncols+wspace*(ncols-1))`, `tot_width = right-left = 1` (`gridspec.py:183,195`) | normalized column width; `tot_width=1` because the patch sets `left=0, right=1` on the gridspec |
| `ch` (input, pinned by `ch*(nrows+hspace*(nrows-1))==1`) | `cell_h = tot_height/(nrows+hspace*(nrows-1))`, `tot_height = top-bottom = 1` (`gridspec.py:184,187`) | normalized row height; `tot_height=1` because the patch sets `bottom=0, top=1` |
| `CellRect(left, bottom, right, top)` | `matplotlib.transforms.Bbox.from_extents(left, bottom, right, top)` (`transforms.py:811`) + the relative-bbox write in `SubFigure._redo_transform_rel_fig(bbox=...)` (`figure.py:2261`, lines 2271-2274) | minimal carrier of the four cell extents the patch feeds to `_redo_transform_rel_fig` |

The pre-patch behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): `subfigures` built the gridspec WITHOUT
`left/right/bottom/top` and never called `get_grid_positions`, so each subfigure
kept the ratios-only, gap-less relative bbox computed by the default branch of
`SubFigure._redo_transform_rel_fig(bbox=None)` (`figure.py:2275-2287`,
`x0 = wr[:colspan.start].sum()/wr.sum()`, `dx = wr[colspan].sum()/wr.sum()`,
etc.) — equal ratios give column i `x0 = i/ncols`, `dx = 1/ncols`, i.e. no gap.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `int` grid counts `nrows, ncols` and loop indices `j, i` | integer-valued `float` (`nrows>=1.0`, `0<=i<=ncols-1.0`, …) | `--float-encoding=real` does not support `float(int)` coercion, so the counts/indices are carried as the reals they denote; comparisons and the "next cell" step `i+1.0` are exact real arithmetic. |
| real division `cell_w = 1/(ncols+wspace*(ncols-1))` (and `cell_h`) | positive input `cw` (resp. `ch`) pinned by the **linear** equation `cw*(ncols+wspace*(ncols-1))==1` | Z3's real-division fragment cannot discharge reciprocal facts (`(1/d)*d==1` is not provable under `--float-encoding=real`); the value the division produces is uniquely characterized by that linear equation, so `cw`/`ch` enter as inputs satisfying it (grounded in the inputs, not an oracle). The gold patch's `left=0,right=1,bottom=0,top=1` is exactly what pins `tot_width=tot_height=1`. |
| `matplotlib.transforms.Bbox` (relative bbox) | `CellRect` class with `left, bottom, right, top: float` | `Bbox.from_extents(l,b,r,t)` → `min=(l,b)`, `max=(r,t)`; `_redo_transform_rel_fig` writes these into `bbox_relative.p0/p1`. The F2P test reads `sub_figs[j,i].bbox.min == [l*w, b*h]`, `.max == [r*w, t*h]` (the figure pixel size `w,h` is untouched by the patch). |
| `wspace, hspace` (float gap fractions) | `float` (`>= 0`) | identity; `None` defaults are resolved before this function (the modeled placement runs only when they are given and no layout engine is active). |

`--float-encoding=real` is required: the placement is a real-valued geometric
computation the F2P test (`np.testing.assert_allclose`) probes to floating
tolerance, and the discriminating value (column 1 at `0.35` vs `1/3`) is a real
inequality, not an integer fact.

**Side-condition on the ℝ↔`float64` bridge, stated on the operations rather than
the magnitudes.** Each R step above claims that the real code's `float64`
evaluation *represents* the ℝ value the model's step denotes; a step where the two
differ is not a type refinement at all, but a changed operation the model does not
express. This is load-bearing in both directions. It is why the deep geometry is
an **A-reference** (§3.1) and not an identical operation: a refinement READS each
cell's extents from `get_grid_positions`, and the closed form re-evaluated in
`float64` would put the bottom row's bottom edge at `-1.11e-16` on the graded
configuration, where the routine's own cumulative sum returns exactly `0.0`. And
it is what excludes a program any step of which has an ℝ value the step's `float64`
evaluation does not denote: additively a real `0`, multiplicatively or divisively a
real `1`, an ℝ identity applied to a whole extent, a re-parameterization through an
intermediate the routine delivers no counterpart for (a cell centre, from which the
extents come back as `mid ± half`), or a CONDITION whose ℝ truth value
the precondition settles while its `float64` comparison reads the other way. Over ℚ
such a program IS the gold function, so no clause stated over ℚ could distinguish
it, and a patch that transcribes the step implements a function the program does
not denote. Magnitude is the wrong axis for this — `float64` addition is
non-associative at unit scale, so the class has members every quantity of which
lies in `[0, 1]`; the guard members show the axis is not even arithmetic; and the
centre member has no real `0` and no real `1` in it to spot at all.
See refinement.md §C.1, whose patch-construction recipe states the rendering the
condition implies, step by step. axiom_check.py (G-AX) measures this
condition instead of leaving it to prose: it asserts the exactness the condition
needs where the graded comparison has no tolerance to spend (the grid origin);
asserts that the two candidate renderings of the model's steps disagree there —
extents READ from the routine close the graded grid at exactly `0.0`, the closed
form re-derived in `float64` lands at `-1.11e-16`; asserts that a real-zero addend
or real-one factor rendered by its own `float64` literal (`+ 0.0`, `* 1.0`,
`/ 1.0`) moves none of the coordinates it observes; and reports the spread where
the bridge does have room (the closing edges). It also measures this row's own
side of the condition: the routine's cell width and height satisfy the pinning
equations above to within 4.5 ulp on every grid it runs (asserted within 64) but
**not identically** — nonzero residual on 229 of 410 grids, and asserted nonzero on
the graded one. That bound is what makes the linear pinning the right description of
the division; that it is not zero is why the precondition itself supplies subterms
of the excluded class.

**Delivery.** The model's precondition additionally obliges the placement to be a
finite computation that always yields its rectangle. This is a property of the
real callee: `get_grid_positions` (`gridspec.py:145`) is straight-line arithmetic
plus two `cumsum`s over grid-dimension-sized arrays, and the gold patch's own
added code is two nested `zip` loops over the subfigure array — no `while`, no
recursion, no data-dependent exit. Without it Nagini proves only partial
correctness, under which a placement that never returns satisfies every extent
clause vacuously; see refinement.md A4d.

## 3. Kind-A reference provenance (checked by G-AX / axiom_check.py)

### 3.1 deep geometry `col_left/col_right/row_top/row_bottom` ↔ `GridSpec.get_grid_positions` (A-reference)
**Callee:** `matplotlib.gridspec.GridSpec.get_grid_positions(fig, raw=False)`
(`lib/matplotlib/gridspec.py:145`). The gold patch calls `gs.get_grid_positions(self)`
on a gridspec the patch constructed with `wspace, hspace, left=0, right=1,
bottom=0, top=1` and the default (equal) ratios. The routine computes, with
`tot_width = right-left = 1`, `tot_height = top-bottom = 1`:

```python
cell_h = tot_height / (nrows + hspace*(nrows-1));  sep_h = hspace*cell_h
cell_heights = [r*norm ...];  sep_heights = [0] + [sep_h]*(nrows-1)
cell_hs = cumsum(interleave(sep_heights, cell_heights))
cell_w = tot_width / (ncols + wspace*(ncols-1));   sep_w = wspace*cell_w
cell_ws = cumsum(interleave(sep_widths, cell_widths))
fig_tops, fig_bottoms = (top - cell_hs).reshape((-1,2)).T
fig_lefts, fig_rights = (left + cell_ws).reshape((-1,2)).T
```

For EQUAL ratios the cumulative sums collapse to the closed form the model pins:
the left edge of column i is `i*(cell_w + sep_w) = i*cell_w*(1+wspace)`, its
right edge `+ cell_w`; the top edge of row j (counted from the top) is
`1 - j*(cell_h + sep_h) = 1 - j*cell_h*(1+hspace)`, its bottom edge `- cell_h`.
With `cw := cell_w`, `ch := cell_h` (each pinned by its normalization equation),
these are exactly `col_left/col_right/row_top/row_bottom`. The grid fills [0,1]:
the last column's right edge is `cell_w*(ncols + wspace*(ncols-1)) = 1`, the
bottom row's bottom is `1 - cell_h*(nrows + hspace*(nrows-1)) = 0`.

This is the **changed placement modeled deeply** — there is no consumed axiom
about `get_grid_positions`. **Soundness check (G-AX):** `axiom_check.py` imports
the standard matplotlib package (the very module the patch uses), runs the REAL
`GridSpec.get_grid_positions(fig)` with `left=0, right=1, bottom=0, top=1` and
the requested `wspace/hspace` over 10 boundary grids (incl. the F2P
`2×3, wspace=1/6, hspace=0.5`; single cell; zero gap; large gaps) + 400 random
grids (`nrows,ncols ∈ [1,6]`, `wspace,hspace ∈ {0}∪[0,2]`), and asserts every
cell's `(left,bottom,right,top)` equals the model closed form to `abs_tol=1e-9`.
It additionally asserts BIT-EXACTNESS at the grid origin (`lefts[0] == 0.0`,
`tops[0] == 1.0`) on every one of those grids, because that is the one place the
ℝ↔`float64` bridge has no tolerance to spend (§2, refinement.md §C.1), and reports
how often the closing edges (`rights[-1]`, `bottoms[-1]`) are bit-exact rather
than asserting that they are. It further evaluates the model's two normalization
equations on the cell width and height the routine itself delivers — the way a
refinement recovers them, as the first column's width and the first row's height —
and asserts the residual stays within 64 ulp of 1 (worst observed 4.5) while being
nonzero on the graded configuration, so both halves of what A3's linear pinning
claims are checked instead of asserted in prose. Exit 0 iff sound. (Validated on host matplotlib 3.10.6 with 0 mismatch; the
routine is unchanged at the instance's 3.7 image, where G-AX re-runs it.)

### 3.2 consumed axioms
None. The `axioms` region of `model.py` is empty (`A-consumed` count = 0); the
proof depends only on the spelled-out geometry, the linear normalization of
`cw/ch`, and the `CellRect` carrier — all expressed directly.

## G-CONF (differential conformance, `conformance_check.py`)

**Shadow.** The `# impl-start`..`# impl-end` region of `model.py`, copied
verbatim as `impl_grid_cell_placement` (there are no contract calls inside the
region, so nothing had to be deleted from it), plus the four `# pure-start`
helpers (`col_left/col_right/row_top/row_bottom`) and the `CellRect` carrier with
their contracts stripped. No transliteration and no restructuring: on nagini the
model IS Python. No `PSeq`/`ToSeq` shim is needed (the region uses no sequences),
and there is no `@ContractOnly` callee to stand in for (§3.2: `A-consumed` = 0).

**Oracle.** The REAL patched repo function, **called**, not transliterated:
`matplotlib.figure.Figure.subfigures` (`lib/matplotlib/figure.py:1543`, the
gap-honouring placement the gold patch adds at body lines 1583-1601) — the same
symbol §1 binds the model to. Driving it in-container needs only `Figure()` +
`.subfigures(nrows, ncols, squeeze=False, wspace=…, hspace=…)`, so the whole
patched path (GridSpec with `left=0, right=1, bottom=0, top=1` →
`get_grid_positions` → `Bbox.from_extents` → `SubFigure._redo_transform_rel_fig`)
runs for real; the §3.1 A-reference is thereby exercised end-to-end rather than
assumed. The script asserts `fig.get_layout_engine() is None` and always passes
both gap arguments, so the patched branch is taken on every call.

**Type bridge (§2 inverted).** Repo `int` counts/indices → the integer-valued
reals the model carries; repo `float` gaps → their exact values; `cw`/`ch` →
the unique reals satisfying the pinning equations
`cw*(ncols+wspace*(ncols-1))==1`, `ch*(nrows+hspace*(nrows-1))==1` (i.e. the
repo's `cell_w`/`cell_h` with `tot_width = tot_height = 1`). Shadow arithmetic
runs over exact rationals (`class Real(Fraction)`) to match
`--float-encoding=real`; every generated tuple is asserted to satisfy each
`Requires` clause exactly before use. The `CellRect` carrier is recovered from
the oracle exactly as the F2P test reads it:
`left = sf.bbox.min[0]/W`, `bottom = sf.bbox.min[1]/H`,
`right = sf.bbox.max[0]/W`, `top = sf.bbox.max[1]/H`, `(W,H) = fig.bbox.max`.

**Inputs.** `SEED = 25960` (pinned module constant). 16-configuration
boundary/sentinel catalogue first — the exact F2P shape (2×3, `wspace=1/6`,
`hspace=0.5`), 1×1, single row, single column, zero gaps (abutting), 1e-9 gaps,
unit gaps, 100.0 gaps, 6×6, 1×12, 12×1 — then seeded fuzz
(`nrows,ncols ∈ [1,6]`, gaps from a 15-value pool ∪ `[0,3)`) to **100 006**
Requires-satisfying cell inputs across 8 221 grid configurations. The input space
is infinite (gaps range over the non-negative reals), so it is sampled, not
enumerated; the impl region is straight-line so branch coverage is total, and the
index/gap boundary classes (`i=0`, `i=ncols-1`, `j=0`, `j=nrows-1`, gap `=0`,
gap `>0`, 1×1) are asserted non-empty at the end.

**Comparison.** `ABS_TOL = 1e-12` on the edges (exact-rational shadow vs float
oracle; worst deviation actually observed 4.44e-16, printed in the report line),
which is 5 orders tighter than the F2P test's `assert_allclose` rtol 1e-7. The
discriminating properties — grid fills `[0,1]²`, a positive requested gap
*strictly* separates consecutive cells, a zero gap makes them abut, and the impl
equals the pure helpers — are checked **exactly** on the rationals, with no
tolerance. Exit 0 iff zero disagreements; last stdout line is a JSON report.

**Failure capability (checked out-of-band on scratch copies, never in the
bundle).** Replacing the shadow with the pre-patch gap-less placement
(`left = i/ncols`) → 280 disagreements, exit 1. Perturbing the row pitch by a
relative 1e-6 (`hspace*0.999999`) → 186 disagreements, exit 1.
