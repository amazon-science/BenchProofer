# refinement.md — astropy__astropy-12907

Maps every op in `implementation_direct_sum` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `let lout := left.length` / `rout := right.length` | `left.shape[0]` / `right.shape[0]` (array branch of `_compute_n_outputs`) | R | `ndarray.shape[0]` ↔ `List.length` of outer list |
| 2 | `let noutp := lout + rout` | `noutp = _compute_n_outputs(left, right)` (array case `lnout+rnout`) | I | sum of output counts; functionally identical |
| 3 | `for i in [0:noutp] do … result := result ++ [row]` | construction of `cleft`/`cright` arrays then `np.hstack`; numpy builds all rows at once, the loop assembles row-by-row | R | numpy block assignment ↔ per-row build; same matrix, total `List`/`ndarray` refinement |
| 4 | `cleftRow := if i < lout then left.getD i [] else zeroRow lin` | `cleft = np.zeros((noutp, left.shape[1])); cleft[:left.shape[0], :left.shape[1]] = left` | R | top `lout` rows = `left`'s rows; rows `≥ lout` = `lin` zeros (zero-padded block) |
| 5 | `crightRow := if lout ≤ i then right.getD (i-lout) [] else zeroRow rin` | `cright = np.zeros((noutp, right.shape[1])); cright[-right.shape[0]:, -right.shape[1]:] = right` | R | **the fixed line** (`= right`, was `= 1`): bottom `rout` rows = `right`'s rows; rows `< lout` = `rin` zeros |
| 6 | `cleftRow ++ crightRow` | `np.hstack([cleft, cright])` | I | per-row horizontal concatenation |

Every op is R or I. **No A-tagged rows** — the combinator is modeled deeply
(element-wise block placement), so its constituent operation (block assignment)
is spelled out, not axiomatized. `_compute_n_outputs` inlined (op #2).

Because the impl region is entirely R/I (no A-tagged content), `conf_skip =
false`: G-CONF mechanically differential-tests this impl against the patched
`_cstack` array/array branch.

## Prepatch (the real bug)

The pre-patch impl replaces op #5's `right.getD (i-lout) []` with
`List.replicate rin 1` — exactly `cright[...] = 1` (fill the bottom-right block
with all-ones) instead of `= right` (copy the sub-matrix). On any nested
`right` whose own matrix is not all-ones (e.g. a diagonal `Linear1D &
Linear1D` block), this fabricates spurious correlations — the bug in the issue.
The discriminating clause is `problem_spec`'s third conjunct
(`result.getD i [] = zeroRow lin ++ right.getD (i-lout) []`): the prepatch
produces `zeroRow lin ++ List.replicate rin 1 ≠ zeroRow lin ++ right.getD …`
whenever some `right` row contains a `0`, so `correct_direct_sum` is unprovable
for the prepatch impl (G-DIFF).
