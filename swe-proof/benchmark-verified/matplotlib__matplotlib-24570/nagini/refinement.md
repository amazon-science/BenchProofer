# refinement.md — matplotlib__matplotlib-24570

The operation-by-operation correspondence between `model.py`'s implementation
(the `aligned_offsets` loop + the deep `offset_for` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses the axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The alignment site — `_get_aligned_offsets` (`lib/matplotlib/offsetbox.py:130`)

Gold hunk (`offsetbox.py:169-174`):
```
-    elif align in ["left", "top"]:
+    elif align in ["left", "bottom"]:
         descent = 0.
         offsets = [d for h, d in hd_list]
-    elif align in ["right", "bottom"]:
+    elif align in ["right", "top"]:
         descent = 0.
         offsets = [height - h + d for h, d in hd_list]
```

| # | model.py impl op (`aligned_offsets` / `offset_for`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `heights, descents : List[int]` (×2) | `hd_list : list[(h, d)]` of floats | R | one `(h,d)` ↔ `(heights[i], descents[i])`; uniform ×2 integer scale (mapping.md §2). |
| A2 | `total : int` (×2) | `height` (recomputed `max(h)` when `None`) | R | the F2P packers pass `self.height is None`; `total = 2·max(h)` (mapping.md §2). |
| A3 | `code : int` ∈ {0,1,2,3} | `align : str` (six names) | R | the four offset-formula classes; `{"left","bottom"}→LOWER`, `{"right","top"}→UPPER` (the post-patch grouping). `str` is banned in Nagini. |
| A4 | the per-box result `Result()[i] == offset_for(heights[i], descents[i], total, code)`, computed by the verified loop | the per-branch `offsets = [...]` list comprehension | A-reference | the changed offset operation is modeled **deeply**: `offset_for` (the spelled-out per-anchor arithmetic in the `pure` region) and the verified loop in `aligned_offsets` ARE the offset computation. There is no consumed axiom. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the post-patch `_get_aligned_offsets` on boundary + 20000 fuzz layouts × 6 anchors and asserts `offset_for == offsets` (un-scaled). (mapping.md §3.1) |
| A5 | the LOWER branch `off = 2*d` ; the UPPER branch `off = 2*(total-h)+2*d` | `offsets = [d …]` (now `{"left","bottom"}`) ; `offsets = [height-h+d …]` (now `{"right","top"}`) | I (under R) | identical arithmetic up to the ×2 scale (A1). The grouping that decides which class an anchor belongs to is A3; with `bottom→LOWER` and `top→UPPER` the model's LOWER formula = the gold's `[d]` branch and the model's UPPER formula = the gold's `[height-h+d]` branch. |
| A6 | the BASELINE branch `off = 0` ; the CENTER branch `off = (total-h)+2*d` | `offsets = [0. …]` ; `offsets = [(height-h)*.5+d …]` | I (under R) | unchanged by the patch; carried for skeleton fidelity. CENTER's `·0.5` ↔ `/2` is exact under the ×2 scale (mapping.md §2). |

The discriminating content of the change — the anchor names `bottom` and `top`
moving between the low-edge (`[d]`) and high-edge (`[height-h+d]`) offset
classes — lives in `CODE_LOWER`/`CODE_UPPER` (model) ⇔ the `align in [...]`
membership lists of the two `elif` branches (real). The pre-patch put `top` in
the low-edge class and `bottom` in the high-edge class; `model_prepatch.py`
reproduces that by **swapping the LOWER and UPPER branch bodies** and **fails**
the postcondition `Result()[i] == offset_for(...)` (the loop invariant on the
LOWER/UPPER branches), which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the per-anchor offset selection/arithmetic — is modeled **deeply**
(the spelled-out `offset_for` consumed in `aligned_offsets`, step A4, an
**A-reference**), not hidden behind an axiom about the function under change:
there is **no consumed `@ContractOnly` axiom** in this bundle (the `axioms`
region is empty). The only out-of-band trust point is the A-reference: the
deep model `offset_for` is validated equal to the real `_get_aligned_offsets`
by G-AX.

## C. verify(model) ⇒ resolved

`aligned_offsets` verifies only if its output equals, element-wise, the exact
per-anchor offset `offset_for` (A4), with the low-edge class returning the
box's own descent and the high-edge class returning the track-excess + descent
(the explicit LOWER/UPPER postcondition clauses). By R (the ×2 integer scale
and the `align`→`code` grouping, A1–A3) the verified offsets equal the gold
patch's `offsets` list on the tested layouts; by G-AX the deep model
`offset_for` equals the real `_get_aligned_offsets` (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement — and the gold patch resolves (G-RESOLVE). The single trust
point is exactly the A-reference soundness of PLAN §1.1 (there is no consumed
axiom); refinement fidelity is this document (G-EQ).
