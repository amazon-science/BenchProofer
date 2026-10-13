import Mathlib
-- imports-end

/-!
Selecting the probability estimates a multiclass linear classifier reports.

A linear classifier that has been configured for a multiclass problem can report
per-class probability estimates in one of two regimes, chosen by a mode setting:

* the one-vs-rest regime maps each class's real-valued score through the logistic
  function and then normalises those values so the per-sample estimates sum to
  one; and
* the multinomial regime maps the whole row of per-class scores through the
  softmax function (exponentiate, then normalise so the row sums to one).

When a model is asked to produce the probability estimates that feed a
probabilistic evaluation, the regime actually used must be the one requested for
the multiclass problem. In particular, when the multinomial regime is requested,
the reported estimates must be the softmax of the score rows — not the
one-vs-rest values. The two regimes disagree on every nontrivial score row, so a
model that always reports one-vs-rest estimates diverges from the requested
behavior whenever the multinomial regime was requested.

Inputs are the requested multiclass mode (the string identifying the regime) and,
for each candidate solution, the matrix of per-sample, per-class real-valued
scores (the decision-function output). The output is, for each candidate, the
matrix of per-class probability estimates obtained by applying the requested
regime row by row, in the same order.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed as an axiom. The probability
-- transforms (logistic-then-normalise and softmax) are modeled DEEPLY over the
-- real-valued score rows that are the observable input, so no `opaque`/`axiom`
-- callee contract is required (G-AX validates these transforms against the real
-- probability routine; G-CONF exercises the mode selection and framing).
-- axioms-end

-- pure-start
/-- The logistic (sigmoid) function on a real score. -/
noncomputable def sigmoid (x : ℝ) : ℝ := 1 / (1 + Real.exp (-x))

/-- One-vs-rest estimates for a single score row: each score through the logistic
function, then normalised so the row sums to one. -/
noncomputable def ovrRow (row : List ℝ) : List ℝ :=
  let s := row.map sigmoid
  let tot := s.sum
  s.map (fun v => v / tot)

/-- Softmax estimates for a single score row: exponentiate each score, then
normalise so the row sums to one. -/
noncomputable def softmaxRow (row : List ℝ) : List ℝ :=
  let e := row.map Real.exp
  let tot := e.sum
  e.map (fun v => v / tot)

/-- The two probability regimes. -/
inductive ProbMode where
  | ovr
  | multinomial
deriving DecidableEq, Repr

/-- The mode identified by the requested multiclass string: the multinomial
regime is requested by `"multinomial"`; any other value selects one-vs-rest. -/
def parseMode (s : String) : ProbMode :=
  if s = "multinomial" then ProbMode.multinomial else ProbMode.ovr

/-- The probability estimates for one score row under a given regime. -/
noncomputable def predictProbaRow (m : ProbMode) (row : List ℝ) : List ℝ :=
  match m with
  | ProbMode.ovr => ovrRow row
  | ProbMode.multinomial => softmaxRow row

/-- The probability estimates for a whole score matrix: the regime applied to
each row, in order. -/
noncomputable def predictProba (m : ProbMode) (decision : List (List ℝ)) : List (List ℝ) :=
  decision.map (predictProbaRow m)
-- pure-end

-- post-conditions-start
/-- For each candidate's score matrix, the reported estimates are exactly the
probability estimates of that matrix under the regime requested for the
multiclass problem, in the same order; the number of candidates is preserved. -/
def problem_spec_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ)))
    (result : List (List (List ℝ))) : Prop :=
  result = decisions.map (fun d => predictProba (parseMode multiClass) d)
-- post-conditions-end

-- impl-start
noncomputable def implementation_scoringProbs
    (multiClass : String) (decisions : List (List (List ℝ))) :
    List (List (List ℝ)) := Id.run do
  let mode := parseMode multiClass
  let mut out : List (List (List ℝ)) := []
  for d in decisions do
    out := out ++ [predictProba mode d]
  return out
-- impl-end

-- proof-start
theorem forIn_append_helper {α β : Type} (f : α → β) (xs : List α) (init : List β) :
    (Id.run (do
        let r ← forIn xs init (fun d r => do
          pure PUnit.unit
          pure (ForInStep.yield (r ++ [f d])))
        pure r)) = init ++ xs.map f := by
  induction xs generalizing init with
  | nil => simp [Id.run]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [Id.run, bind] at ih ⊢
    rw [ih]
    simp [List.map_cons]

theorem correct_scoringProbs :
    ∀ (multiClass : String) (decisions : List (List (List ℝ))),
      problem_spec_scoringProbs multiClass decisions
        (implementation_scoringProbs multiClass decisions) := by
  intro multiClass decisions
  unfold problem_spec_scoringProbs implementation_scoringProbs
  rw [forIn_append_helper (fun d => predictProba (parseMode multiClass) d) decisions []]
  simp
-- proof-end
