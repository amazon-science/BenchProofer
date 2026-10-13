# refinement.md — pydata__xarray-7233

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `coordsToKeep` `do` block and the deep `keptCoordNames` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The coordinate re-selection site — `Coarsen.construct` (`xarray/core/rolling.py:973`)

Gold hunk:
```
- should_be_coords = set(window_dim) & set(self.obj.coords)
+ should_be_coords = (set(window_dim) & set(self.obj.coords)) | set(
+     self.obj.coords
+ )
  result = reshaped.set_coords(should_be_coords)
```

| # | Solution.lean impl op (`coordsToKeep`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `requestedDims : List String` | `set(window_dim)` (the reshaped-dimension names) | R | name set ↔ `List String` (mapping.md §2). G-CONF bridges via membership. |
| A2 | param `coordNames : List String` | `set(self.obj.coords)` (prior coordinate names) | R | name set ↔ `List String` (mapping.md §2). |
| A3 | `common := requestedDims.filter (fun k => coordNames.contains k)` | `set(window_dim) & set(self.obj.coords)` | I | set intersection ↔ filter-by-membership (mapping.md §2); concrete, transliterated by G-CONF. |
| A4 | `result := common ++ coordNames` | `(set(window_dim) & set(self.obj.coords)) | set(self.obj.coords)` | I | set union ↔ membership-union (realised as `++`); concrete, transliterated by G-CONF. The deep model `keptCoordNames` IS this expression. |
| A5 | `out` returned (`List String`), spec `∀ k, k ∈ out ↔ k ∈ coordNames` | `result = reshaped.set_coords(should_be_coords)` then the result's `.coords` | A-reference | `set_coords` installs the chosen name-set as the result's coordinate names; it is an identity on the coordinate-name set on the rebuilt container (mapping.md §3.1). The equality "result's coordinate names == the chosen set" is the A-reference G-AX validates against the real callee. |

Discriminating content of the change — a prior coordinate whose name is NOT a
reshaped dimension (the issue's `day`) must remain a coordinate — lives in the
`++ coordNames` step (model) ⇔ the `| set(self.obj.coords)` union (real). The
pre-patch computed only `set(window_dim) & set(self.obj.coords)`, dropping such
names; `Solution_prepatch.lean` reproduces that (`result := common`) and **fails**
`∀ k, k ∈ out ↔ k ∈ coordNames` on the reverse direction for any prior coordinate
absent from `requestedDims` (G-DIFF).

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely *changed* — the
coordinate-name re-selection set expression — is modeled **deeply** (the
spelled-out `keptCoordNames` / the `filter` + `++` of steps A3–A4, an I + I), not
hidden behind an axiom about the function under change. The only callee fact is
the A-reference at A5 (`set_coords`, an UNCHANGED neighbour), validated by G-AX.
There are no consumed axioms.

## C. verify(Solution) ⇒ resolved

`coordsToKeep` verifies only if its output's membership set equals the prior
coordinate-name set (`∀ k, k ∈ out ↔ k ∈ coordNames`, A3–A4 / `keptCoordNames`).
By R (name set ↔ `List String`) and the A-reference at A5 (`set_coords` is an
identity on coordinate names), the verified re-selection makes the patched
`construct`'s result carry exactly the prior coordinate names — which is what the
F2P test `test_coarsen_construct_keeps_all_coords` asserts
(`list(da.coords) == list(result.coords)`). By G-CONF the R/I transliteration of
the set expression agrees with `patch.diff`'s real `construct().coords` over the
fuzzed configs; by G-AX the `set_coords` identity holds on the real callee.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
