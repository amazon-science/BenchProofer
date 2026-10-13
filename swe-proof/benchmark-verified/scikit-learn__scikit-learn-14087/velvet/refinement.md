# refinement.md — scikit-learn__scikit-learn-14087

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `recordClassResult` `do` block and the pure decisions `chooseCoef` /
`chooseAux`) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The two changed decisions — `LogisticRegressionCV.fit`, no-refit branch

Gold hunks (`sklearn/linear_model/logistic.py`):

```
# behavior 1 — coefficient selection (line 2173)
-                if self.multi_class == 'ovr':
+                if multi_class == 'ovr':
                     w = np.mean([coefs_paths[i, best_indices[i], :] ...
                 else:
                     w = np.mean([coefs_paths[:, i, best_indices[i], :] ...

# behavior 2 — auxiliary append (lines 2183-2184)
-                best_indices_l1 = best_indices // len(self.Cs_)
-                self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
+                if self.penalty == 'elasticnet':
+                    best_indices_l1 = best_indices // len(self.Cs_)
+                    self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))
+                else:
+                    self.l1_ratio_.append(None)
```

| # | Solution.lean impl op (`recordClassResult`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `perClassEffective : Bool` | the resolved local `multi_class == 'ovr'` test, `:2173` post-fix | R | `str`-equality on the resolved strategy ↔ `Bool` (mapping.md §2). The resolver `_check_multi_class` is unchanged; only its already-computed boolean reaches the decision. |
| A2 | param `perClassRequested : Bool` | the raw `self.multi_class == 'ovr'` test, `:2173` pre-fix | R | `str`-equality on the raw attribute ↔ `Bool`. Present only so the spec can pin that selection uses A1, not A2; the gold patch *removes* A2 from the decision. |
| A3 | params `coefByPerClass`, `coefByJoint : Coef` | the two `np.mean([...], axis=0)` read-outs, `:2174-2175` / `:2177-2178` | R | each fitted coefficient vector ↔ `List Rat` (mapping.md §2). Both read-outs are produced by **unchanged** code; the fix selects between them, so they are free inputs carried by opaque tags in G-CONF. |
| A4 | `out.1 = chooseCoef perClassEffective coefByPerClass coefByJoint` (impl: `if perClassEffective then coefByPerClass else coefByJoint`) | the `if multi_class == 'ovr': w = <per-class> else: w = <joint>` selection, `:2173-2178` post-fix | I | the post-fix two-way selection on the resolved flag, transliterated concretely (an `if/else` over `Bool`). G-CONF differential-tests it against the patched selection. |
| A5 | param `auxActive : Bool` | the `self.penalty == 'elasticnet'` test, `:2183` post-fix | R | penalty-mode equality ↔ `Bool` (mapping.md §2). The new guard the patch adds. |
| A6 | param `auxValue : Rat` | `np.mean(l1_ratios_[best_indices_l1])`, `:2184` | R | the averaged auxiliary scalar ↔ `Rat` (mapping.md §2, DECISIONS float note). Computed by unchanged arithmetic; a free input. |
| A7 | `out.2 = chooseAux auxActive auxValue` (impl: `if auxActive then some auxValue else none`) | the guarded `if self.penalty == 'elasticnet': append(np.mean(...)) else: append(None)`, `:2183-2188` post-fix | I | the post-fix guarded record, transliterated concretely. `some auxValue` ↔ `append(<averaged value>)`; `none` ↔ `append(None)`. G-CONF differential-tests it against the patched append. |

Discriminating content of behavior 1 — selection by the **effective** strategy
(`perClassEffective`), not the **requested** one (`perClassRequested`) — lives in
`out.1 = chooseCoef perClassEffective ...`. `Solution_prepatch.lean` reproduces
the bug (selects by `perClassRequested`) and **fails** on that clause (the two
flags disagree exactly when `'auto'` resolves to the per-class layout — the
issue's IndexError) (G-DIFF).

Discriminating content of behavior 2 — record `none` outside the auxiliary mode —
lives in `out.2 = chooseAux auxActive auxValue`. `Solution_prepatch_2.lean`
reproduces the bug (records `some auxValue` unconditionally) and **fails** on that
clause (the divergence at `auxActive = false`, i.e. the non-elastic-net penalties
the three F2P `*-l2` cases use) (G-DIFF).

## B. No kind-A (axiom) steps

This bundle declares **no axioms and no deep-model references**. The two changed
decisions consume only values produced by **unchanged** surrounding code
(`np.mean`, NumPy indexing, `_check_multi_class`), which are taken as free inputs
(mapping.md §3). There is no unchanged repo callee *inside* the modeled decisions
whose contract the proof must assume, so there is nothing to axiomatize and
nothing for G-AX to falsify. `axiom_check.py` records the empty obligation set
and supplies a non-vacuous witness: it asserts `axioms == []` /
`deep_model_references == []`, confirms the deep model agrees with the real
patched decision logic, and exercises the **unchanged** real resolver
`_check_multi_class` to validate the resolved-vs-raw strategy bijection (the
binary-`'auto'` disagreement the issue triggers). Because G-AX runs against the
**unpatched** image (the gold patch is applied only for G-CONF/G-RESOLVE), the
witness touches only patch-unchanged code — it does not drive the buggy `fit`
path. The end-to-end "patched estimator runs the reproducer without IndexError"
check belongs to **G-CONF** (which applies the gold patch), not G-AX.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The two operations that genuinely *changed* — which flag
drives the coefficient selection, and whether the auxiliary value is recorded —
are modeled **directly** as the two `if`-decisions `chooseCoef` / `chooseAux`,
not hidden behind an axiom about the function under change. There are no consumed
axioms.

## D. verify(Solution) ⇒ resolved

`recordClassResult` verifies only if (A4) the committed coefficient vector is the
candidate selected by the **effective** strategy and (A7) the recorded auxiliary
value is `some auxValue` exactly when the auxiliary mode is in effect, else
`none`. By R (`str`-equality ↔ `Bool`, coefficient vector ↔ `List Rat`, averaged
scalar ↔ `Rat`, `append`/`append(None)` ↔ `some`/`none`) the verified decisions
equal the patched branch's two commitments on the tested inputs; by G-CONF the
R/I transliteration of `chooseCoef`/`chooseAux` agrees with `patch.diff`'s
behaviour on ≥10⁵ inputs (including the binary-`auto` boundary and the
non-elastic-net penalty cases); by G-AX the real patched estimator runs the
issue's reproducer without `IndexError` and yields the contracted no-refit
attribute shapes. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms (G-AX is non-vacuous but has an empty obligation
set).
