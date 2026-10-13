# refinement.md — operation correspondence (scikit-learn__scikit-learn-25931)

Maps every op in `implementation_fit` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

Post-patch Python (the modeled tail of `fit`):
```python
if self.contamination == "auto":
    self.offset_ = -0.5
    return self
# Else, define offset_ wrt contamination parameter
# To avoid performing input validation a second time we call
# _score_samples rather than score_samples
self.offset_ = np.percentile(self._score_samples(X), 100.0 * self.contamination)
```
where `_score_samples(X)` runs `check_is_fitted` then
`-self._compute_chunked_score_samples(X)` — and crucially does NOT call
`self._validate_data(X, ..., reset=False)`. The public `score_samples` keeps the
validation; `_score_samples` omits it.

## What the modeled value IS

`implementation_fit` returns a `Fitting`: the fitting tail AS THE PROGRAM IT
RUNS, not merely the values it leaves behind. `Fitting.done r` is a program that
finishes with `r`; `Fitting.traverse v k` performs ONE traversal of the fitted
model over the payload `v` (the chunked scoring pass) and continues as `k`
applied to the anomaly scores that traversal yields. `Fitting.result sc` runs the
program to the values it yields and `Fitting.traversals sc` reads the payloads it
traversed off its structure, both under an INTERPRETATION `sc : Scoring` of what
a traversal yields — and `problem_spec_fit` quantifies over that interpretation,
so every clause holds whatever the anomaly scores of a payload are.

Turning a payload into anomaly scores is real work, performed a definite number
of times, and observable as such: `test_iforest_chunks_works1/2` count it through
`@patch(... get_chunk_n_rows)`. It is modeled as a program CONSTRUCTOR rather
than as a `Nat` field of the result because a field is something the
implementation writes — an impl can report one traversal while performing two,
and no predicate over the returned values can tell. Measured, not argued: against
an earlier model that carried the count as `FitResult.scorePasses`, the two
work-shaped rivals in `properties.py` are provably indistinguishable from the
frozen impl (`implementation_fit = <rival>` closes by
`intro x c f; cases c <;> rfl`), so no clause over the result could reject them.
With the program deep-embedded, a `traverse` node is the only place a traversal
can occur, and the machinery lives in the FROZEN `pure` spec region — so a
variant cannot redefine what counts as a traversal either
(`markers.same_spec` rejects the file).

Deep-embedding alone was measured NOT to be enough, and the second half of the
device is SCOPE. While the score computation was a top-level
`opaque scoreCore : List Float → List Float` it was in scope for the impl region,
so an implementation could reach anomaly scores WITHOUT a `traverse` node:
perform the real work by applying it, discard the result, and also build the node
the contract expects. That class is unreachable by any predicate over `Fitting` —
an unused `let` binder of a pure application is erased by definitional equality,
so the rival IS the same Lean value as the frozen impl (`intro x c f;
cases c <;> rfl` closes `implementation_fit = <rival>`), exactly as the forged
`Nat` field was. So the declaration is gone: there is no term in the file
denoting "the anomaly scores of this payload", the readers are parameterized over
`Scoring`, and the obligation is universally quantified over it. The work is
INEXPRESSIBLE rather than merely unequal.

The SAME device is used for what the fitting leaves behind. `FitResult.scoreLater`
is not a function from a carrier to what a scoring call reports; it is a
`Scored` — the call AS THE PROGRAM IT RUNS — with `Scored.outcome sc` running it
to what it reports and `Scored.traversals sc` reading the payloads it traversed
off its structure, under the same universally quantified interpretation. The
reason is the same and it is measured the same way: presenting a carrier to a
fitted estimator costs chunked traversals of the fitted model, `get_chunk_n_rows`
counts them there exactly as it counts fitting's, and under a plain
`InputData → ScoreOutcome` an entry point that traverses once, twice or not at
all has ONE image. That is not a hypothetical gap: a rival whose stored entry
point performs a discarded warm-up traversal before reporting is, against the
plain-function model, provably the same Lean value as the frozen impl
(`implementation_fit = <rival>` closes by `intro x c f; cases c <;> rfl`), so no
clause over the old types could have rejected it — the same failure the forged
`Nat` field and the in-scope `scoreCore` had. With `Scored` the traversals are
read off the program's structure and cannot be over- or under-reported, and the
type and both readers sit in the FROZEN `pure` region.

**Residual, measured.** `Scoring` is inhabited — it has to be, or `∀ sc` would be
vacuous — so `Classical.arbitrary (α := Scoring)` denotes some function and an
impl may apply it and discard the result; that file elaborates. No clause closes
that, and the defence is the refinement rule instead: a chunked-scoring pass
corresponds to a `Fitting.traverse` node and to nothing else (mapping.md). An
arbitrary inhabitant of `Scoring` denotes no callee of the modeled tail, so an
impl that materializes one and applies it has invented a Python operation its
counterpart does not perform — unmapped invention rather than a refinement of
this tail. Recorded here because the alternative, a clause asserting that the
impl "applies no arbitrary function", is an assertion no control could refute.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let v0 := validateInput xOrig true unrecorded` / `let ref := v0.refAfter` | the model records `feature_names_in_` / `n_features_in_` from the fit-time carrier | R | a labelled table whose labels the estimator admits as names ↔ `hasFeatureNames = true` (mapping.md) |
| 2 | `let x := v0.carrier` (so `x.values = checked xOrig.values`) | `X = self._validate_data(X, accept_sparse=["csc"], dtype=tree_dtype)` at top of `fit` (reset=True) | A-reference | `_validate_data` modeled deeply; reset=True ⇒ no warning, strips carrier metadata, and RE-PRESENTS the payload — what `fit` scores afterwards is this returned object, modeled as `checked`. It does NOT densify: `accept_sparse=["csc"]` admits sparse content and hands it back sparse — and in ITS layout, column-indexed, whichever layout arrived — so `carrier.form := Form.reshaped x.form Form.sparseByColumn` and the tail below inherits a layout its scoring path does not accept (see "Deliberate model limit (STORAGE FORM)"). What it hands back bears no labels at all, so `carrier.namesInspectable := true` — the label question is answerable about it whatever was asked of the caller's presentation (see "PRECONDITION (LABEL INSPECTABILITY)"). Validated == real callee by G-AX. |
| 3 | `if contaminationAuto then Fitting.done {offset := -0.5, warned := false, …}` | `if self.contamination == "auto": self.offset_ = -0.5; return self` | I | identical branch + constant. `done` rather than `traverse`: this arm returns without entering the chunked scoring path at all, so it spends no traversal. |
| 4 | `Fitting.traverse x.values fun scores => …` | `self._score_samples(X)` ⇒ `-self._compute_chunked_score_samples(X)` | I | the score computation is unchanged and is modeled as the traversal EFFECT, not as a callee (mapping.md): the node is applied to the once-validated data (NO second validation pass) and `scores` is what that traversal yields under whichever interpretation the obligation is being checked at. Entering it is the one traversal of the fitted model the configured arm spends, which is what the chunking tests observe via their `get_chunk_n_rows` mock. The real callee is PARTIAL on storage form (it raises on the CSC array row 2 hands back), so the two clauses about what this arm produces are asked only where `fitCompletes` holds; the node itself is unconditional in the impl, exactly as the Python call is. |
| 5 | `let off := percentile scores (100.0*contamination)` | `np.percentile(..., 100.0 * self.contamination)` | I | unchanged callee, identical arithmetic, applied to THE SCORES THAT TRAVERSAL YIELDED — which is what makes a decorative traversal (one whose continuation ignores its argument and re-derives the threshold from the payload) refutable rather than merely unproven |
| 6 | `Fitting.done {offset := off, warned := false, reference := ref, scoreLater := scoreEntry ref}` | `self.offset_ = ...; return self` — `_score_samples` performs no consistency re-check, so no warning | A-reference | the discriminator: routing through `_score_samples` (no `_validate_data(reset=False)`) means `warned = false`. The deep `validateInput` model establishes that omitting the reset=False call drops the warning. `scoreEntry ref` is the stored public scoring entry point as a PROGRAM: `scoreReport` is the report that entry point's own `_validate_data(..., accept_sparse="csr", reset=False)` produces (the same deep `validateInput` model, at the layout THIS path accepts), and `scoreEntry` is `done` on that report when it refuses — the raise happens before the scoring core — and one `traverse` over the carrier the check handed on, continuing to that report, when it does not, mirroring `score_samples`' single entry into `_compute_chunked_score_samples`. The continuation ignores the scores it is handed because `score_samples` returns the negation of that one pass and performs no further traversal; the negation itself is not modeled (mapping.md: the traversal EFFECT is the modeled operation, and every clause is quantified over its interpretation). |

No row above is discharged by consuming an axiom PROPERTY: the proof discharges
the spec via `validateInput`'s definition, the `Fitting` equations, and the
opaque callees' identical appearance in spec and impl. Machine-checked —
`#print axioms correct_fit` reports `[propext, Classical.choice, Quot.sound]`,
i.e. no bundle axiom is used by the proof. No changed-inexpressible op.

**Assumed, consumed by nothing.** `checked_idem` (`checked (checked v) =
checked v`) is a measured fact about the callee that neither the proof nor any
clause's region depends on. It USED to be load-bearing: clause 7 once admitted a
later carrier only when its payload was already in the accepted numeric form
(`z.values = checked z.values`), so `(checked_idem _).symm` was what exhibited a
carrier in its region. That antecedent is gone — clause 7's admission region is
now `z.contentAdmissible = true`, so the clause is non-vacuous on ORDINARY
carriers and its battery witnesses present one directly (see PRECONDITION
(CONTENT ADMISSIBILITY) below). The axiom is retained rather than dropped
because it is independently measured (G-AX leg I re-presents an already-converted
array at three widths and compares content) and because a retained admissible
eq-attack rival consumes it, so removing it would silently void that rival's
replay. Justification for the axiom itself is unchanged: re-presenting content
that `check_array` has already converted is a content no-op, which is why the
real `fit` can hand its validated array to `_score_samples` without a second
conversion.

## Discriminating clause
`result.warned = false` (`fitting.result.warned` in the shipped spec). The
PRE-patch impl routes the contamination branch through the public scorer =
`validateInput x false ref`, whose warning is
`(!false) && x.namesInspectable && (ref.hasFeatureNames != x.hasFeatureNames)`.
The carrier handed to the scorer is the internal array, whose metadata the first
validation stripped (`x.hasFeatureNames = false`) and about which the label
question is answerable (`x.namesInspectable = true`), so this is
`ref.hasFeatureNames` — the metadata status the fit recorded. For a
feature-named carrier (`xOrig.hasFeatureNames = true`, `contaminationAuto =
false`) it is `true`, contradicting
`problem_spec_fit`'s `fitting.result.warned = false` conjunct — so the prepatch
`correct_fit` cannot close. That is the G-DIFF signal, and it mirrors exactly the
F2P non-regression test (`test_iforest_preserve_feature_names`, which sets
`UserWarning → error`).

## Modeled-but-not-in-`patch.diff` observables

Three observables are pinned by the spec although the diff does not change them;
all three are unchanged behavior the fix must PRESERVE, and each is needed
because a diagnostic-only contract cannot see it:

- `Fitting.traversals` — which payloads fitting traverses the fitted model over,
  and how many times. The configured branch spends exactly one traversal, over
  the validated training payload, and the auto branch none — both before and
  after the patch. `sklearn/ensemble/tests/test_iforest.py::test_iforest_chunks_works1/2`
  pin this via `@patch(... get_chunk_n_rows)` and
  `@pytest.mark.parametrize("contamination, n_predict_calls", [(0.25, 3), ("auto", 2)])`;
  subtracting the two traversals the test body's `decision_function` + `predict`
  contribute leaves 1 and 0 for `fit`.
  Against this program model both work-shaped rivals are excluded by REFUTATION,
  not by a tactic that merely fails to close: ported region-for-region onto the
  frozen spec (`markers.same_spec` true, `variant_scope.unsound_evasions` empty),
  the rival that hoists the traversal above the branch is left with
  `[checked xOrig.values] = []` on the constant arm, the rival that adds a
  discarded warm-up traversal is left with
  `[checked xOrig.values, checked xOrig.values] = [checked xOrig.values]`, and
  `¬ problem_spec_fit …` is provable for each at a concrete carrier.
- `result.reference` — the description of admissible input the fitted estimator
  holds (`n_features_in_`, and whether `feature_names_in_` is set). Taken from
  the training carrier alone by the single `reset=True` validation.
- what ONE call to the fitted estimator's public scoring entry point COSTS:
  `((fitting.result sc).scoreLater z).traversals sc`. A refused call spends
  nothing — it raises out of the feature-name/feature-count checks before the
  scoring core is reached — and an accepted call spends exactly one chunked
  traversal, over the carrier its own check handed on. Unchanged by the diff (both
  before and after, `score_samples` enters `_compute_chunked_score_samples` once
  per accepted call) and pinned for the same reason `Fitting.traversals` is: the
  count is observable from outside and is not the estimator's to choose.
  `test_iforest_chunks_works1/2` measure it through the same
  `@patch(... get_chunk_n_rows)` mock, and their
  `@pytest.mark.parametrize("contamination, n_predict_calls", [(0.25, 3), ("auto", 2)])`
  counts a TOTAL: the auto row's 2 is the test body's `decision_function` plus
  `predict` with `fit` spending 0, i.e. one traversal per accepted scoring call,
  and the configured row's 3 is those two plus fitting's one.
  Stated as a function of what the call REPORTS rather than as a constant, so it
  pins the call's shape (free when refused, one pass over the crossing carrier
  when not) instead of an incidental number, and it is the crossing carrier's
  payload rather than the caller's — an entry point that converts correctly,
  reports correctly and then traverses the model over its own raw argument is a
  break the crossing-carrier equation cannot see, because that equation constrains
  what crosses and not what is scored.
  Excluded by REFUTATION, not by an unclosable tactic: ported region-for-region
  onto the frozen spec (`markers.same_spec` true), the rival whose accepting lane
  performs a discarded warm-up pass is left with
  `[v, v] = [v]`, the rival whose accepting lane reports without traversing at all
  with `[] = [v]`, the rival that traverses on the REFUSING lane with `[v] = []`,
  and the rival that traverses over the caller's payload with
  `[z.values] = [checked z.values]` at a carrier where the two differ — and
  `¬ problem_spec_fit …` is provable for each at a concrete carrier
  (`properties.py`, the four score-time reject cases).
- `scoreLater.handedOn` — the CARRIER that entry point hands the fitted model.
  The check that licenses a carrier's crossing into the model's own presentation
  is separable from the crossing itself, so an entry point can run every
  admissibility check correctly, report every flag correctly, and still hand the
  model its own argument rather than the object the check re-presented. Nothing
  about the outcome's booleans or its record differs, so a contract over flags
  alone cannot reach it. Not hypothetical: built on the real repository in that
  shape (public scorer performs the feature-name and feature-count checks, then
  calls the non-validating private scorer on its raw argument), the FAIL_TO_PASS
  test passes and four PASS_TO_PASS bodies fail — it verifies and does not
  resolve. Grounded against the real callee by `axiom_check.py` legs H/P (the
  entry point accepts a payload the scoring core refuses, so the value that
  crosses is demonstrably the check's output) and by G-CONF tier B, which spies
  on `_compute_chunked_score_samples` and compares the payload it is handed.

  It is a whole `InputData` and not a `List Float` because what crosses is the
  estimator's OWN presentation of the data, and a presentation describes itself.
  An entry point can convert the content correctly and hand the model that
  content still wearing the CALLER's account of itself — its label status, its
  inspectability, its admissibility — which is a second break in the same place
  that a payload equation cannot see, and it is the reading C5's fourth leg
  admitted while it pinned only `checked z.values`. It can also convert the content
  and describe it correctly and hand it on in the sparse LAYOUT its own scoring
  path refuses: which of the two sparse layouts the crossing value carries is the
  entry point's own choice, since it chooses which layout its check accepts, and
  the scoring path is partial on exactly that choice. A sparseness bit could not
  see it — both choices are "still sparse" — so the observable is three-valued and
  the equation names the layout THIS entry point's check accepts. The leg is
  therefore ONE record equation over all six fields: the presented width, the
  storage form this step hands content back in, no feature-name metadata of its
  own, content the check accepts and labels it will inspect. Each of the three self-description fields is a question the
  real callee answers, and answers differently elsewhere, which is what makes the
  equation an obligation rather than a restatement: `axiom_check.py` leg E asks
  all three of the object `_validate_data` hands back (its width, the layout it
  is handed back in, whether the label inspection answers for it, whether
  re-presenting it is accepted) with the name-bearing caller's carrier as the in-loop control — 306
  observations, 90 of them under a caller's carrier that DOES bear labels, 0
  mismatches; rewriting that control to assert the collapsed reading instead
  ("the presentation's label description is the caller's") yields 90 mismatches
  and exit 1, so the leg is refutable. Legs L and D are the refuting controls for
  the other two halves: there are carriers the label inspection will not answer
  for and contents the check declines, so "inspectable and admissible" is not a
  property everything has. G-CONF tier B reads all six fields off the object the
  scoring core was ACTUALLY handed, and its `forward-caller-description` mutation
  — content converted correctly, description taken from the caller — is caught.
  The two rivals the leg now rejects are
  `later-scoring-hands-on-caller-description`, which the payload equation
  admitted, and `later-scoring-hands-on-unscorable-layout`, which every equation
  over a two-valued storage form admitted — the latter measured on the real
  repository in exactly that shape (the public scorer admits its argument in the
  layout the FITTING end accepts rather than the one its own scoring path
  consumes): the FAIL_TO_PASS test passes and a PASS_TO_PASS body fails, i.e. it
  verifies and does not resolve. The layout legs of `axiom_check.py` (leg F) ask
  each end of the tail for all three presentations of the same numbers and
  require the scoring path to traverse the layout this entry point hands on and to
  REFUSE the other one, so the pinned layout is the one value that keeps the
  crossing scorable rather than an arbitrary choice; G-CONF tier B asserts the
  layout of the object the scoring core was actually handed and runs that
  two-layout control on every sparse crossing.
- `scoreLater`'s flags — the behavior of the fitted estimator's public scoring
  entry point. The record it enforces and its warning behavior are unchanged by
  the diff; the spec pins them so that an impl cannot pay for `warned = false` by
  breaking the public scorer (the diff explicitly keeps validation there). This
  is not decoration: an impl can silence the diagnostic HONESTLY by switching the
  second pass from a check to a re-description, which was built and measured on
  the real repository — it passes the F2P test and fails a P2P test, i.e. it
  verifies and does not resolve.

## Deliberate model limit (name PRESENCE, not name IDENTITY)

`InputData.hasFeatureNames` records only WHETHER the estimator admits names for a
carrier, never WHICH names. Two carriers differing only in their column labels
share one image in this model.

The real estimator refuses a carrier whose names DISAGREE with the recorded ones
(`BaseEstimator._check_feature_names`, unchanged by the diff, raises "The feature
names should match those that were passed during fit"). Measured against the real
post-patch code: an `IsolationForest` fitted on a frame with columns
`[a, b, c]` RAISES when scored with those columns permuted, and RAISES for
columns `[f0, f1, XX]`.

So the spec's two admission clauses are stated only where a name comparison
CANNOT arise:

- clause 6 (the training carrier stays admissible to its own fit) is guarded by
  `xOrig.hasFeatureNames = false`;
- clause 7 (a carrier whose content the check accepts, at the training width, is
  admitted) carries the antecedent
  `xOrig.hasFeatureNames = false ∨ z.hasFeatureNames = false`.

Where either side bears no names there is nothing to compare, the naming question
is settled by the warning equation in clause 5, and the real code does not raise
— it warns and carries on. Where BOTH sides bear names the model cannot see
whether the two label sets agree, so the spec claims nothing, and the faithful
impl that refuses there conservatively must verify. That is not left to argument:
`properties.py::pos-name-identity-refusal` is that impl (`refused := v.refused ||
(z.hasFeatureNames && ref.hasFeatureNames)`) and is a soundness case the gate
builds. Narrowing rather than deleting is what keeps the clauses load-bearing —
`later-scoring-refuses-everything` is still rejected by clause 6 and
`names-treated-as-inadmissibility` (which escalates a NAMELESS carrier's absent
metadata into a refusal) is still rejected by clause 7.

Absent metadata is never itself a ground for refusal in the real code, in either
direction: fitting on a frame and scoring an array, or fitting on an array and
scoring a frame, both warn and return.

## Deliberate model limit (STORAGE FORM)

`InputData.form` records the carrier's storage form — three-valued (`dense`,
`sparseByRow`, `sparseByColumn`), because the operation on the far side is partial
on WHICH sparse index the content carries and not merely on sparseness — and
`fitCompletes x auto = auto || (Form.reshaped x.form Form.sparseByColumn).traversable`
(frozen `pure` region) records which runs of the tail reach a result at all. The two clauses about what such a run
PRODUCES — clause 3, the derived threshold, and clause 8, the traversal record —
are asked only where `fitCompletes` holds. Everything else in the description is
unconditional.

Why, measured against the real callees rather than argued:

- the fit-time check ADMITS a sparse carrier and hands it back sparse, in the one
  sparse layout it accepts: `check_array(X, accept_sparse=["csc"],
  dtype=np.float32)` returns CSC for a CSC input *and* for a CSR input, so a
  sparse presentation reaches the tail column-indexed however it arrived. That is
  `Form.reshaped x.form Form.sparseByColumn`, and it is why the reshaping takes the
  accepted layout as an argument: the layout content comes back in is a property
  of the STEP, not of the caller — the check the public scoring entry point uses
  (`accept_sparse="csr"`) hands the same two presentations back ROW-indexed;
- the scoring path the patched tail then enters refuses the column-indexed layout:
  `_compute_chunked_score_samples` on the checked CSC array raises
  `ValueError: X should be in csr_matrix format`, for an estimator fitted on any of
  the three presentations — while the DENSE presentation of the same numbers, and
  the row-indexed one, are traversed and scored. So the refusal is a property of
  the LAYOUT, not of sparseness, not of the payload, and not of how the estimator
  was fitted; `Form.traversable` names the two layouts it consumes;
- end to end on the patched code: `fit(sparse carrier, configured level)` raises
  with no `offset_` assigned and `n_features_in_` already recorded;
  `fit(sparse carrier, "auto")` returns with `offset_ = -0.5`; both dense forms
  return normally. On the PRE-change code all four calls return, so this
  divergence is introduced by the change under test — the model is describing
  the patched behaviour, which is what the obligation is about.

An unguarded clause 3 or 8 would therefore assert a threshold and one completed
traversal for a run that raises: over-strength, and a real faithfulness defect
rather than a conservative one, because a faithful implementation of the patched
tail CANNOT satisfy it. The guard is a NARROWING in the same style as the
name-identity limit above, and it is bounded on three sides, each machine- or
container-checked:

- `properties.py::pos-sparse-declines-threshold` — the faithful counterpart that
  declines to invent a threshold exactly where the traversal is impossible is a
  soundness case and MUST verify (it does);
- `properties.py::sparse-guard-inverted` — a rival that reads the limit as a
  general licence, spending its traversal only where the description withholds
  its claims and handing a dense configured fit a constant, is REJECTED by clause
  8 on a dense carrier;
- `properties.py::sparse-abort-emits-diagnostic` — a rival that reads the
  withheld threshold as a withheld run, surfacing the feature-name diagnostic on
  the way out of the abort, is REJECTED by clause 1 at a SPARSE carrier. That is
  what scopes the limit to two clauses: clauses 1, 4, 5, 6 and 7 carry no storage
  antecedent, and the aborted run really is observed to emit no diagnostic, to
  leave the training carrier's record behind, and to enforce it afterwards.

Grounded mechanically outside Lean on both sides, because a domain limit no
control can refute is indistinguishable from a hole: `axiom_check.py`'s legs S and F
call the real check and the real scoring path at two widths × all three storage
forms and assert the column-indexed refusal, the row-indexed traversal and the
dense acceptance (the last two are the negative controls — it fails if the collapsed reading, that the two forms are
one carrier, were right), and `conformance_check.py`'s real-code leg asserts
`fitCompletes` against the patched estimator in BOTH directions on every draw, for
a row-indexed training carrier as well as a column-indexed one
(the tail must abort exactly where the guard says and complete everywhere else),
compares the record each aborted run established, and fits the same numbers
densely as a per-abort control. Two of that gate's mutations abuse the limit in
either direction — traversing on the sparse unconfigured lane, and declining
every sparse carrier — and both are caught, so the sparse UNCONFIGURED lane is
demonstrably still under the full obligation.

`fitCompletes` lives in the FROZEN spec region, so a variant cannot redefine
which runs the two clauses cover (`markers.same_spec` rejects the file).

## PRECONDITION (LABEL INSPECTABILITY)

Three carriers appear in this tail: the presentation the caller hands `fit`, the
object the fit-time check hands back, and the later carrier presented to the
fitted estimator's public scoring entry point. All three inhabit one Lean type,
`InputData`, which is the right abstraction only if every distinction the real
callees draw between them is expressible in its fields. With `hasFeatureNames`
alone it is not: that field forces every carrier into "bears names" or "bears
none", and BOTH of those are cases the estimator can ANSWER. There is a third.

Measured against the real callee: `sklearn.utils.validation._get_feature_names`
RAISES `TypeError` for a frame whose column labels are of MIXED kinds — some
textual, some not (`pd.DataFrame(..., columns=["c0", 1])`) — rather than
returning a label list or `None`. A frame whose labels are ALL non-string is a
different case: it returns `None`, i.e. `hasFeatureNames = false`. And
`_validate_data` calls `_check_feature_names` (hence that inspection) before
`_check_n_features`, at fit time and at score time alike, so the raise happens
before any width or name comparison.

`InputData.namesInspectable : Bool` carries that case, and the model uses it in
OPPOSITE directions on the two ends of the tail:

- the training carrier: the whole obligation is stated under
  `xOrig.namesInspectable = true`. A fit on any other presentation raises inside
  the first validation, leaving neither a threshold nor a width record behind, so
  there is no fitted estimator for the description to describe. Withholding the
  description exactly there is a domain limit; withholding it anywhere else would
  be a weakening.
- the later carrier: clause 5 gains a FIFTH leg,
  `z.namesInspectable = false → refused = true` — a POSITIVE obligation, not a
  guard. The entry point must turn such a carrier away. The warning leg and
  clause 7 are the two places that had to be guarded by
  `z.namesInspectable = true`, because a name-status delta and an admission are
  both things the real path only reaches for labels it can inspect.

So the repair is not a narrowing on balance: one antecedent is added at the fit
end and one obligation is added at the scoring end. What it closes is a rival
that reads the collapse literally — an entry point that checks the width, finds
it agrees, and hands the model a carrier whose labels the real code refuses to
work with.

Grounded outside Lean on both sides, because a precondition no control can
refute is indistinguishable from a hole:

- `axiom_check.py` leg L presents mixed labels at three widths, both to the
  inspection itself and through the fitted estimator's public scoring path, AT
  THE TRAINING WIDTH so no width check could account for the refusal — and on
  every observation the homogeneously labelled carrier of the SAME payload at the
  SAME width is the negative control: it is read and scored. The precondition
  half is measured too: the fit raises, leaves no threshold, and the
  homogeneously labelled control fit produces one. Every control is a hard
  failure of the leg if it stops discriminating, and a leg that never fires is a
  failure as well.
- `conformance_check.py` tier B asserts the precondition against the patched
  estimator in BOTH directions on every draw (the fit must raise exactly where
  `namesInspectable` is false and complete everywhere else), asserts that such a
  fit leaves neither `offset_` nor `n_features_in_`, fits the same numbers under
  homogeneous labels as a per-abort control, and asserts that every uninspectable
  probe is turned away BY THE LABEL INSPECTION at the training width, with the
  homogeneous presentation of the same numbers accepted there. Four of that
  gate's mutations abuse the limit in either direction — dropping the
  precondition, over-claiming it onto merely unlabelled carriers, admitting an
  uninspectable later carrier on a width check, and reporting a name-status delta
  for labels that were never readable — and all four are caught.
- in Lean, `properties.py::pos-uninspectable-fit-declines` is the soundness
  control for the precondition: an impl that returns a refusing, warning
  placeholder for a carrier it cannot inspect MUST verify, and does. Its rival
  `properties.py::later-scoring-admits-uninspectable` is the collapsed reading
  itself — refusal on the width alone — and is REJECTED by clause 5's fifth leg
  at a concrete carrier.

`namesInspectable` and the precondition live in the FROZEN spec regions, so a
variant can neither redefine the case nor drop the antecedent
(`markers.same_spec` rejects the file).

## PRECONDITION (CONTENT ADMISSIBILITY)

The three carriers of the section above are distinguished by one more thing the
real callees see and `hasFeatureNames`, `form` and `namesInspectable`
together cannot express: whether the admissibility check accepts the carrier's
CONTENT at all. Establishing admissibility is not a pure inspection — the check
RE-PRESENTS the content in the numeric form the fitted model operates in — and
that step is partial in its content argument, not only in its labels.

Measured against the real patched callee: `check_array` (via `_validate_data`)
RAISES `ValueError` for content with no rows to describe, for content with no
columns to describe, and for content holding a value that is not finite. The
raise happens after `_check_feature_names` and before `_check_n_features`, so the
naming question is already settled and reported when the content is declined, and
the width is never reached. None of the three is a label case: each is a bare
array, so the label inspection answers about all three, and answers "no names".
None of them is a storage-form case either: the check ADMITS sparse content and
hands it back sparse, in its own layout, which is a different fact about a
different field.

`InputData.contentAdmissible : Bool` carries that case, and — like label
inspectability — the model uses it in OPPOSITE directions on the two ends of the
tail:

- the training carrier: the whole obligation gains a second antecedent,
  `xOrig.contentAdmissible = true`. A fit on content the check declines raises
  inside the first validation, leaving neither a threshold nor a width record
  behind, so there is no fitted estimator for the description to describe.
- the later carrier: clause 5 gains a SIXTH leg,
  `z.contentAdmissible = false → refused = true` — a POSITIVE obligation, not a
  guard. The entry point must turn such a carrier away, whatever its width and
  whatever the estimator holds on record. Unlike the inspectability leg, the
  WARNING leg is NOT guarded by it: the naming question is settled before the
  content is re-presented, so a diagnostic about the carrier's feature-name status
  is surfaced even on a call that then turns it away. That asymmetry is measured,
  not assumed.

Clause 7 is the third place the field appears, and there it replaces something.
Clause 7 used to admit a later carrier only where `z.values = checked z.values` —
where the check hands the content back as it found it. That antecedent was a
hole, not a limit: it left refusal entirely free for every carrier the check has
to convert, which is most of what the entry point exists to accept. Its
replacement is `z.contentAdmissible = true`, so clause 7 now claims admission for
content the check ACCEPTS whether or not it rewrites it — the same terms for both
— and the rival that turned away every carrier it had to convert is refuted
rather than licensed.

So this repair, like the previous one, is not a narrowing on balance: one
antecedent is added at the fit end, one obligation is added at the scoring end,
and one antecedent is REMOVED from clause 7, widening it.

Grounded outside Lean on every side, because a precondition no control can refute
is indistinguishable from a hole:

- `axiom_check.py` leg D presents each of the three declined contents at three
  widths, at fit time and through the fitted estimator's public scoring path, with
  the ordinary content of the same width as the negative control on every
  observation: the control fits, records its width and scores. The leg also
  asserts each declined content is one the label inspection ANSWERS about, which
  is what shows it is not leg L again under another name. A leg that never fires
  and a control that never fires are both hard failures of the probe.
- `conformance_check.py` tier B asserts the precondition against the patched
  estimator in BOTH directions on every draw, and reads WHICH step declined off
  the estimator rather than assuming it: the re-presentation runs before the width
  is recorded, so a record left behind means the run got past the check and
  aborted later inside the scoring path. It asserts that a content abort leaves
  neither `offset_` nor `n_features_in_`, fits the ordinary content of the same
  width as a per-abort control, presents declined content AT THE TRAINING WIDTH to
  the fitted estimator's public scoring path (so no width check can account for
  the refusal) and asserts it is turned away with the ordinary content of the same
  width accepted, and asserts the name diagnostic still stands on that refused
  call. Four of that gate's mutations abuse the limit in either direction —
  dropping the content precondition, over-claiming it onto every carrier the check
  converts, admitting an inadmissible later carrier on a label-and-width check,
  and escalating "the check had to convert this content" into a refusal — and all
  four are caught.
- in Lean, `properties.py::pos-inadmissible-content-fit-declines` is the
  soundness control for the precondition: an impl that returns a refusing,
  warning placeholder for content the check declines MUST verify, and does. Its
  two rivals are `later-scoring-admits-inadmissible-content` (the entry point
  that drops the content ground, REJECTED by clause 5's sixth leg) and
  `content-rewrite-treated-as-inadmissibility` (the entry point that refuses
  everything it had to convert, REJECTED by clause 7 on exactly the region the
  removed antecedent used to carve out).

`contentAdmissible`, the second precondition, clause 5's sixth leg and clause 7's
antecedent list all live in the FROZEN spec regions, so a variant can neither
redefine the case, drop the antecedent, nor reinstate the fixed-point restriction
(`markers.same_spec` rejects the file).
## PRECONDITION (CONFIGURED THRESHOLD LEVEL)

The three preceding limits are all about a CARRIER. This one is about the
configured threshold level itself, and it is prior to all of them: the model gives
that level a bare `Float` binder, while the real estimator DECLARES the parameter's
domain and validates it before it looks at a carrier at all.

Measured against the real patched callee:
`IsolationForest._parameter_constraints["contamination"]` admits either the
unconfigured marker `"auto"` or a real number in the interval `(0, 0.5]`, and
`self._validate_params()` is the FIRST statement of `fit` — ahead of
`_validate_data`, hence ahead of the label inspection, the content re-presentation
and the width record. A level outside that interval therefore raises
`InvalidParameterError` (a `ValueError`) out of parameter validation, and the run
ends with no threshold, no recorded width, no traversal of the training payload
and no estimator that can score. Fitting at a level inside it completes with
exactly ONE traversal, which is the count clause 8 pins.

`levelAdmitted : Float → Bool` in the axioms region carries the estimator's
verdict on a level, and the obligation is stated under
`contaminationAuto = false → levelAdmitted contamination = true`, first in the
antecedent list because the real validation is first in the run. Three things
about that shape:

- It is an IMPLICATION over the branch selector, not a constraint on the binder,
  because the pair `(contaminationAuto = true, contamination = c)` models the
  unconfigured marker — where the real parameter holds no level at all and the
  validation never looks at one. A run carrying an arbitrary `c` alongside the
  marker is therefore described in FULL, and the unconfigured-lane witnesses in
  `properties.py` discharge the precondition outright at their literals.
- It is an OPAQUE Bool rather than a Float interval, and that is a usability fact
  about this carrier rather than a modelling preference: `Float` order comparison
  has no kernel-reducible `Decidable` instance here, so an interval antecedent
  would make even `0.25` a level nothing in a proof could show admitted, and every
  witness would have to condition on the comparison anyway. The verdict is exactly
  a function of the level, which is what an opaque `Float → Bool` says and all it
  says.
- The model does NOT pin WHICH levels are admitted. That is what keeps this a
  precondition rather than a constant smuggled into the spec: nothing in the
  bundle consumes a property of `levelAdmitted`, and no axiom constrains it.

The repair is not a narrowing on balance either. Nothing is withheld on the
unconfigured lane, and on the configured lane the region removed from the
description is exactly the region where the real fit raises before doing anything
at all — so what is withheld is a description of a run that does not happen, while
every level the estimator serves is still described.

Grounded outside Lean on both sides, because a precondition no control can refute
is indistinguishable from a hole:

- `axiom_check.py` leg V reads the real verdict in BOTH directions at two widths:
  at every level the battery configures (and the interval's closed upper endpoint)
  the fit must complete, leave both attributes behind, traverse the training
  payload EXACTLY ONCE — counted by instrumenting the chunked scoring routine the
  model's traversal node stands for — and score; at levels outside the interval
  (including its open lower endpoint) it must raise ABOUT THAT PARAMETER, leave
  nothing behind, traverse ZERO times and leave nothing that can score. The levels
  the battery configures are the refuting control for the ones outside: a leg where
  everything raised would be indistinguishable from "this estimator never fits".
  The leg also measures the ORDER as a contrast — a refused level over content the
  admissibility check declines raises about the parameter, while the same content
  at an admitted level raises about the content — which is what shows the
  validation is FIRST and not merely present. Measured: 50 observations, 0
  mismatches, 26 admitted and 22 refused readings, and the collapsed reading (the
  level binder is unconstrained, so every `Float` is a level the estimator works
  with) is REFUTED by the same leg when asserted as a control.
- `conformance_check.py` draws its configured level inside the declared interval,
  so every draw of that gate compares the shadow against a run the description
  covers; the out-of-domain direction is measured where the real callee is, in
  leg V.
- in Lean, `properties.py::pos-declines-refused-level` is the soundness control:
  an impl that declines to invent a threshold exactly where the validation refuses
  the level MUST verify, and does. The precondition is load-bearing rather than
  decorative — that impl's configured branch closes only by APPLYING it, and
  against a description without it the same impl is REFUTED at a refused level,
  measured during authoring. `admiss-f2p-shaped-input` is the control in the other
  direction: its ground `have` INTRODUCES the precondition and never uses it, so
  the level the failing test configures is described unconditionally and the
  precondition cannot be hollowing the obligation out at the input this change is
  about.

`levelAdmitted` and the precondition live in the FROZEN spec regions (axioms and
post-conditions), so a variant can neither redefine the verdict nor drop the
antecedent (`markers.same_spec` rejects the file).
