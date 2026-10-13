# refinement.md — astropy__astropy-12907

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `combineParallel` `do` block + the `blockDiag`/`widenRight`/`widenLeft`
pure models) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — none in this bundle), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (mapping.md §3). Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the array/array branch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The fixed site — `_cstack()` array/array branch (`separable.py:244-245`)

Gold hunk:
```
  cright = np.zeros((noutp, right.shape[1]))
- cright[-right.shape[0]:, -right.shape[1]:] = 1
+ cright[-right.shape[0]:, -right.shape[1]:] = right

  return np.hstack([cleft, cright])
```

The model assembles the *whole* block-diagonal result of the array/array
branch (`np.hstack([cleft, cright])` with both blocks filled), since that is
the observable output `_cstack` returns and what the F2P tests compare.

| # | Solution.lean impl op (`combineParallel`) | patch.diff / branch op | tag | justification |
|---|---|---|---|---|
| A1 | params `left right : List (List Int)` | `left`, `right` ndarrays (coord matrices) of the array/array branch | R | 2-D 0/1 ndarray ↔ `List (List Int)` (mapping.md §2). G-CONF bridges via `M ↔ M.tolist()`. |
| A2 | `lc`/`rc : Nat` with `require ∀ r ∈ left, r.length = lc` / `… right … = rc` | `left.shape[1]` / `right.shape[1]` | R | column widths; rectangularity of a real ndarray makes the `require` always hold (mapping.md §2). |
| A3 | `upper := left.map (widenRight rc)` — each left row followed by `rc` zeros | `cleft = np.zeros((noutp, lc)); cleft[:lr,:lc] = left`, then the left half of `hstack` (columns 0..lc-1 of the upper `lr` rows = left; the right `rc` columns of those rows = 0) | I | concrete zero-padding; this branch of the fix was already correct pre-patch (the symmetric `cleft` assignment). Transliterated by G-CONF. |
| A4 | `lower := right.map (widenLeft lc)` — `lc` zeros then each right row | `cright = np.zeros((noutp, rc)); cright[-rr:,-rc:] = right`, then the right half of `hstack` (the lower `rr` rows: left `lc` columns = 0, right `rc` columns = **right**) | I | concrete zero-padding carrying **each right row's own entries** — this is exactly the gold change `= right` (not the buggy constant `= 1`). Transliterated by G-CONF. |
| A5 | `return upper ++ lower` | `np.hstack([cleft, cright])` viewed row-wise: upper `lr` rows are `[left | 0]`, lower `rr` rows are `[0 | right]` | I + R | `np.hstack` of the two zero-extended blocks equals, row by row, the vertical concatenation `upper ++ lower` (mapping.md §2). The combined row count `noutp = lr + rr` (`_compute_n_outputs`) is implicit in `++`. |

Discriminating content of the change — the lower-right block carries the
**actual `right` matrix**, not a constant all-ones fill — lives in
`widenLeft lc rrow = replicate lc 0 ++ rrow` (model) ⇔ `cright[-rr:,-rc:] =
right` (real). The pre-patch `= 1` overwrites that block with ones;
`Solution_prepatch.lean` reproduces it (`fun _ => replicate lc 0 ++ replicate
rc 1`) and **fails** `out = blockDiag left right lc rc` (G-DIFF) on any input
whose right rows are not uniformly all-ones — e.g. a diagonal `sh1 & sh2`
block, the exact nested structure the F2P tests assert.

## B. No kind-A (axiomatized-callee) steps; no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — filling the
lower-right block with the right operand's own rows instead of a constant — is
modeled **concretely** (the spelled-out `widenLeft`/`blockDiag`, steps A4/A5),
not behind an axiom about the function under change. There is no consumed axiom
and no A-reference (mapping.md §3): the fixed branch uses only numpy primitives,
so `conf_skip=false` and G-CONF carries the full mechanical weight.

## C. verify(Solution) ⇒ resolved

`combineParallel` verifies only if its output equals the exact block-diagonal
assembly `blockDiag left right lc rc`, whose lower block is `right`'s own rows
zero-padded on the left (A4) — not a constant fill. By R (`ndarray ↔ List (List
Int)`, `shape[1] ↔ row length`) the verified assembly equals the array/array
branch of `np.hstack([cleft, cright])` with `cright[-rr:,-rc:] = right`, i.e.
the patched `_cstack`, on every rectangular 0/1 input; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (seed
12907), 0 disagreements. There are no axioms to trust (mapping.md §3).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point of plan §1.1 that applies is refinement fidelity (this doc +
G-CONF); axiom soundness (G-AX) is vacuous here.
