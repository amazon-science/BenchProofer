import Mathlib
-- imports-end

/-!
Outcome of the bounded refinement-pass loop used when post-processing collected
static files.

A storage backend post-processes the collected files in up to a configured
maximum number of refinement passes. Each pass either still rewrites some
references to other files ("produced substitutions") or leaves everything
unchanged. The loop stops as soon as a pass produces no substitutions (a
fixpoint has been reached); otherwise it stops after exhausting the configured
number of passes.

After the loop the backend inspects a single flag: whether the loop finished
while a pass was *still* producing substitutions — i.e. the configured number of
passes was reached without converging.

Modeled inputs:
  * `maxPasses` — the configured maximum number of refinement passes;
  * `passSubst i` — for each pass index `i`, whether that pass would still
    produce substitutions.

The modeled result is that post-loop flag, carried as an `Option Bool`: the
defined value `some b` reports the flag's boolean value `b` for the given
configuration, while `none` denotes the absence of any value. The result is a
defined value `some _` for every configuration — every choice of `maxPasses`
(including none) and every per-pass behavior determines the flag fully.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The modeled
-- behavior is the control flow of the bounded refinement loop itself: a flag
-- initialized before the loop, overwritten once per pass with that pass's
-- aggregated substitution outcome, with early termination when a pass produces
-- no substitutions. The per-pass aggregated outcome (the work an individual
-- pass performs over the collected files) is abstracted as the input
-- `passSubst`, so no `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- Final value of the loop's substitution flag given the still-to-run pass
indices `is`, the per-pass substitution behavior `f`, and the flag's current
value `cur`.

Front-recursive companion to the accumulator loop: a pass that produces
substitutions sets the flag to `true` and continues; a pass that produces none
sets the flag to `false` and stops (early termination); when no passes remain,
the current value stands. -/
def passLoopResult : List Nat → (Nat → Bool) → Bool → Bool
  | [], _, cur => cur
  | i :: is, f, _ => if f i then passLoopResult is f true else false
-- pure-end

-- post-conditions-start
/-- The post-loop substitution flag is fully determined by the configuration:
it is the value computed by running the configured passes in order, each pass
overwriting the flag with its own substitution outcome and the loop stopping at
the first pass that produces none. The flag is produced as a defined value
`some _` for every configuration (directive 5 frame: no configuration leaves the
result unconstrained). -/
def problem_spec_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) (result : Option Bool) : Prop :=
  result = some (passLoopResult (List.range maxPasses) passSubst false)
-- post-conditions-end

-- impl-start
def implementation_postProcess
    (maxPasses : Nat) (passSubst : Nat → Bool) : Option Bool := Id.run do
  let mut substitutions : Option Bool := some false
  for i in List.range maxPasses do
    let subst := passSubst i
    substitutions := some subst
    if ! subst then
      break
  return substitutions
-- impl-end

-- proof-start
theorem correct_postProcess :
    ∀ (maxPasses : Nat) (passSubst : Nat → Bool),
      problem_spec_postProcess maxPasses passSubst
        (implementation_postProcess maxPasses passSubst) := by
  intro maxPasses passSubst
  have helper : ∀ (is : List Nat) (cur : Bool),
      Id.run (forIn is (some cur) (fun i r =>
        if (!passSubst i) = true then pure (ForInStep.done (some (passSubst i)))
        else do
          pure PUnit.unit
          pure (ForInStep.yield (some (passSubst i))))) =
        some (passLoopResult is passSubst cur) := by
    intro is
    induction is with
    | nil => intro cur; rfl
    | cons a as ih =>
      intro cur
      rw [List.forIn_cons]
      simp only [Id.run, bind] at ih ⊢
      by_cases h : passSubst a = true
      · simp only [h, passLoopResult, Bool.not_true, Bool.false_eq_true,
          if_false, ih, if_true]
      · simp only [Bool.not_eq_true] at h
        simp only [h, passLoopResult, Bool.not_false, if_true, Bool.false_eq_true,
          if_false]
        rfl
  unfold problem_spec_postProcess implementation_postProcess
  exact helper (List.range maxPasses) false
-- proof-end
