# refinement.md — scikit-learn__scikit-learn-25232

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`initialFillStatistics` `do` block and the `constantFill` callee stub) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses the callee's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The A legs and this narrative are audited by **G-EQ** and G-AX; the R/I legs
would be refuted by **G-CONF**, but this bundle's impl region is all-A-tagged so
G-CONF is skipped (`conf_skip=true`, mapping.md §4) — there is no R/I
computational content.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `IterativeImputer._initial_imputation` forwards `fill_value`

Gold hunks: add a `fill_value` parameter to `IterativeImputer.__init__`
(stored as `self.fill_value`), declare it `"no_validation"` in the parameter
constraints, and — the behavioural hunk — pass `fill_value=self.fill_value` into
the `SimpleImputer(...)` constructed in `_initial_imputation`:

```
 self.initial_imputer_ = SimpleImputer(
     missing_values=self.missing_values,
     strategy=self.initial_strategy,
+    fill_value=self.fill_value,
     keep_empty_features=self.keep_empty_features,
 )
 X_filled = self.initial_imputer_.fit_transform(X)
```

| # | Solution.lean impl op (`initialFillStatistics`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fillValue : Option Rat` | `self.fill_value` (numerical configured constant; `None` ↔ default) — set from the new `__init__` arg | R | `fill_value` (number-or-`None`) ↔ `Option Rat` (mapping.md §2). The `__init__`/constraint hunks only carry the value to `self.fill_value`; they are observationally the binding of this parameter. |
| A2 | parameter `nFeatures : Nat` | `X.shape[1]` | R | feature count ↔ `Nat` (mapping.md §2). |
| A3 | `let stats ← constantFill fillValue nFeatures` | `SimpleImputer(strategy="constant", fill_value=self.fill_value, …).fit(X)` then `.statistics_` | A-consumed | the unchanged constant-strategy fit is the callee; the proof consumes its `ensures` (`stats = replicate nFeatures (resolveFill fillValue)`). The **forwarding** of `fillValue` (vs the default) IS the fix: it is the only argument the patch threads through. G-AX checks the callee contract (mapping.md §3.1). |
| A4 | `return stats` (`List Rat`) | `self.initial_imputer_.statistics_` observed by the F2P test | R | `statistics_` ndarray ↔ `List Rat` (mapping.md §2); the test reads `initial_imputer_.statistics_` and asserts it equals `fill_value`. |

Discriminating content of the change — the configured constant must REACH the
fill helper, not be dropped for the default — lives in
`constantFill fillValue nFeatures` (model: helper set up with `fillValue`) ⇔ the
`fill_value=self.fill_value` argument (real). The pre-patch built the helper
without that argument, so it always used the numerical default `0`;
`Solution_prepatch.lean` reproduces that (`constantFill none nFeatures`) and
**fails** the `stats = replicate nFeatures (resolveFill fillValue)` clause
whenever `fillValue = some v` with `v ≠ 0` — exactly the F2P case
`fill_value = 100` (G-DIFF).

## B. The callee stub — `constantFill`

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `constantFill (fillValue) (nFeatures)` with `ensures stats = replicate nFeatures (resolveFill fillValue)`, impl `let stats :| stats = …` | the unchanged `SimpleImputer` constant-strategy fit | A-consumed + I | `:|` choice stub — sound by construction (`prove_correct` discharged by `loom_solve`). Its `ensures` is the weakest contract the caller needs: constant strategy yields the resolved constant in every feature slot (`np.full`). G-AX confirms against the real `SimpleImputer`. The `replicate`/`resolveFill` shape is **I** (concrete), but it lives entirely in the A callee's contract, so the whole row is A-consumed. |

`resolveFill` (`none → 0`, `some v → v`) is the numerical default-resolution of
`SimpleImputer.fit` (`_base.py:394-400`), part of the A-consumed callee contract.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The operation that genuinely changed — forwarding the
configured constant into the initial constant imputer — is modeled as the
**argument flowing into an A-consumed callee** (the unchanged `SimpleImputer`
fit), not hidden behind an axiom about the function under change. There is no
axiom about `_initial_imputation` itself. The only consumed contract,
`constantFill`, covers an **unchanged** callee (`SimpleImputer` fit), validated
by G-AX.

## D. verify(Solution) ⇒ resolved

`initialFillStatistics` verifies only if its output equals the per-feature
constant vector built from the **configured** `fillValue` (A3) — a prepatch that
forwards `none` (the default) fails (G-DIFF). By R (`fill_value ↔ Option Rat`,
`statistics_ ↔ List Rat`, `n_features ↔ Nat`) the verified routine equals
`SimpleImputer(strategy="constant", fill_value=self.fill_value).fit(X).statistics_`
on the modeled numerical inputs; by G-AX the callee contract matches the real
`SimpleImputer` constant fit (A-consumed). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE: the F2P test
`test_iterative_imputer_constant_fill_value` asserts `initial_imputer_.statistics_
== fill_value` for `fill_value=100`). Trust points are exactly axiom soundness
(G-AX) and refinement fidelity (this doc, G-EQ).
