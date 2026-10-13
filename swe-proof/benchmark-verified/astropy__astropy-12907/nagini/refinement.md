# refinement.md — astropy__astropy-12907

The operation-by-operation correspondence between `model.py`'s implementation
(the `parallel_dependency_matrix` impl region, plus the deep pure models
`expected_row` / `zeros` it consumes) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated `== real callee` by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed function — `_cstack` (`astropy/modeling/separable.py:219`)

Gold hunk (the single changed line, in the `right`-is-ndarray branch):

```
         cright = np.zeros((noutp, right.shape[1]))
-        cright[-right.shape[0]:, -right.shape[1]:] = 1
+        cright[-right.shape[0]:, -right.shape[1]:] = right

     return np.hstack([cleft, cright])
```

`model.py` builds the same stacked matrix one row at a time. For each output
row `i`:
- upper rows (`i < lr`): `row = left[i] + zeros(rc)` — the `left` row followed
  by the empty right padding;
- lower rows (`i >= lr`): `row = zeros(lc) + right[i - lr]` — the empty left
  padding followed by the **actual** `right` row (the fix).

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `left, right : PSeq[PSeq[int]]`, extents `lr, lc, rr, rc` | `_cstack(left, right)` with `left`/`right` the ndarray coord matrices and shapes `left.shape`/`right.shape` | R | ndarray ↔ `PSeq[PSeq[int]]`, `.shape[0/1]` ↔ extents (mapping.md §2). |
| A2 | `noutp = lr + rr` | `noutp = _compute_n_outputs(left, right) = left.shape[0] + right.shape[0]` (line 234) | R + I | `_compute_n_outputs` on two ndarrays returns the sum of row counts (separable.py:118-127); identical integer. |
| A3 | upper row `left[i] + zeros(rc)` (the `cleft` block + zero right pad) | `cleft = np.zeros((noutp, left.shape[1])); cleft[:left.shape[0], :left.shape[1]] = left` then the left half of `np.hstack` (lines 239-240, 247) | R + I | the `left`-is-ndarray branch is **unchanged** by the patch; `cleft` is `left` in its top `lr` rows and 0 below, width `lc`; its contribution to row `i<lr` is `left[i]`, and the right half of that row is the `rc`-wide zero pad from `cright`. Type-refined array→PSeq, otherwise identical. |
| A4 | lower row `zeros(lc) + right[i - lr]` — the left zero pad then the **actual** `right` row | `cright = np.zeros((noutp, right.shape[1])); cright[-right.shape[0]:, -right.shape[1]:] = right` then the right half of `np.hstack` (lines 244-245 post-fix, 247) | R + I | **the fix.** `cright` is 0 in its top `lr` rows and equals `right` in its bottom `rr` rows (slice `[-rr:, -rc:]` with `rc == cright.shape[1]` spans the full width); row `i>=lr` of the result is the `lc`-wide zero pad from `cleft` then `right[i-lr]`. The assignment copies the operand `right` into the block — exactly `zeros(lc) + right[i-lr]`. Type-refined array→PSeq, otherwise identical. |
| A5 | `result = result + PSeq(row)` (outer fold over rows) | `np.hstack([cleft, cright])` followed by the implicit row stacking of the two `noutp`-row blocks | R + I | `np.hstack` concatenates `cleft` and `cright` column-wise; row `i` of the hstack is `cleft[i] ++ cright[i]`, which equals A3/A4's `row`. Building the result row-by-row and concatenating rows (`PSeq` outer concat) is the same matrix. |

## B. The discriminating delta (G-DIFF)

The bug is the constant fill `= 1`: the pre-patch code sets the entire
lower-right block to `1`, so every lower output appears to depend on every
lower input — the spurious off-diagonal dependence the problem statement
reports for `m.Pix2Sky_TAN() & cm`. The fix copies `right`, preserving its
(diagonal / independent) structure.

`model_prepatch.py` reproduces the bug: its lower rows build a constant
`1`-block (an inner loop appending `PSeq(1)` `rc` times) in place of
`right[i - lr]`, giving `row = zeros(lc) + ones(rc)`. Against the **byte-
identical** frozen spec it **fails** the impl assertion / postcondition
`row == expected_row(left, right, lr, lc, rr, rc, i)`
(`expected_row` for a lower row is `zeros(lc) + right[i-lr]`). Whenever `right`
contains a 0 entry — i.e. whenever the nested right child has any independent
output, which is exactly the F2P scenario — `ones(rc) != right[i-lr]`, so the
spec senses the change. This is the single independently-fixed behaviour, so
one `model_prepatch.py` suffices.

## C. No kind-3 (unexpressible-changed-op) steps; no axioms

Every step above is R or I. The changed operation — replacing the constant
block fill with a copy of the operand — is modeled **deeply** (`expected_row`'s
`zeros(lc) + right[i-lr]` consumed in the verified loop), not hidden behind an
axiom. There is **no `@ContractOnly` axiom**: the patched hunk calls only
`np.zeros` / slice-assignment / `np.hstack`, all pure block placement captured
directly by the `PSeq` concatenation model. Consequently there is no A-consumed
and no A-reference row; `axiom_check.py` validates the deep block-placement
model against a faithful numpy re-implementation of the gold `_cstack` branch
(G-AX as a model-fidelity check, since there is no library callee to over-
approximate).

## D. verify(model) ⇒ resolved

`parallel_dependency_matrix` verifies only if every result row equals
`expected_row`, whose lower rows copy the actual `right` row (A4) — the fix.
By the R-refinement (ndarray ↔ `PSeq[PSeq[int]]`, shapes ↔ extents, `np.hstack`
↔ per-row concat, integer 0/1 ↔ nonzero test) the verified row layout is
exactly the matrix `np.hstack([cleft, cright])` produced by the patched
`_cstack`, and `separability_matrix` booleanises it (`!= 0 → True`)
identically for both carriers. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The only trust point is refinement fidelity (this
document, G-EQ); there is no axiom-soundness trust point because no callee is
axiomatized.
