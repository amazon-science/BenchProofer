import Mathlib
-- imports-end

/-!
Selecting the best result among several independent repeated attempts.

A procedure is run several times, once per entry of a given list of independent
configuration values supplied by the caller. Each value drives one self-contained
attempt that yields an *outcome* — a numeric cost together with the data the
attempt produced. The attempts do not interact: an attempt's outcome is a
function of its own configuration value alone.

The procedure keeps the single best outcome, "best" meaning lowest cost. When
several attempts tie for the lowest cost, the earliest of them (the one driven by
the configuration value appearing first in the list) is the one kept. The whole
chosen outcome is returned verbatim — both its cost and its produced data come
from one and the same attempt.

Because the selection is a deterministic function of the supplied list of
configuration values, the result does not depend on the order in which the
attempts happen to be evaluated or on how the work is distributed. The behavior
is stated abstractly as an input→output relation; the implementation and
correctness proof are supplied separately.
-/

-- axioms-start
/-- The outcome of one self-contained attempt: a numeric `cost` used to rank
attempts (lower is better) together with the `data` that attempt produced. Cost
is modeled by an exact integer because only its ORDER is observed by the
selection (the real quantity is compared with `<` / argmin only). -/
structure Outcome where
  cost : Int
  data : List Int
deriving Inhabited, DecidableEq

/-- Run one self-contained attempt for a given configuration value. This is an
UNCHANGED downstream routine: deterministic in its argument and observed only
through its returned outcome. Declared `opaque` so it can appear in the
executable implementation; the proof consumes no property of it (the selection is
correct for ANY such routine), so no `_prop` axiom is asserted. -/
opaque runTrial : Int → Outcome
-- axioms-end

-- pure-start
-- No additional pure helpers: the selection is spelled out in the impl region.
-- pure-end

-- post-conditions-start
/-- The result is the outcome of the earliest minimum-cost attempt:

* there is an index `i` into the configuration list such that the result IS the
  outcome of running attempt `i` (frame: every component of the result — cost and
  produced data — comes from this one attempt);
* no attempt has a strictly lower cost than the result (global minimum);
* every attempt strictly EARLIER than `i` has a strictly greater cost (so `i` is
  the first index attaining the minimum — the tie-break the procedure uses). -/
def problem_spec_bestTrial (trials : List Int) (result : Outcome) : Prop :=
  ∃ i : Fin trials.length,
    result = runTrial (trials.get i) ∧
    (∀ j : Fin trials.length, result.cost ≤ (runTrial (trials.get j)).cost) ∧
    (∀ j : Fin trials.length, j.val < i.val →
        result.cost < (runTrial (trials.get j)).cost)
-- post-conditions-end

-- impl-start
def implementation_bestTrial (trials : List Int) : Outcome := Id.run do
  let mut best : Option Outcome := none
  for t in trials do
    let o := runTrial t
    match best with
    | none   => best := some o
    | some b => if o.cost < b.cost then best := some o
  return best.getD default
-- impl-end


-- proof-start
/-- Pure extraction of the loop body's effect on `best`: fold accumulator update. -/
def step (b : Option Outcome) (t : Int) : Option Outcome :=
  match b with
  | none   => some (runTrial t)
  | some o => if (runTrial t).cost < o.cost then some (runTrial t) else b

/-- Loop invariant carrying the earliest-minimum-cost witness through the fold:
(a) empty prefix ⇒ accumulator is `none`;
(b) nonempty prefix ⇒ the accumulator is `some` of the outcome of the earliest
    minimum-cost trial among the processed prefix. -/
def FoldInv (processed : List Int) (b : Option Outcome) : Prop :=
  (processed = [] → b = none) ∧
  (processed ≠ [] → ∃ i : Fin processed.length,
      b = some (runTrial (processed.get i)) ∧
      (∀ j : Fin processed.length,
          (runTrial (processed.get i)).cost ≤ (runTrial (processed.get j)).cost) ∧
      (∀ j : Fin processed.length, j.val < i.val →
          (runTrial (processed.get i)).cost < (runTrial (processed.get j)).cost))

theorem getD_some (x : Outcome) : (some x).getD default = x := rfl

theorem impl_eq_foldl (trials : List Int) :
    implementation_bestTrial trials = (trials.foldl step none).getD default := by
  simp only [implementation_bestTrial, Id.run, bind_pure_comp, map_pure]
  suffices h : ∀ (init : Option Outcome),
      (forIn trials init fun t r =>
        (match r with
        | none => (pure (ForInStep.yield (some (runTrial t))) : Id (ForInStep (Option Outcome)))
        | some b => if (runTrial t).cost < b.cost then pure (ForInStep.yield (some (runTrial t))) else pure (ForInStep.yield r))) = List.foldl step init trials by
    rw [h none]; rfl
  induction trials with
  | nil => intro init; rfl
  | cons h t ih =>
    intro init
    rw [List.forIn_cons, List.foldl_cons]
    cases init with
    | none => simp only [pure_bind, step]; rw [ih]
    | some b =>
      by_cases hc : (runTrial h).cost < b.cost
      · simp only [pure_bind, step, hc, if_true]; rw [ih]
      · simp only [pure_bind, step, hc, if_false]; rw [ih]

theorem FoldInv_init : FoldInv [] none := by
  constructor
  · intro _; rfl
  · intro h; exact absurd rfl h

theorem FoldInv_step (P : List Int) (t : Int) (b : Option Outcome) :
    FoldInv P b → FoldInv (P ++ [t]) (step b t) := by
  intro hInv
  refine ⟨fun hEmpty => absurd hEmpty (by simp), fun _ => ?_⟩
  by_cases hP : P = []
  · -- Empty prefix: b = none, so step none t = some (runTrial t)
    subst hP
    have hb : b = none := hInv.1 rfl
    subst hb
    simp only [step, List.nil_append]
    refine ⟨⟨0, by simp⟩, ?_, ?_, ?_⟩
    · simp
    · intro j
      simp only [List.get_eq_getElem]
      have hj0 : (j : ℕ) = 0 := by
        have := j.isLt; simp only [List.length_cons, List.length_nil] at this; omega
      simp only [hj0]
      exact le_refl _
    · intro j hj
      exact absurd hj (Nat.not_lt_zero _)
  · -- Nonempty prefix
    obtain ⟨i, hb, hmin, hearl⟩ := hInv.2 hP
    simp only [List.get_eq_getElem] at hb hmin hearl
    have hi := i.isLt
    have hilt : i.val < (P ++ [t]).length := by
      simp only [List.length_append, List.length_cons, List.length_nil]; omega
    by_cases hcase : (runTrial t).cost < (runTrial P[i.val]).cost
    · -- new trial wins; best becomes some (runTrial t), witness = last index
      have hstep : step b t = some (runTrial t) := by
        rw [hb]; simp only [step, if_pos hcase]
      rw [hstep]
      refine ⟨⟨P.length, by simp⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          have hm := hmin ⟨j.val, hj⟩
          exact le_of_lt (lt_of_lt_of_le hcase hm)
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_concat_length (l := P) (a := t) rfl]
        rw [List.getElem_append_left hj]
        have hm := hmin ⟨j.val, hj⟩
        exact lt_of_lt_of_le hcase hm
    · -- old best wins; accumulator unchanged, witness = i
      push_neg at hcase
      have hstep : step b t = b := by
        rw [hb]; simp only [step, if_neg (not_lt.mpr hcase)]
      rw [hstep, hb]
      refine ⟨⟨i.val, hilt⟩, ?_, ?_, ?_⟩
      · simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
      · intro j
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        by_cases hj : j.val < P.length
        · rw [List.getElem_append_left hj]
          exact hmin ⟨j.val, hj⟩
        · have hjeq : j.val = P.length := by
            have hjl := j.isLt
            simp only [List.length_append, List.length_cons, List.length_nil] at hjl
            omega
          rw [List.getElem_concat_length (l := P) (a := t) hjeq]
          exact hcase
      · intro j hj
        simp only [List.get_eq_getElem]
        rw [List.getElem_append_left hi]
        have hjP : j.val < P.length := lt_trans hj hi
        rw [List.getElem_append_left hjP]
        exact hearl ⟨j.val, hjP⟩ hj

theorem FoldInv_holds (L : List Int) : FoldInv L (L.foldl step none) := by
  induction L using List.reverseRecOn with
  | nil => exact FoldInv_init
  | append_singleton P t IH =>
    rw [List.foldl_concat]
    exact FoldInv_step P t (P.foldl step none) IH

theorem nonempty_gives_some (trials : List Int) (h : trials ≠ []) :
    ∃ iBest : Fin trials.length,
      (trials.foldl step none) = some (runTrial (trials.get iBest)) ∧
      (∀ j : Fin trials.length,
          (runTrial (trials.get iBest)).cost ≤ (runTrial (trials.get j)).cost) ∧
      (∀ j : Fin trials.length, j.val < iBest.val →
          (runTrial (trials.get iBest)).cost < (runTrial (trials.get j)).cost) :=
  (FoldInv_holds trials).2 h

theorem result_is_trial_i (trials : List Int) (iBest : Fin trials.length)
    (hfold : (trials.foldl step none) = some (runTrial (trials.get iBest))) :
    implementation_bestTrial trials = runTrial (trials.get iBest) := by
  rw [impl_eq_foldl, hfold, getD_some]

theorem correct_bestTrial :
    ∀ (trials : List Int), trials ≠ [] →
      problem_spec_bestTrial trials (implementation_bestTrial trials) := by
  intro trials h
  obtain ⟨iBest, hfold, hmin, hbefore⟩ := nonempty_gives_some trials h
  have hres := result_is_trial_i trials iBest hfold
  refine ⟨iBest, ?_, ?_, ?_⟩
  · exact hres
  · intro j; rw [hres]; exact hmin j
  · intro j hj; rw [hres]; exact hbefore j hj

-- proof-end
