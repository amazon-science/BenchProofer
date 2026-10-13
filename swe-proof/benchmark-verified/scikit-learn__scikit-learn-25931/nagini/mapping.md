# mapping.md — scikit-learn__scikit-learn-25931

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e3d1f9ac39e4bf0f31430e779acc50fb05fe1b64`, states the type
abstraction, and gives the provenance + executable soundness check of each
axiom / deep-model reference.

Repo file under change: `sklearn/ensemble/_iforest.py`.
Unchanged callees referenced: `sklearn/base.py`
(`BaseEstimator._check_feature_names`, `BaseEstimator._validate_data`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fit_offset(self, X_raw, calibration_requested)` | `IsolationForest.fit` — `sklearn/ensemble/_iforest.py:268` (the offset hunk at line 347–348) | the patched site: routes the calibration scoring through the non-validating private scorer |
| `validating_scorer(self, X)` | `IsolationForest.score_samples` — `sklearn/ensemble/_iforest.py:407` (post-patch: validate then delegate to `_score_samples`) | the public scoring routine; runs one validation pass on its own argument as a side effect of being called |
| `prepared_scorer(self, X)` *(consumed `@ContractOnly` axiom)* | `IsolationForest._score_samples` — introduced by the patch (`check_is_fitted` + `-self._compute_chunked_score_samples(X)`, NO `_validate_data`) | the non-validating private scorer the gold `fit` calls; emits no advisory and furnishes the offset |
| `offset_from_unvalidated_scoring(est)` *(abstract `@Predicate` token)* | the provenance of `self.offset_` after the gold non-auto branch | unforgeable witness that the offset was produced by `_score_samples` (a no-validation pass); granted only by `prepared_scorer` |
| `raw_fit_input(X)` *(abstract `@Predicate` token)* | the identity of `fit`'s own raw training input `X` | unforgeable witness that a matrix IS the fit's actual input; granted only to `fit_offset`'s parameter `X_raw`, consumed by `prepare` |
| `prepared_input(X)` *(abstract `@Predicate` token)* | the prepared form of `fit`'s own raw training input (the validated array `_score_samples` is fed in gold `fit`) | unforgeable witness that a matrix is the prepared form of fit's actual input; granted only by `prepare`, required by `prepared_scorer` |
| `prepare(X_raw)` *(consumed + A-reference callee)* | `BaseEstimator._validate_data(X, reset=True)` in `fit` — `sklearn/base.py:495` (casts to `ndarray`, dropping labels) | the fitting preparation pass: yields an unlabelled matrix (`Ensures Result().has_labels == False`, the A-reference deep fact) and binds it to fit's own input via the `prepared_input` token (the consumed provenance fact) |
| `mismatch_advisory(arg_has_labels, fitted_with_labels)` *(deep model — A-reference)* | `BaseEstimator._check_feature_names(X, reset=False)` — `sklearn/base.py:406` (the warning at lines 450–455) | pure spec: advisory count of one label-consistency preparation pass |
| `Estimator.fitted_with_labels` | `feature_names_in_` attribute set in `_check_feature_names(reset=True)` — `sklearn/base.py:427–429` | recorded fit-time label state |
| `Estimator.fit_advisories` | the count of "X does not have valid feature names …" `UserWarning`s emitted during `fit` | the side effect under fix: 0 in the fixed code, 1 in the bug. Mutated by the scoring routines as a side effect of being called, so it cannot be discarded by the caller |
| `Estimator.offset_set` | whether `self.offset_` was assigned **by per-row scoring** (the non-auto branch) | `offset_set == (hasattr(self, "offset_") and self.contamination != "auto")`, i.e. `offset_set == (contamination != "auto")` after fitting (since `offset_` is set in both branches). The non-auto branch derives the offset from `np.percentile(_score_samples(X), …)`; the `"auto"` branch sets `offset_ = -0.5` and early-returns WITHOUT scoring, so `offset_set` is `False` there. The calibration offset is a REQUIRED product of fitting when `contamination != "auto"` (consumed by `decision_function`, `predict`, `score_samples`). Modelled so it is granted ONLY by the per-row scorer `prepared_scorer`, never assigned directly — hence `offset_set` exactly tracks scoring-provenance, matching the strengthened `Ensures(offset_set == calibration_requested)` |
| `Matrix.has_labels` | whether the input carries feature names (`_get_feature_names(X) is not None`) — `sklearn/utils/validation.py` | abstracted input field |

The pre-patch repo line the change edits (for the refinement audit, not
referenced from the consumer spec view): the offset assignment
`self.offset_ = np.percentile(self.score_samples(X), 100.0 * self.contamination)`
(`_iforest.py:348`), which called the validating public `score_samples`, and
the original `score_samples` body that contained the `_validate_data(reset=False)`
pass before scoring.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| labelled `pandas.DataFrame` vs. unlabelled `numpy.ndarray` input | `Matrix` with field `has_labels: bool` | `has_labels == (_get_feature_names(X) is not None)` |
| `feature_names_in_` present/absent on the estimator | `Estimator.fitted_with_labels: bool` | `fitted_with_labels == hasattr(self, "feature_names_in_")` |
| the `UserWarning` emission count during `fit` | `Estimator.fit_advisories: int` (mutated by the scoring routines) | the warning is a side effect of invoking a scoring routine, not a return value — modelled as shared estimator state so a verifying impl cannot discard it |
| whether `offset_` was computed **by per-row scoring** (+ its provenance) | `Estimator.offset_set: bool` + `offset_from_unvalidated_scoring` token | `offset_set == (hasattr(self, "offset_") and contamination != "auto")` — True exactly in the non-auto (scoring-derived) branch, False in the `"auto"` branch where `offset_ = -0.5` is set without scoring; the token witnesses the offset came from `_score_samples` |
| `_validate_data(reset=True)` casting a table to a float32 array | `prepare(X_raw)` → an unlabelled `Matrix` (`Result().has_labels == False`) carrying the `prepared_input` token | preparation drops labels; the prepared form is always unlabelled (§3.2) and is bound to fit's own input |
| one `_check_feature_names(reset=False)` pass + its warning | `int mismatch_advisory(...)` (0/1) | the count of "X does not have valid feature names …" warnings the pass emits (§3.1) |
| `self.contamination != "auto"` | `bool calibration_requested` | the non-auto branch that computes the offset; "auto" short-circuits (`offset_ = -0.5; return self`) |
| `np.percentile(scores, 100*contamination)` offset value | abstracted (only existence + provenance modelled) | the tests assert the ABSENCE of the warning during fit and that `offset_` is set, not the offset value; behaviour is precision-independent, so no float encoding is used |

`pandas`/`numpy` objects and `np.percentile` are not Nagini-expressible; the
modelled state is the minimal touched fields plus the advisory tally and the
offset-existence token, which is exactly the tested behaviour (F2P
warning-absence + P2P `offset_` existence).

## 3. Axiom / deep-model provenance (checked by G-AX / axiom_check.py)

### 3.1 `mismatch_advisory` ↔ `BaseEstimator._check_feature_names(reset=False)` (A-reference 1, patch-independent)
**Callee:** `sklearn/base.py:406` `_check_feature_names(self, X, *, reset)`.
With `reset=False`, it computes `fitted_feature_names = getattr(self,
"feature_names_in_", None)` and `X_feature_names = _get_feature_names(X)`, then
(lines 450–455) warns "X does not have valid feature names, but
{ClassName} was fitted with feature names" **iff** `X_feature_names is None and
fitted_feature_names is not None` — i.e. the argument carries no labels while
the estimator was fitted with labels. The other three combinations are silent
for THIS advisory (the both-None / both-present cases return without it; the
`X has names / fitted without` case emits a DIFFERENT message). That is exactly
`mismatch_advisory(arg_has_labels, fitted_with_labels) = 1 iff
(not arg_has_labels) and fitted_with_labels`, else `0`.

**Soundness check (G-AX):** `check_consistency_rule()` drives the REAL
`_check_feature_names(reset=False)` on a probe estimator across all four
`(arg_has_labels, fitted_with_labels)` combinations and counts the real warning,
asserting `== mismatch_advisory(...)`.

### 3.2 `prepare` ↔ `BaseEstimator._validate_data(reset=True)` (A-reference + consumed provenance, patch-independent fact)
**Callee:** `sklearn/base.py:495` `_validate_data`. In `fit` it is called as
`self._validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)` (reset=True);
with `cast_to_ndarray=True` (default) it runs `check_array`, returning a numeric
`ndarray`/sparse matrix that carries no feature names. Hence the prepared form
is always unlabelled — `prepare`'s `Ensures(Result().has_labels == False)`
(the A-reference deep fact). reset=True also sets `feature_names_in_` from the
input without emitting the mismatch advisory.

`prepare` is modelled as a contracted callee (replacing the earlier dead `@Pure
prepared`) so it can ALSO carry the provenance binding: it `Requires
(raw_fit_input(X_raw))` and `Ensures(prepared_input(Result()))`. This makes the
prepared matrix the prepared form of fit's OWN input — the array `_score_samples`
is fed inside the gold `fit` is precisely the reset=True `_validate_data` output
of fit's `X`, never a foreign array. The `prepared_input` token is the consumed
provenance fact `prepared_scorer` requires (§3.3); the `has_labels == False`
clause is the A-reference deep fact checked below. `prepare` also `Ensures
(X_raw.has_labels == Old(X_raw.has_labels))` (it reads, does not relabel, its
input) for contract completeness.

**Soundness check (G-AX):** `check_prepared_drops_labels()` runs the REAL
`_validate_data(reset=True)` on a labelled DataFrame and on an unlabelled array
and asserts the output has no feature names (`_get_feature_names(out) is None`)
in both cases (validating the `has_labels == False` Ensures). The provenance
binding is validated by `check_offset_derives_from_prepared_training_input()`
(§3.4).

### 3.3 `prepared_scorer` ↔ `IsolationForest._score_samples` (consumed axiom, patch-dependent)
**Callee:** `IsolationForest._score_samples`, introduced by the patch:
`check_is_fitted(self)` + `return -self._compute_chunked_score_samples(X)` —
crucially NO `_validate_data` call, so NO label-consistency pass runs. The
axiom's `Ensures`:
* `self.fit_advisories == Old(self.fit_advisories)` — calling it emits no
  advisory (it runs no validation pass).
* `self.offset_set` ∧ `offset_from_unvalidated_scoring(self)` — it produces the
  per-row scores from which `np.percentile` derives the offset, and is the only
  granter of the no-validation token.

Its preconditions `Requires(X.has_labels == False)` AND `Requires
(prepared_input(X))` narrow the callee's domain to the already-prepared
(unlabelled) matrix that is the prepared form of FIT'S OWN input. This is
faithful and NOT an over-claim: `_score_samples` runs no `_validate_data`, so it
can only consume a numeric array — in the gold `fit` its argument is the `X`
returned by the reset=True `_validate_data` at `fit` entry (always unlabelled),
and via the public `score_samples` its argument is that validated array. Feeding
it a raw labelled DataFrame is outside its domain (the real callee raises
`ValueError: X should be in np.ndarray format` inside
`_compute_chunked_score_samples`) — rejected by `X.has_labels == False`. Feeding
it a FABRICATED/foreign unlabelled array would compute the offset from the wrong
data (a different `offset_`, so the resolving P2P predictions break) — rejected
by `prepared_input(X)`, which only `prepare` (on fit's own input) can grant.
Narrowing a callee's precondition can only make the proof harder, never weaker,
so it cannot mask a wrong impl.

This is the WEAKEST contract the proof needs and never over-claims the real
callee (it only asserts "no advisory" + "produces scores", both of which the
real `_score_samples` satisfies, on its actual unlabelled domain).

**Soundness check (G-AX):** `check_prepared_scorer_runs_no_validation()` calls
the REAL `_score_samples` on an unlabelled array after a labelled fit and
asserts (a) ZERO "does not have valid feature names" advisories, and (b) it
returns one score per row (so it can furnish the offset). Runs only when the
gold patch is applied (the method exists only post-patch).

### 3.4 Provenance/capability tokens soundness (patch-dependent)
Three abstract `@Predicate` tokens, none of which the impl can `Fold` into
existence:
* `offset_from_unvalidated_scoring` — no granter other than `prepared_scorer`.
  Soundness: in the gold `fit`, the only producer of `self.offset_` in the
  non-auto branch is `_score_samples`, which runs no validation. So an offset
  that exists after a non-auto fit was produced by a no-validation pass.
* `raw_fit_input` — granted only to `fit_offset`'s own parameter `X_raw`
  (the fit's actual training input), consumed by `prepare`. Soundness: the impl
  cannot manufacture a foreign matrix bearing this token, so `prepare` (and
  therefore the prepared-input token) can only be applied to the fit's own input.
* `prepared_input` — granted only by `prepare`, required by `prepared_scorer`.
  Soundness: the scorer can only be fed the prepared form of fit's actual input;
  a fabricated `Matrix(False)` lacks the token (rejected: insufficient
  permission), and cannot acquire it by laundering through `prepare` (which needs
  `raw_fit_input`). This is exactly the discriminator the gold offset value
  depends on (scoring the wrong data yields the wrong `offset_`).

**Soundness check (G-AX):** `check_fit_emits_no_advisory()` runs the REAL
post-patch `IsolationForest.fit` for the F2P case (labelled + `contamination=0.05`)
and the "auto"/unlabelled variants, asserting ZERO advisories, and that
`offset_` is set when `contamination != "auto"`. `check_offset_derives_from_
prepared_training_input()` confirms the gold `offset_` equals
`np.percentile(_score_samples(<prepared training X>), 100*contamination)` and
does NOT equal the offset that scoring a FOREIGN array would yield — grounding
the `prepared_input`/`raw_fit_input` provenance constraint as faithful and
load-bearing. Both run only when gold applied.

### 3.5 Public `score_samples` still validates (patch-independent)
**Soundness check (G-AX):** `check_public_score_samples_still_validates()` feeds
the public `score_samples` an unlabelled array after a labelled fit and asserts
exactly one advisory (`mismatch_advisory(False, True) == 1`) — confirming the
public path still validates its own argument both at base and at gold.

axiom_check.py imports only `sklearn` (the library under change), `numpy`,
`pandas`, and the stdlib; nothing repo-private beyond the documented
`_check_feature_names` / `_validate_data` / `_score_samples` / `_get_feature_names`
helpers the patched code itself uses. Patch-state coupling is handled by gating
the patch-dependent checks on `hasattr(IsolationForest, "_score_samples")`, so
the script returns 0 both with and without `apply_gold` (Defect 4 fix).

## G-CONF (differential conformance: MODEL vs REAL patched repo code)

`conformance_check.py` refutes the refinement leg — does the impl region of
`model.py` actually agree with the real patched repository functions §1 binds it
to? Run in-container with the gold patch applied.

**Pinned seed: `25931`** (module constant `SEED`; also seeds the `random.Random`
and `numpy.random.RandomState` draws, so the verdict is deterministic).

**Shadow.** The impl regions of `validating_scorer` (site 1) and `fit_offset`
(site 2) copied VERBATIM with only the contract calls deleted, plus the `@Pure`
`mismatch_advisory` helper and the two carrier constructors reduced to their
field writes. No transliteration (the model is Python) and no `PSeq` shim (this
model uses no Nagini sequence carrier). The two `@ContractOnly` axioms have no
body to copy, so they are shimmed onto the REAL callees §3 names — `prepare` →
`BaseEstimator._validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)`
(reset=True), `prepared_scorer` → `IsolationForest._score_samples` followed by
the real `numpy.percentile` — and each shim ASSERTS the part of its own
`Ensures` the real callee is claimed to satisfy (zero advisories; unlabelled
prepared form; one score per row), so the axioms are exercised rather than
assumed.

**Oracle.** CALLED, never reimplemented: the live patched
`IsolationForest.fit` (`_iforest.py:268`) for site 2 and the live public
`IsolationForest.score_samples` (`_iforest.py:407`) for site 1.

**Type bridge (§2 inverted).** `has_labels` → `pd.DataFrame(data,
columns=[...])` vs. a bare `np.ndarray` (read back via `_get_feature_names`);
`fitted_with_labels` → `hasattr(est, "feature_names_in_")`; `fit_advisories` →
count of "does not have valid feature names" `UserWarning`s emitted by the call;
`offset_set` → `hasattr(est, "offset_") and contamination != "auto"`;
`calibration_requested` → `contamination != "auto"`.

**Inputs: 105,165** (60,137 real `fit`s at site 2 — 137 boundary incl. the exact
F2P repro + 60,000 fuzz — and 45,028 real `score_samples` calls at site 1 — 28
boundary + 45,000 fuzz), 0 disagreements. The MODELLED input space is finite (8
abstract points: 2 sites × `has_labels` × branch) and is ENUMERATED
EXHAUSTIVELY; the count is then filled by fuzzing the CONCRETE PRE-IMAGES of
those points (shape, values, contamination value, `n_estimators`,
`random_state`, container, dense/CSC-sparse) — stronger than 1e5 samples of an
infinite space. Beyond what §2 models, the concrete offset value is compared
bit-for-bit against the real `est.offset_`, which is what makes the
`raw_fit_input`/`prepared_input` provenance tokens load-bearing.

**Capable of failing.** A built-in `harness_self_test()` runs the PRE-PATCH
shadow (`model_prepatch.py`'s impl region) against the same oracle on the F2P
input and requires it to DISAGREE, so a green cannot come from a
non-discriminating harness. Independently mutation-tested: forcing
`fitted_with_labels := False`, scoring a foreign matrix, reaching the scorer
unconditionally, flipping the `mismatch_advisory` condition, and skipping
`prepare`'s validation each produce exit 1.

### G-CONF finding: the gold patch regresses CSC-sparse + non-`"auto"` contamination
Surfaced by the boundary battery, this is a defect in the instance's
`patch.diff`, NOT in `model.py` and not in the bridge. With CSC-sparse input and
`contamination != "auto"` the patched `fit` raises `ValueError: X should be in
csr_matrix format`, where the pre-patch code returns an offset normally. `fit`'s
preparation pass uses `accept_sparse=["csc"]`, so the prepared matrix is CSC;
pre-patch, the offset path ran through the public `score_samples`, whose
`_validate_data(accept_sparse="csr")` converted CSC→CSR before scoring. The
patch removes exactly that re-validation (the point of the fix), so the CSC
matrix now reaches `tree.apply`, which requires CSR. Upstream scikit-learn later
inserted `if issparse(X): X = X.tocsr()` before the `_score_samples` call in
`fit`; that line is absent here. The P2P test `test_iforest_sparse` misses it
because it never sets `contamination` (default `"auto"` early-returns before the
offset path).

Not routed around: CSC-sparse inputs REMAIN in the input domain and the check
requires both legs to agree on the exception as an observation (same error
identity, same advisory tally). They do agree — the shadow reproduces the raise
because its `prepared_scorer` shim drives the SAME real `_score_samples`. Since
the model abstracts the offset value away and models no error channel, this
divergence lies outside what `model.py` claims and does not falsify the
refinement.
