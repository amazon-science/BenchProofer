# refinement.md — pydata__xarray-4094

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `toComponents` `do` block plus the `sliceCoords`/`expectedComponents` deep
models) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** where the proof uses an
axiom's `ensures`, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference leg + narrative are audited by **G-AX** / **G-EQ**. Claim:
any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The component-extraction site — `to_unstacked_dataset()` (`xarray/core/dataarray.py:1964`)

Gold hunk:
```
  for k in variables:
-     data_dict[k] = self.sel({variable_dim: k}).squeeze(drop=True)
+     data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)
```

| # | Solution.lean impl op (`toComponents`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `vars : List String` | `variables = idx.levels[level_number]` | R | the ordered component labels ↔ `List String` (mapping.md §2). Iteration order preserved. |
| A2 | parameter `selDim : String` | `dim` — the indexed stacked dimension (`to_unstacked_dataset(self, dim, ...)`) | R | the residual scalar coordinate left by the point-selection is named after the indexed dimension `dim`; `dim` ↔ `String` (mapping.md §2). |
| A3 | parameter `sampleCoords : List String`; precondition `selDim ∉ sampleCoords` | the shared sample coordinates carried by every component (the `sample_dims` of `to_stacked_array`); `variable_dim` is the *stacking* level, distinct from any sample coordinate | R | the shared coordinate names ↔ `List String`; the selector level is by construction not one of the sample coordinates, so `selDim ∉ sampleCoords` holds for every real input (mapping.md §2). |
| A4 | the `while` loop building `result`, one entry per label: `(k, sliceCoords selDim sampleCoords false) :: result` | `for k in variables: data_dict[k] = self.sel({variable_dim: k}, drop=True).squeeze(drop=True)` | A-reference + I | the component-extraction op whose behaviour the change toggles is modeled **deeply**: `sliceCoords … keep:=false` IS the `drop=True` extraction's coordinate-name result (the selector label discarded). The loop/cons/`map`/membership ops are **I** (concrete, transliterated by G-CONF); the equality of `sliceCoords … false` to the real `sel(..., drop=True).squeeze(drop=True)` coordinate set is the **A-reference** G-AX validates. mapping.md §3.1. |
| A5 | `ensures out.map Prod.fst = vars` | `data_dict` keyed by every `k in variables` | I + R | the dict key set ↔ the labels in order; no label dropped/duplicated (`expectedComponents_keys`). |
| A6 | `ensures ∀ p ∈ out, selDim ∉ p.2` | `Dataset(data_dict)` is conflict-free (no `MergeError`) | A-reference | reassembly succeeds iff no two components carry a conflicting value for the same coordinate name; the residual `selDim` scalar coordinate is exactly that conflict source. `drop=True` removes it; G-AX confirms `Dataset(data_dict)` is then `identical` to the original. mapping.md §3.1. |

Discriminating content of the change — whether the transient selector label
`selDim` survives extraction — lives in `sliceCoords selDim sampleCoords keep`
(`keep=false` discards, `keep=true` retains). The pre-patch (`drop=False`,
modeled `keep=true`) leaves `selDim` on every component;
`Solution_prepatch.lean` reproduces that and **fails** the postcondition
(specifically the loop invariant goal `sliceCoords selDim sampleCoords true =
sampleCoords`, which is false because the result is `sampleCoords ++ [selDim]`)
(G-DIFF).

## B. No second site

The gold patch changes a single line. There is exactly one modeled function and
one independently-observable fixed behaviour (the single-dim roundtrip of
`FAIL_TO_PASS`), so one `Solution_prepatch.lean`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the `drop` flag of the per-component selection — is modeled **deeply** (the
spelled-out `sliceCoords` with its `keep` parameter, step A4/A6, an
A-reference + I), not hidden behind an axiom about the function under change.
There is **no consumed axiom**.

## D. verify(Solution) ⇒ resolved

`toComponents` verifies only if every extracted component carries exactly
`sampleCoords` and never the transient `selDim` (A4/A6) and the labels are
preserved in order (A5). By R (`variables`/`variable_dim`/sample-coords ↔ Lean
strings) the verified extraction equals
`self.sel({variable_dim:k}, drop=True).squeeze(drop=True)` on each label; by
G-AX the deep model `sliceCoords … false` equals the real extractor's
coordinate set (A-reference) and `Dataset(data_dict)` is then `identical` to the
original (so `assert_identical(unstacked, data)`, the F2P assertion, holds); by
G-CONF the R/I transliteration agrees with `patch.diff`'s behaviour over the
fuzzed single- and multi-dim shapes. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). The one trust point is
deep-model fidelity (G-AX) + refinement fidelity (this doc, G-EQ + G-CONF).
