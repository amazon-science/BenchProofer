# refinement.md — scikit-learn__scikit-learn-25973

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `runScoringRounds` `do` block + the deep `materialize`/`readObs`/`advance`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(a deep model validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I.

The A legs + this narrative are audited by **G-EQ**; the R/I legs are normally
refuted by **G-CONF**, but here the discriminating observable is a stateful
generator-exhaustion side effect (see §C, `conf_skip=true`). `patch.diff` is the
gold patch **verbatim** (G-RESOLVE).

## A. The materialize-before-loop site

Gold hunks (`sklearn/feature_selection/_sequential.py`):
```
+ from ..base import ..., is_classifier
+ from ..model_selection import cross_val_score, check_cv
  ...
+ cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))
  ...
  for _ in range(n_iterations):
-     new_feature_idx, new_score = self._get_best_new_feature_score(cloned_estimator, X, y, current_mask)
+     new_feature_idx, new_score = self._get_best_new_feature_score(cloned_estimator, X, y, cv, current_mask)
  ...
- def _get_best_new_feature_score(self, estimator, X, y, current_mask):
+ def _get_best_new_feature_score(self, estimator, X, y, cv, current_mask):
  ...
-         cv=self.cv,
+         cv=cv,
```

| # | Solution.lean impl op (`runScoringRounds`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `source : CvSource` | the `cv` argument value (`self.cv`: splitter / iterable / one-shot generator of `(train,test)` splits) | R | source ↔ `CvSource` (mapping.md §2): full split sequence ↔ `splits`, re-readable ↔ `reusable`, exhausted ↔ `consumed`. |
| A2 | parameter `k : Nat` | `n_iterations` (`_sequential.py:280`), the `range(n_iterations)` loop count | R | `n_iterations` ↔ `k` (mapping.md §2). |
| A3 | `let mut src := materialize source` (before the loop) | `cv = check_cv(self.cv, y, classifier=is_classifier(self.estimator))` inserted before the `for` loop | A-reference | the added buffering call is modeled **deeply** by `materialize`; its claimed property (the result is re-readable and carries the same split sequence) is validated == the real `check_cv` by axiom_check.py (G-AX). NOT a consumed axiom. mapping.md §3.1. |
| A4 | the backward `while` fold: each round `let o := readObs src; src := advance src; obs := o :: obs` | the `for _ in range(n_iterations)` loop, each iteration calling `_get_best_new_feature_score(..., cv, ...)` → `cross_val_score(..., cv=cv, ...)` which reads the split source | I | the loop control flow + per-round read/advance are transliterated concrete ops; `k` rounds each reading `src`. The read semantics (`readObs`/`advance`) are the deep model of "iterate the split source once". |
| A5 | `obs = List.replicate k source.splits` (every round observed the full sequence) | the post-patch behaviour: every round's `cross_val_score` sees the full split set, so scoring succeeds for all `n_iterations` rounds (no empty-splits `IndexError`) | R | the observation record ↔ "each round scored against the full CV splits". The F2P test only requires `fit` to complete without error for a generator `cv`; the postcondition pins the stronger, sufficient property that EVERY round observes the full splits. |

The threading of `cv` through `_get_best_new_feature_score`'s signature
(`current_mask` → `cv, current_mask`) and the `cv=self.cv` → `cv=cv` rename are
the mechanical plumbing of A3/A4: they route the materialized source (`src`)
into every per-round read rather than re-reading the raw `self.cv`. Modeled as
the single threaded `src` variable.

## A2. Termination semantics (spec-strengthening, audit repair)

The bundle uses `loom.semantics.termination "total"` (`TotalCorrectness`), not
`"partial"`. Under partial correctness a diverging implementation (an infinite
`while` that never reaches the postcondition) discharges every `ensures`
vacuously — a spec-too-weak hole: its translated patch would hang the real
test suite and not resolve (verify⇏correct). The real scoring loop is a
bounded `for _ in range(n_iterations)` that always terminates, so total
correctness is the faithful semantics: it rejects every diverging impl (a loop
without a provable `decreasing` measure is unverifiable under total
semantics), while the verified impl's `while` carries `decreasing i` to
discharge the totality obligation. The `set_option`/`open` lines are part of
the frozen spec view shared byte-identical by both twins (same_spec holds).

Note on the recorded echo probe: `return List.replicate k source.splits` is
NOT an ungrounded-oracle hole — `source.splits` is the genuine input carrier
(directive 8: the postcondition is grounded in the inputs, not an opaque
answer-key), so producing the full sequence `k` times IS the desired
observable; any refined patch of that impl buffers the source and yields full
splits every round, i.e. resolves. It is a non-vacuity witness, not a wrong
implementation.

## B. No consumed axioms

There are no `axiom` declarations. The only kind-A construct is the A-reference
`materialize` (a deep model of the unchanged helper `check_cv`), validated by
G-AX. `is_classifier` is observationally irrelevant on the iterable/generator
path the bug and F2P test exercise (mapping.md §3.1) and is not modeled.

## C. No kind-3 (inexpressible-changed-op) steps; conf_skip rationale

Every step is R, A, or I. The operation that genuinely *changed* — inserting the
buffering call so repeated reads see the full splits — is modeled **deeply**
(`materialize` + the threaded `src`), an A-reference, not hidden behind an axiom
about the function under change.

`conf_skip = true`: the discriminating observable is a **stateful side effect** —
a one-shot generator is exhausted by the first read and yields `[]` thereafter.
That is not reproducible as a pure, deterministic input→output R/I shadow this
gate can fuzz over ≥10⁵ inputs without instantiating the real `cross_val_score`
/ CV-splitter machinery and a live generator object (i.e. the F2P integration
test itself, `test_cv_generator_support`). The R/I content of the loop, once a
re-readable source is supplied, reduces to "observe `source.splits` each round";
there is no input-dependent computation on split *contents* to differentially
refute — the discriminating fact is whether the source was BUFFERED before the
loop (the branch the patch adds), which is exercised only by the live
read/exhaust machinery and is covered by axiom_check.py (G-AX). This mirrors the
django__django-11066 conf_skip precedent (observable is a stateful interaction,
not a fuzzable pure shadow). The prepatch (`Solution_prepatch.lean`) omits A3
(`materialize`) and consequently FAILS the postcondition `obs = List.replicate k
source.splits` for a single-pass source (G-DIFF) — the bug, seen by the spec.

## D. verify(Solution) ⇒ resolved

`runScoringRounds` verifies only if, after the (modeled) buffering, EVERY one of
the `k` rounds observes the full split sequence (A5) — which requires the
`materialize` step (A3); drop it and a single-pass source is consumed after
round 1, the observations are not `List.replicate k source.splits`, and the proof
fails (the prepatch, G-DIFF). By R (`CvSource ↔ cv source`, `k ↔ n_iterations`)
and by G-AX (the deep model `materialize` == real `check_cv`: the materialized
source is re-readable with the same splits), a model satisfying this spec refines
to the gold patch: insert `check_cv` before the loop and thread it through every
round's scoring read. The gold patch resolves (G-RESOLVE). Trust points: the
A-reference soundness (G-AX) and refinement fidelity (this doc, G-EQ).
