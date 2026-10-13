# refinement.md — scikit-learn__scikit-learn-25931

Operation-by-operation correspondence between `model.py`'s implementation
regions and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses a `@ContractOnly` callee's
`Ensures`), **A-reference** (a deep model validated `==` the real callee by
axiom_check.py / G-AX, NOT consumed), or **I** (identical concrete operation).
Claim: *any implementation that verifies against this frozen spec, refined per
the map below, is behaviourally equal to the gold patch on the tested input
(F2P and the relevant P2P), so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The fix splits one public scoring method into a validating public method
(`score_samples`) and a non-validating private method (`_score_samples`), and
re-routes the in-`fit` offset computation through the non-validating private
method so the already-validated array is not validated a second time. The
discriminating behaviour is a **control-flow effect** that is INVISIBLE in the
returned scores: both scoring methods return the same per-row scores; they
differ only in whether a second validation pass (which, on a labelled fit of an
unlabelled prepared array, emits a `UserWarning`) is run as a side effect of
being called. A value-level postcondition therefore cannot separate gold from
the buggy code; the model pins the effect explicitly (see "How the effect is
modelled").

## How the effect is modelled (the soundness core)

The warning is a *side effect of invoking a scoring method*, not a value the
caller may keep or discard. So the model carries it as estimator state, and
makes the offset an un-fabricatable product of the correct method:

* `Estimator.fit_advisories: int` — a running tally of label-mismatch
  advisories emitted during fitting. **Each scoring routine mutates it as a
  side effect of being called** (`validating_scorer` adds
  `mismatch_advisory(...)`; `prepared_scorer` adds nothing). So the tally
  records what was actually emitted regardless of what the caller does with any
  return value — closing the "side-effect-as-discardable-return" hole.
* `Estimator.offset_set: bool` + the abstract token
  `offset_from_unvalidated_scoring(self)` — the calibration offset is furnished
  ONLY by `prepared_scorer` (the no-validation routine), whose contract sets
  `offset_set` and grants the token. The token is an abstract `@Predicate` the
  implementation cannot `Fold` into existence; there is no other granter. So an
  offset carrying the token can only have been produced by a no-validation
  scoring pass.
* **Provenance of the scored matrix** — a second pair of abstract `@Predicate`
  tokens, `raw_fit_input(X)` and `prepared_input(X)`, binds the scorer's argument
  to the fit's OWN training data, closing the fresh/foreign-matrix hole (attack
  10). `raw_fit_input` is granted only to `fit_offset`'s parameter `X_raw` (the
  impl cannot `Fold` it, so it cannot manufacture a foreign "raw input"). The
  contracted preparation callee `prepare` CONSUMES `raw_fit_input(X_raw)` and
  GRANTS `prepared_input(Result())`. `prepared_scorer` `Requires(prepared_input(X))`.
  Hence the scorer can only be fed the prepared form of fitting's actual input: a
  fabricated `Matrix(False)` lacks `prepared_input`, and cannot acquire it by
  laundering through `prepare` (it lacks `raw_fit_input`). This is faithful: the
  gold `fit` feeds `_score_samples` only the validated form of its OWN `X`, never
  a foreign array; the offset value is grounded in the actual training data
  (axiom_check.py confirms the gold offset derives from `_score_samples` of the
  prepared training input and differs from scoring a foreign array).

`fit_offset`'s postcondition requires BOTH `self.fit_advisories == 0` (rejects
routing through the validating path even if the count is discarded) AND, when
calibration is requested, `self.offset_set ∧ offset_from_unvalidated_scoring(self)`
(rejects skipping the scorer / fabricating the offset).

## Type abstraction (used throughout)

| repo reality | model carrier | bijection |
|---|---|---|
| a labelled `DataFrame` vs. an unlabelled `ndarray` | `Matrix` with `bool has_labels` | `has_labels == (the object carries column/feature names)` |
| the estimator's recorded fit-time feature names (`feature_names_in_` present/absent) | `Estimator.fitted_with_labels: bool` | `fitted_with_labels == hasattr(self, "feature_names_in_")` |
| the `UserWarning` count emitted during `fit` | `Estimator.fit_advisories: int` | the number of "X does not have valid feature names …" warnings emitted while fitting (0 in the fixed code, 1 in the bug) |
| whether the calibration `offset_` was computed **by per-row scoring** | `Estimator.offset_set: bool` (+ token) | `offset_set == (hasattr(self, "offset_") and contamination != "auto")` — True in the non-auto (scoring-derived) branch, False in the `"auto"` branch (`offset_ = -0.5`, no scoring); the token witnesses it came from `_score_samples`. Pinned by `Ensures(offset_set == calibration_requested)` |
| `_validate_data(… reset=True)` casting a table to a numeric array | `Matrix(prepared(X))`, with `prepared(X) == False` | preparation drops labels: the prepared form is always unlabelled (A-reference 2) |
| a `_check_feature_names(X, reset=False)` consistency pass + its possible warning | the integer `mismatch_advisory(X.has_labels, fitted)` (0/1) | the count of "X does not have valid feature names …" advisories that pass emits (A-reference 1) |
| `np.percentile(scores, 100*contamination)` offset value | (abstracted away; only its EXISTENCE + provenance is modelled) | the tests observe only that fitting emits no warning and that `offset_` is set, not the offset value; the scores' values are precision-irrelevant to the tested behaviour |

## Site 1 — the public scoring routine (`score_samples`)

Gold hunk (`sklearn/ensemble/_iforest.py`):
```
 def score_samples(self, X):
-    check_is_fitted(self)
     X = self._validate_data(X, accept_sparse="csr", dtype=np.float32, reset=False)
-    return -self._compute_chunked_score_samples(X)
+    return self._score_samples(X)
```

| # | model.py impl op (`validating_scorer`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1a | `self: Estimator`, `X: Matrix` | `self`, `X` (array/DataFrame) | R | object fields ↔ `Matrix.has_labels` / `Estimator.fitted_with_labels` (type table). |
| 1b | `self.fit_advisories += mismatch_advisory(X.has_labels, self.fitted_with_labels)` | `X = self._validate_data(X, ..., reset=False)` (runs `_check_feature_names(reset=False)`) | A-reference | the consistency pass's advisory behaviour is modelled **deeply** as `mismatch_advisory`; validated `==` the real `_check_feature_names(reset=False)` over all four label combinations (A-reference 1). The pass runs as an UNCONDITIONAL side effect of calling the public method, so it mutates the tally; the post-patch `score_samples` still validates its own argument. |
| 1c | (no return value; scores unmodelled) | `return self._score_samples(X)` | I + R | after validation the public method delegates to the non-validating scorer; the delegated scoring contributes no further advisory (site 2). The returned scores are not modelled because no tested behaviour observes their values — only the validation side effect is. |

## Site 2 — the non-validating private scorer (`_score_samples`), modelled as a consumed `@ContractOnly` callee

Gold hunk introduces:
```
+def _score_samples(self, X):
+    """Private version of score_samples without input validation."""
+    check_is_fitted(self)
+    return -self._compute_chunked_score_samples(X)
```

`prepared_scorer` is a `@ContractOnly` callee that `fit_offset` (= the gold
`fit`) CALLS — it is not the changed operation itself, so axiomatizing it is
sound (SPEC_GUIDE §3). Its contract:

| # | `prepared_scorer` contract clause | repo fact | tag | justification |
|---|---|---|---|---|
| 2a | `self`, `X` | `self`, `X` | R | type table. |
| 2a' | `Requires(X.has_labels == False)` | `_score_samples` runs NO `_validate_data`, so it is only ever fed the already-validated UNLABELLED numeric array (the `X` returned by `fit`'s reset=True `_validate_data`, or the array the public `score_samples` validates before delegating) | R | the callee's domain is the prepared/unlabelled matrix; feeding it a raw labelled table is out of domain (the real callee raises `ValueError: X should be in np.ndarray format`). Narrowing a callee precondition is faithful and cannot weaken the proof. Closes the raw-matrix hole (attack 8 below). |
| 2b | `Ensures(self.fit_advisories == Old(self.fit_advisories))` | `_score_samples` runs NO `_validate_data` (only `check_is_fitted` + `_compute_chunked_score_samples`) | A-consumed | the private scorer performs no label-consistency pass, so it emits zero advisories whatever the fit-time label state. Checked by axiom_check.py: the real `_score_samples`, fed an unlabelled array after a labelled fit, emits 0 advisories. |
| 2c | `Ensures(self.offset_set)` ∧ `Ensures(offset_from_unvalidated_scoring(self))` | `_score_samples` returns the per-row scores that `np.percentile` turns into `offset_` | A-consumed | the offset is produced BY this scoring pass; the token witnesses it came from a no-validation pass. Checked by axiom_check.py: the real `_score_samples` produces one score per row (so it can furnish the offset). |

## Site 3 — the in-`fit` offset computation (`fit_offset`)

Gold hunk:
```
-    self.offset_ = np.percentile(self.score_samples(X), 100.0 * self.contamination)
+    # To avoid performing input validation a second time we call
+    # _score_samples rather than score_samples
+    self.offset_ = np.percentile(self._score_samples(X), 100.0 * self.contamination)
```

| # | model.py impl op (`fit_offset`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 3a | `self.fitted_with_labels = X_raw.has_labels`; `Xp = prepare(X_raw)` | the earlier-in-`fit` `X = self._validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)` (reset=True) | A-consumed + A-reference | the one reset=True preparation pass records labels (`feature_names_in_`) and yields an unlabelled array; modelled by `fitted_with_labels := X_raw.has_labels` and the contracted `prepare` callee, whose `Ensures(Result().has_labels == False)` is the A-reference deep fact (validated `== _validate_data(reset=True)` output by axiom_check.py) and whose `prepared_input`-token grant is the consumed provenance fact binding `Xp` to fit's own input. reset=True never advises (A-reference 2). |
| 3b | `if calibration_requested:` | `if self.contamination == "auto": … return self` else fall through | R | `calibration_requested == (self.contamination != "auto")`; the "auto" early-return path computes no offset, modelled by the `if` being false. |
| 3c | `prepared_scorer(self, Xp)` | `np.percentile(self._score_samples(X), 100.0*self.contamination)` | A-consumed + R | **the fix:** the offset is derived through the NON-validating private scorer (site 2), which runs NO second preparation pass on the already-prepared `Xp`. By the callee's contract this leaves `fit_advisories == 0` and furnishes the token-bearing offset. The `np.percentile`/offset value is abstracted (only its existence + provenance is tested). |
| 3d | postconditions: `fit_advisories == 0`; `calibration_requested ⇒ offset_set ∧ offset_from_unvalidated_scoring(self)`; `offset_set == calibration_requested` | (the whole `fit` body emits no warning AND sets `offset_` from `_score_samples` in the non-auto branch, while the `"auto"` branch sets `offset_ = -0.5` WITHOUT scoring) | I | the postcondition pins the tested behaviour: a labelled fit with calibration requested produces no warning (F2P) and sets `offset_` (the P2P `offset_`/`decision_function`/`score_samples` consumers). The **biconditional** `offset_set == calibration_requested` (via 3b: `calibration_requested == (contamination != "auto")`) additionally pins the auto branch: scoring is reached IFF calibration is requested, so an impl that scores unconditionally (which would crash on `100.0 * "auto"` in the real auto branch — does NOT resolve) is rejected. |

### Where the bug lives (G-DIFF discriminator)

The pre-patch `fit` derived the offset via the **public** `self.score_samples(X)`,
which re-runs `_validate_data(reset=False)` — a second consistency pass — on the
already-prepared (unlabelled) array while `feature_names_in_` was set. That pass
emits the spurious advisory. `model_prepatch.py` reproduces this exactly: its
`fit_offset` routes calibration through `validating_scorer(self, Xp)`, whose
`mismatch_advisory(False, True) == 1` mutates `fit_advisories` to 1, so the
postcondition `self.fit_advisories == 0` **fails** (G-DIFF). The spec regions are
byte-identical between `model.py` and `model_prepatch.py`; only the `fit_offset`
impl differs.

## No kind-3 (unexpressible-changed-op) steps

Every step is R, A-consumed, A-reference, or I. The operation that genuinely
changed — *which* scoring routine the offset computation calls, a control-flow
effect invisible in the scores — is modelled by (i) two contracted scoring
functions distinguished by their side effect on `fit_advisories` and by whether
they grant the offset token, and (ii) the `fit_offset` caller choosing between
them. `prepared_scorer` is the only **consumed** `@ContractOnly` axiom;
`mismatch_advisory` / `prepared` are A-reference deep models validated `==` the
real `_check_feature_names` / `_validate_data` by axiom_check.py (G-AX).

## verify(model) ⇒ resolved

`fit_offset` verifies only if (a) the advisory tally ends at 0 — which forbids
invoking the validating path at all, since calling it mutates the tally to 1 on
a labelled fit even if the result is discarded — and (b) when calibration is
requested, the offset is set and carries the no-validation token — which can
only be obtained by calling `prepared_scorer`. By the type refinement (R), the
consumed-axiom soundness (G-AX: real `_score_samples` emits 0 advisories and
produces the scores) and the A-reference validations (G-AX: `mismatch_advisory`
/ `prepared` `==` the real callees; post-patch `IsolationForest.fit` emits no
advisory and sets `offset_` in the F2P case), the verified `fit_offset` equals
the gold `fit` on the tested input (F2P + the `offset_`-consuming P2P). The gold
patch resolves (G-RESOLVE, confirmed: F2P + `test_iforest_works[42-0.25/auto]` +
`test_score_samples` pass with gold applied). Trust points: refinement fidelity
(this document, G-EQ) and the axiom/deep-model soundness (axiom_check.py, G-AX).

## Adversarial closure (all re-spec holes are closed)

Same-spec wrong implementations were re-encoded against the fixed spec (each
shares model.py's spec view byte-for-byte; only `fit_offset`'s impl region
differs); each was confirmed SAME-spec and NONE verifies; a structurally-
different correct positive control verifies. The recover-verdict hole (attack 8,
raw matrix) is rejected by the `prepared_scorer` precondition `X.has_labels ==
False`; the fresh/foreign-matrix hole (attack 10) is rejected by the
`prepared_input` provenance token.

| attack | refines to | rejected by clause |
|---|---|---|
| skip the scorer entirely (verdict attack 2) | omit the `offset_` assignment → P2P `decision_function`/`score_samples` AttributeError | `Implies(calibration_requested, self.offset_set)` |
| route through validating path, discard count (verdict attack 3 = literal pre-patch line) | the buggy `np.percentile(self.score_samples(X), …)` → F2P warning | `self.fit_advisories == 0` |
| set `offset_set = True` with no scoring (attack 4) | invent `offset_` without scoring | `offset_from_unvalidated_scoring(self)` (unforgeable token: insufficient permission) |
| call BOTH scorers — prepared for the token, validating to re-introduce the pass (attack 6) | re-introduce a validating pass alongside the correct one → warning | `self.fit_advisories == 0` |
| call the no-validation scorer on the RAW matrix: `prepared_scorer(self, X_raw)` (recover-verdict attack 8) | `self._score_samples(<raw DataFrame>)` → `ValueError: X should be in np.ndarray format` in `_compute_chunked_score_samples` → `fit` crashes → F2P + most P2P fail | `prepared_scorer` precondition `X.has_labels == False` (the in-fit scorer's argument must be the already-prepared unlabelled matrix) |
| **score a FABRICATED unlabelled matrix `prepared_scorer(self, Matrix(False))` (verdict attack 10)** | `np.percentile(self._score_samples(<fabricated array>), …)` → wrong `offset_` (≠ gold) → P2P `test_iforest_works[42-0.25]` predictions wrong → does NOT resolve | **`prepared_scorer` precondition `prepared_input(X)`** (insufficient permission: a fabricated matrix lacks the prepared-input token) |
| **launder a fresh matrix through `prepare`: `prepared_scorer(self, prepare(Matrix(True)))` (attack 10b)** | scoring a foreign array's prepared form → wrong `offset_` → does NOT resolve | **`prepare` precondition `raw_fit_input(X_raw)`** (insufficient permission: a fresh matrix lacks the raw-input token; only `fit_offset`'s own `X_raw` carries it) |
| **invoke the scorer UNCONDITIONALLY — drop the `if calibration_requested:` guard: `prepared_scorer(self, Xp)` always (verdict attack 11, 3rd-pass)** | `np.percentile(self._score_samples(X), 100.0 * self.contamination)` runs even in the gold `"auto"` branch → `100.0 * "auto"` → `TypeError: can't multiply sequence by non-int` → `fit` crashes → 3/5 P2P fail (gold passes 5/5) → does NOT resolve | **`Ensures(self.offset_set == calibration_requested)`** (the biconditional: scoring sets `offset_set`, the sole granter; calling it when `calibration_requested == False` makes `offset_set` True ≠ False — verifier: `atk_uncond.py:239 Postcondition of fit_offset … (self.offset_set == calibration_requested) might not hold`) |
| skip recording the fit-time labels | not setting `feature_names_in_` | `self.fitted_with_labels == Old(X_raw.has_labels)` |

Positive control: an impl that records the fit-time labels AFTER scoring (a
different statement order than model.py) still verifies — confirming the spec
admits the correct behaviour through a structurally-different skeleton. (All
results reproduced: model.py verifies in ~22s; each attack fails on exactly the
clause above; poscontrol verifies.)
