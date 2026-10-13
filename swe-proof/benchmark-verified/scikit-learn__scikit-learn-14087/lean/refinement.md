# refinement.md — scikit-learn__scikit-learn-14087

Maps every operation in `implementation_chooseLayout` and
`implementation_ratioEntry` to its `patch.diff` counterpart in
`sklearn/linear_model/logistic.py` (`LogisticRegressionCV.fit`, `refit=False`
branch). Tags: **R** type-refinement, **A-consumed** proof uses a callee axiom,
**A-reference** deep-modeled changed/dependency op validated == real callee, **I**
identical concrete op.

The fix changes two independent decisions; each is modeled as its own triple.

## Modeled decision 1 — `chooseLayout` (coefficient-aggregation branch)
The gold patch changes the branch guard from `self.multi_class == 'ovr'` (raw
configured) to `multi_class == 'ovr'` (the effective, already-resolved strategy).
The two branches select different `coefs_paths` indexing layouts; selecting on the
unresolved request runs the wrong layout when the request is `'auto'`, raising
`IndexError`.

| # | Lean op | patch.diff / source op | tag | note |
|---|---|---|---|---|
| 1 | `let mut layout := AggLayout.jointLayout` | the `else:` (non-`ovr`) averaging branch default | I | initial layout = the joint/4-D branch. |
| 2 | `if eff = EffStrategy.perClass` | POST `if multi_class == 'ovr':` (the effective strategy) | R | `'ovr'/'multinomial'` string ↔ `EffStrategy.perClass/.joint` (mapping.md). The selector is the resolved `multi_class`, NOT raw `self.multi_class`. |
| 3 | `layout := AggLayout.perClassLayout` | `w = np.mean([coefs_paths[i, best_indices[i], :] ...])` (3-D layout) | R | the per-class/3-D averaging branch ↔ `perClassLayout`. |
| 4 | `else layout := AggLayout.jointLayout` | `w = np.mean([coefs_paths[:, i, best_indices[i], :] ...])` (4-D layout) | R | the joint/4-D averaging branch ↔ `jointLayout`. |
| 5 | `return layout` | the branch actually taken (which `coefs_paths` indexing runs) | I | the selected layout. |

`req : ReqStrategy` appears as a free input but is intentionally absent from the
spec relation and unused by the impl: the whole point of the fix is that the
choice depends on `eff`, never on the raw request. (The unused-variable linter
warning on `req` is expected and benign.)

## Modeled decision 2 — `ratioEntry` (mixing-ratio summary entry)
The gold patch guards the mixing-ratio append with `if self.penalty ==
'elasticnet'`, appending the computed mean only in that regime and `None`
otherwise.

| # | Lean op | patch.diff / source op | tag | note |
|---|---|---|---|---|
| 1 | `let mut entry : Option ℚ := none` | the absent-ratio default (`self.l1_ratio_.append(None)`) | I | initial entry = absent. |
| 2 | `if combinedPenalty` | POST `if self.penalty == 'elasticnet':` | R | `self.penalty == 'elasticnet'` (Bool) ↔ `combinedPenalty`. |
| 3 | `entry := some ratio` | `self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))` | R | the computed mixing-ratio mean ↔ `some ratio`; the exact mean is the unchanged argmax/index/mean arithmetic, carried as the free input `ratio`. |
| 4 | `else entry := none` | `else: self.l1_ratio_.append(None)` | R | the absent-ratio case ↔ `none`. |
| 5 | `return entry` | the value appended to `self.l1_ratio_` this iteration | I | the recorded entry. |

`ratio` is the candidate mixing-ratio mean computed upstream by unchanged
argmax/floor-division/index/mean arithmetic; the fix decides only whether that mean
is recorded (`some ratio`) or suppressed (`none`). Modeling `ratio` as a free
`ℚ` and pinning only its presence/absence is faithful: no property of the
arithmetic is consumed, so it is an input, not an axiom.

## Soundness summary
Both impls are pure decision logic (R/I tags only — no A-consumed, no
A-reference). There is **no opaque callee and no consumed axiom**; each theorem is
proved for every value of its free inputs (`req`, `eff`, `combinedPenalty`,
`ratio`). Hence `axiom_check.py` (G-AX) is a skip stub. G-CONF
(`conformance_check.py`) is a real differential test (`conf_skip=false`): it grounds
the Python transliteration of both decisions against the REAL patched
`LogisticRegressionCV.fit` over the `{l2,elasticnet} × {ovr,multinomial,auto}`
config grid and fuzzes the shadow vs the gold-patch decision over ≥1e5 inputs.

## Prepatches (the real bugs)
- `Solution_prepatch_1.lean`: `chooseLayout` selects on the RAW request
  (`if req = ReqStrategy.perClass`) instead of `eff`. For `req=autoStrategy,
  eff=perClass` the impl yields `jointLayout` while the spec demands
  `perClassLayout`; the carried gold proof's `rfl` no longer closes → fails
  G-VERIFY. This is exactly the issue's `IndexError` config (default
  `multi_class='auto'` resolving to `'ovr'`).
- `Solution_prepatch_2.lean`: `ratioEntry` always records `some ratio`
  (no `combinedPenalty` guard). For `combinedPenalty=false` the impl yields
  `some ratio` while the spec demands `none`; the carried gold proof fails →
  fails G-VERIFY. This is the FAIL_TO_PASS `l2` (non-elasticnet) config.

One prepatch per independently-observable fixed behavior (the two decisions are
fixed by disjoint hunks and observed by disjoint F2P configurations).
