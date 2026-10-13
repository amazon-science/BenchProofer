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
  let mut lastConfig : Option Int := none
  for t in trials do
    lastConfig := some t.1
    match best with
    | none => best := some t
    | some (_, bs) => if t.2 > bs then best := some t
  -- Bug: the reported labels are computed from the configuration left after the
  -- final trial rather than from the selected best configuration.
  match lastConfig with
  | none => return []
  | some lc => return labelsOf lc
-- impl-end

-- proof-start
theorem correct_fit_predict :
    ∀ trials : List (Int × Int), trials ≠ [] →
      problem_spec_fit_predict trials (implementation_fit_predict trials) := by
  sorry
-- proof-end

#print axioms correct_fit_predict
