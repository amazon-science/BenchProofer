# refinement.md — scikit-learn__scikit-learn-13135

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `computeBoundaries` `do` block, the `mids` fold, and the `asc` deep model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The bin-edge construction — `KBinsDiscretizer.fit`, kmeans branch (`sklearn/preprocessing/_discretization.py:173-177`)

Gold hunk:
```
  centers = km.fit(column[:, None]).cluster_centers_[:, 0]
+ # Must sort, centers may be unsorted even with sorted init
+ centers.sort()
  bin_edges[jj] = (centers[1:] + centers[:-1]) * 0.5
  bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]
```

| # | Solution.lean impl op (`computeBoundaries`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `centers : List Rat` | `centers = km.fit(...).cluster_centers_[:, 0]` (the value flowing in) | R | KMeans is upstream and **unchanged** by the patch; its 1-D output is taken as a free input. `ndarray` of finite `float64` ↔ `List Rat` (mapping.md §2). |
| A2 | parameters `lo hi : Rat` | `col_min, col_max` | R | column endpoints; `float64` scalar ↔ `Rat` (mapping.md §2). |
| A3 | `let ys := asc centers` (ascending reorder) | `centers.sort()` (the line the patch ADDS) | A-reference | the changed reordering op is modeled **deeply**: `asc = mergeSort (· ≤ ·)` (pure region) IS the ascending reorder. No consumed sort axiom. The equality of that deep model to the real `numpy.ndarray.sort` is the **A-reference** G-AX validates (mapping.md §3.1). |
| A4 | the backward `while` fold building `result = mids ys` (adjacent-pair midpoints) | `(centers[1:] + centers[:-1]) * 0.5` | I | concrete, transliterated by G-CONF. `mids` peels one midpoint per loop step (the `mids_drop_step` fold lemma); exact `/2` ↔ float `*0.5` (mapping.md §2). |
| A5 | `return lo :: (result ++ [hi])` | `bin_edges[jj] = np.r_[col_min, bin_edges[jj], col_max]` | I | list `++`/cons ↔ `np.r_` concatenation (mapping.md §2). |

Discriminating content of the change — the **ascending reorder before pairing**
— lives in `out = boundaries centers lo hi`, whose midpoints are taken over
`asc centers` (A3). Without the reorder the midpoints are taken over the raw,
possibly-unordered representatives and the bracketed sequence is non-monotone,
which the issue reports as fatal to the downstream binning step.
`Solution_prepatch.lean` reproduces exactly that (the impl sets `ys := centers`,
omitting `asc`) and **fails** the postcondition on the clause
`result_1 = mids (asc centers)` — provably false whenever `centers` is unsorted
(G-DIFF). The loop body of the prepatch closes; only this spec-vs-buggy-output
divergence remains unprovable, pinpointing the discriminator.

## B. No consumed axioms

The `axioms` region of `Solution.lean` is empty. The sole kind-A obligation is
the **A-reference** `asc` (step A3), a deep model validated == the real
`numpy.ndarray.sort` by G-AX. There is no dead `axiom` the proof never uses, and
nothing about the function under spec or the operation the patch changes is
axiomatized away — the changed op (the reorder) is spelled out, not hidden.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
inserting the ascending reorder — is modeled **deeply** (the `asc` sort + the
spelled-out `mids` fold over it), not behind an axiom about the function under
change. Floats are modeled as `Rat` because this is an **order-only** fix: the
patch changes which representatives are paired (their order), not any rounding;
`Rat` is exact and order-faithful, so no IEEE behavior is approximated away.

## D. verify(Solution) ⇒ resolved

`computeBoundaries` verifies only if its output equals the exact bracketed
adjacent-midpoint sequence of the **ascending-reordered** representatives (A3 +
A4 + A5). By R (`ndarray ↔ List Rat`, scalar `↔ Rat`, `np.r_ ↔ ++`) the verified
computation equals the patched kmeans-branch fragment on the tested inputs; by
G-AX the deep model `asc` equals the real `numpy.ndarray.sort` (A-reference); by
G-CONF the R/I transliteration of the `mids` fold + bracketing agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the one
audited callee — and the gold patch resolves (G-RESOLVE). The single trust point
is A-reference soundness (G-AX, `asc == numpy.sort`); refinement fidelity is
mechanically checked (this doc, G-EQ + G-CONF).
