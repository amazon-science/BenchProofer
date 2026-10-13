import Mathlib
-- imports-end

/-!
Relative complement of a finite collection against another set, governed by a
three-valued membership test.

We are given a finite ordered collection of candidate elements and, for each
candidate, the outcome of testing whether it belongs to the set we are
subtracting. That test is three-valued: it may report a definite "yes", a
definite "no", or be undetermined (no definite answer is available, e.g. when
the candidate is a free symbol whose membership cannot be decided).

Forming the difference splits the candidates by that outcome:

* a candidate whose membership is a definite "yes" is excluded entirely — it
  appears in neither part of the result;
* a candidate whose membership is a definite "no" is retained as an explicit
  member of the difference;
* a candidate whose membership is undetermined is set aside separately, as a
  member that can be neither confirmed nor ruled out — it must NOT be treated as
  a confirmed member of the difference.

The result records the two retained groups, each in the candidates' original
order. Retaining undetermined candidates apart from confirmed-out candidates is
the whole point: undetermined membership is not the same as confirmed exclusion.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The three-valued membership outcome
-- for each candidate is supplied as an input classifier (`contains`), so the
-- behavior is grounded directly in the inputs and the proof needs no callee
-- contract. (G-AX is a skip stub.)
-- axioms-end

-- pure-start
/-- The two retained groups of a membership-governed difference:
`kept` are the candidates with a definite "no" outcome (confirmed members of the
difference), `unresolved` are the candidates with an undetermined outcome (set
aside, neither confirmed in nor out). Candidates with a definite "yes" appear in
neither group. -/
structure ComplementResult (α : Type) where
  kept : List α
  unresolved : List α
deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The difference partitions the candidates by their three-valued membership
outcome: `kept` is exactly the subsequence of candidates whose outcome is a
definite "no" (`some false`), and `unresolved` is exactly the subsequence whose
outcome is undetermined (`none`); both preserve the input order. Candidates with
a definite "yes" (`some true`) occur in neither group. -/
def problem_spec_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α)
    (result : ComplementResult α) : Prop :=
  result.kept = other.filter (fun el => contains el = some false) ∧
  result.unresolved = other.filter (fun el => contains el = none)
-- post-conditions-end

-- impl-start
def implementation_partitionByMembership {α : Type}
    (contains : α → Option Bool) (other : List α) :
    ComplementResult α := Id.run do
  let mut kept : List α := []
  let mut unresolved : List α := []
  for el in other do
    match contains el with
    | some true => pure ()            -- definite member: dropped from both groups
    | some false => kept := kept ++ [el]
    | none => unresolved := unresolved ++ [el]
  return { kept := kept, unresolved := unresolved }
-- impl-end


-- proof-start
theorem correct_partitionByMembership {α : Type} :
    ∀ (contains : α → Option Bool) (other : List α),
      problem_spec_partitionByMembership contains other
        (implementation_partitionByMembership contains other) := by
  intro contains other
  simp only [problem_spec_partitionByMembership, implementation_partitionByMembership, Id.run,
    bind_pure_comp, map_pure]
  have key : ∀ (l : List α) (k u : List α),
      (forIn l ((⟨k, u⟩ : MProd (List α) (List α)) : MProd (List α) (List α)) (fun el r =>
        match contains el with
        | some true => pure (ForInStep.yield ⟨r.fst, r.snd⟩)
        | some false => pure (ForInStep.yield ⟨r.fst ++ [el], r.snd⟩)
        | none => pure (ForInStep.yield ⟨r.fst, r.snd ++ [el]⟩)) : Id (MProd (List α) (List α)))
      = (⟨k ++ l.filter (fun el => contains el = some false),
          u ++ l.filter (fun el => contains el = none)⟩ : MProd (List α) (List α)) := by
    intro l
    induction l with
    | nil =>
      intro k u
      simp only [List.forIn_nil, List.filter_nil, List.append_nil]
      rfl
    | cons hd tl ih =>
      intro k u
      simp only [List.forIn_cons, List.filter_cons]
      rcases h : contains hd with _ | b
      · simp only [ih]
        simp
      · cases b
        · simp only [ih]
          simp
        · simp only [ih]
          simp
  rw [key other [] []]
  refine ⟨?_, ?_⟩ <;> rfl

-- proof-end
