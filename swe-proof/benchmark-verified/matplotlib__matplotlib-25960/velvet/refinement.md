# refinement.md — matplotlib__matplotlib-25960

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`axisCellExtents` `do` block, the deep `axisExtents`/`cellPitch`/`cellSize`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A** (axiomatized callee — **A-consumed**
where the proof uses the axiom's `ensures`, **A-reference** where a deep model is
validated == the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ** / **G-AX**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The placement site — `Figure.subfigures` (`lib/matplotlib/figure.py:1544`)

Gold hunk (behavioural part; the docstring hunk is non-semantic):
```
  gs = GridSpec(..., width_ratios=..., height_ratios=...,
+               left=0, right=1, bottom=0, top=1)
  ...
+ if self.get_layout_engine() is None and (wspace is not None or hspace is not None):
+     bottoms, tops, lefts, rights = gs.get_grid_positions(self)
+     for sfrow, bottom, top in zip(sfarr, bottoms, tops):
+         for sf, left, right in zip(sfrow, lefts, rights):
+             bbox = Bbox.from_extents(left, bottom, right, top)
+             sf._redo_transform_rel_fig(bbox=bbox)
```

| # | Solution.lean impl op (`axisCellExtents`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `n : Nat`, `s : Rat` | `nrows`/`ncols` and `hspace`/`wspace` of `subfigures` | R | `int ↔ Nat`, gap `float ↔ Rat` (mapping.md §2). One axis at a time: columns ↔ `(ncols, wspace)`, rows ↔ `(nrows, hspace)`. |
| A2 | `cellSize n s = 1/(n + s·(n-1))`, `cellPitch n s = cellSize·(1+s)` | `cell_w/cell_h` and the `cell+sep` stride inside `gs.get_grid_positions(self)`, evaluated with `left=0,right=1,bottom=0,top=1` and equal ratios | A-reference + I | the changed placement is modeled **deeply**: `cellSize`/`cellPitch`/`axisExtents` ARE the reduced grid-position arithmetic (mapping.md §3.1). The fold ops (`.map`, `*`, `+`) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `get_grid_positions` is the **A-reference** G-AX validates. No consumed `get_grid_positions` axiom. |
| A3 | `out = axisExtents n s` — the `n` ordered `(low, high)` cell extents, the per-index expansion of `range n` | `lefts/rights` (and, reversed, `bottoms/tops`) the patch reads from `get_grid_positions`, packed via `Bbox.from_extents` and applied by `_redo_transform_rel_fig(bbox=…)` | A-reference + R + I | the extent **list** is the modeled result (I/A-reference). `Bbox.from_extents` + `_redo_transform_rel_fig(bbox=…)` only carry the four numbers into `bbox_relative` — identity on extent content (**R**, mapping.md §2). The row axis is `axisExtents nrows hspace` **reversed** (top-origin indexing) — an order-only **R**. |
| A4 | `out.length = n` (exactly `n` extents) | `sfarr` has `nrows×ncols` cells; `zip` assigns one extent pair per row/col | R | the per-axis count `n` ↔ `ncols` (resp. `nrows`); the 2-D bbox of cell `(j,i)` is `(lefts[i],bottoms[j],rights[i],tops[j])`, the product of the two per-axis extent lists. |

Discriminating content of the change — a positive gap `s` must *separate*
consecutive cells (`high i < low (i+1)` for `s > 0`), versus the pre-patch even
gap-free tiling where cells abut — lives in `cellPitch`'s `(1+s)` factor:
`axisExtents n s` spaces the cells, `evenSize = 1/n` does not. The prepatch
(mapping.md §1) reproduces the buggy even split (`1/n`, ignoring `s`) and
**fails** `out = axisExtents n s` whenever `s > 0` (G-DIFF; the residual goal
`∀ a<n, a·(1/n) … = a·cellPitch …` is false for `s ≠ 0`).

## B. No consumed axioms

There is **no `axiom`** in this bundle. The one operation that genuinely changed
— the spacing-aware cell placement — is modeled **deeply** (`axisExtents`, an
A-reference validated == the real `get_grid_positions` by G-AX), not hidden
behind an axiom about the function under change. Per directive 7 there are no
dead/over-claimed axioms to audit.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The changed placement is expressible as an
exact rational closed form (mapping.md §2 float-band note), so it is modeled
directly rather than declared BLOCKED.

## D. verify(Solution) ⇒ resolved

`axisCellExtents` verifies only if its output equals `axisExtents n s` — the
spacing-aware extents with the `(1+s)` pitch (A2-A3) — and has exactly `n`
entries (A4). By R (`int↔Nat`, `float↔Rat`, the `Bbox`/`_redo_transform_rel_fig`
identity, the row-axis reversal, and the fixed `w×h` affine) the verified extents
equal what the patched `subfigures` writes into each subfigure's
`bbox_relative`, hence the absolute `bbox.min/.max` the F2P test reads. By G-AX
the deep model `axisExtents` equals the real `get_grid_positions` under the
patch-supplied margins (A-reference); by G-CONF the R/I transliteration agrees
with the reduced grid-position arithmetic on ≥10⁵ inputs. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE).
Trust points are exactly the two of plan §1.1: the A-reference soundness (G-AX)
and refinement fidelity (this doc, G-EQ + G-CONF).
