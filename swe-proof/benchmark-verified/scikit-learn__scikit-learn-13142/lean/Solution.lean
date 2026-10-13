import Mathlib
-- imports-end

/-!
Model of an estimator that performs several independent fitting trials and then
assigns labels to the data. Each trial yields a candidate parameter
configuration together with a numeric quality score; the procedure keeps the
configuration of the highest-scoring trial and must report the label assignment
that this selected configuration produces.

A trial is modeled as `(config, score)` where `config : Int` identifies a fitted
parameter configuration and `score : Int` is the (order-only) quality score.
Real-valued scores are modeled as `Int` because only their ORDER matters for the
selection (DECISIONS.md: kernel `Float` order is opaque to tactics).
-/

-- axioms-start
/-- The label assignment produced for a given parameter configuration. This is
the unchanged downstream label-computation callee; we need only that it is a
deterministic function of the configuration it is applied to (no property is
consumed by the proof, so it is declared `opaque` with no `_prop` axiom). -/
opaque labelsOf : Int → List Nat
-- axioms-end

-- pure-start
/-- Fold step selecting the best trial seen so far. Keeps the running best
unless the incoming trial's score is STRICTLY greater (so the earliest trial
attaining the maximum score wins ties). -/
def stepBest (acc : Option (Int × Int)) (t : Int × Int) : Option (Int × Int) :=
  match acc with
  | none => some t
  | some (bp, bs) => if t.2 > bs then some t else some (bp, bs)

/-- The configuration of the highest-scoring trial (earliest on ties), or `none`
when there are no trials. -/
def bestParam (trials : List (Int × Int)) : Option Int :=
  (trials.foldl stepBest none).map (·.1)
-- pure-end

-- post-conditions-start
/-- The reported labels are exactly those produced by the SELECTED (highest
scoring) trial's configuration; with no trials the result is empty. Both output
branches are pinned (frame discipline: no result component left free). -/
def problem_spec_fit_predict (trials : List (Int × Int)) (result : List Nat) : Prop :=
  (∀ b, bestParam trials = some b → result = labelsOf b) ∧
  (bestParam trials = none → result = [])
-- post-conditions-end

-- impl-start
def implementation_fit_predict (trials : List (Int × Int)) : List Nat := Id.run do
  let mut best : Option (Int × Int) := none
  for t in trials do
    match best with
    | none => best := some t
    | some (_, bs) => if t.2 > bs then best := some t
  match best with
  | none => return []
  | some (bp, _) => return labelsOf bp
-- impl-end

-- proof-start
/-- The desugared `forIn` loop body equals folding `stepBest` over the trials,
generalized over the accumulator. -/
theorem loop_helper (trials : List (Int × Int)) (init : Option (Int × Int)) :
    (forIn (m := Id) trials init (fun t r =>
      match r with
      | none => pure (ForInStep.yield (some t))
      | some (_, bs) => if t.2 > bs then pure (ForInStep.yield (some t)) else pure (ForInStep.yield r)))
    = trials.foldl stepBest init := by
  induction trials generalizing init with
  | nil => rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    simp only [bind] at ih ⊢
    cases init with
    | none => simp only [ih, List.foldl_cons, stepBest]
    | some p =>
      obtain ⟨bp, bs⟩ := p
      by_cases h : a.2 > bs <;> simp only [h, if_true, if_false, ih, List.foldl_cons, stepBest]

theorem correct_fit_predict :
    ∀ trials : List (Int × Int), trials ≠ [] →
      problem_spec_fit_predict trials (implementation_fit_predict trials) := by
  intro trials _
  unfold implementation_fit_predict
  simp only [Id.run, bind]
  rw [loop_helper trials none]
  constructor
  · intro b hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rw [hf] at hb; simp at hb
    | some p => rw [hf] at hb; obtain ⟨bp, bs⟩ := p; simp at hb; simp only [hb]; rfl
  · intro hb
    unfold bestParam at hb
    cases hf : trials.foldl stepBest none with
    | none => rfl
    | some p => rw [hf] at hb; simp at hb
-- proof-end

#print axioms correct_fit_predict
