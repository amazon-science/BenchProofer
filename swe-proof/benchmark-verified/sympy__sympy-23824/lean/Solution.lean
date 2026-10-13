import Mathlib
-- imports-end

/-!
Prepending a block of leading labels to each term of an additive expansion.

The setting is a rearrangement step that finishes building an additive
expression. Its data are:

  * `leadCount` — how many *leading* items sit in front of the expansion and
    must be re-attached to every term unchanged;
  * `labels`    — the labels carried by the positions, of which only the first
    `leadCount` are the leading block;
  * `terms`     — the additive terms produced so far, each represented as a list
    of labels.

The desired behavior is: attach the leading block — the first `leadCount`
labels, **in their original left-to-right order** — to the front of every term,
leaving the remainder of each term exactly as it was, and keeping the number of
terms unchanged.

The defining subtlety is *order*: the leading block must appear ahead of each
term in the same order it has among the inputs, never reversed.
-/

-- axioms-start
-- No unchanged outside callee is consumed. The transformation is expressed
-- entirely in terms of the input carriers (taking a prefix of `labels` and
-- concatenating it ahead of each term), so no `opaque`/`axiom` callee contract
-- is needed.
-- axioms-end

-- pure-start
-- No shared pure helpers are needed: the leading block is `labels.take
-- leadCount` and each term is rebuilt by list concatenation.
-- pure-end

-- post-conditions-start
/-- The result has the same number of terms as the input, and each term is the
leading block (`labels.take leadCount`, in order) followed by the original term.
Both components are pinned to the inputs, so no part of any term is left free. -/
def problem_spec_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int))
    (result : List (List Int)) : Prop :=
  result.length = terms.length ∧
  ∀ i, i < terms.length →
    result[i]! = labels.take leadCount ++ terms[i]!
-- post-conditions-end

-- impl-start
def implementation_prependLeading
    (leadCount : Nat) (labels : List Int) (terms : List (List Int)) :
    List (List Int) := Id.run do
  let lead := labels.take leadCount
  let mut out : List (List Int) := []
  for t in terms do
    out := out ++ [lead ++ t]
  return out
-- impl-end

-- proof-start
theorem helper_prependLeading (lead : List Int) (terms : List (List Int)) :
    ∀ (init : List (List Int)),
      Id.run (forIn terms init (fun t r =>
        (pure (ForInStep.yield (r ++ [lead ++ t]))))) = init ++ terms.map (fun t => lead ++ t) := by
  induction terms with
  | nil =>
    intro init
    show Id.run (pure init) = _
    rw [Id.run_pure]; simp
  | cons a as ih =>
    intro init
    rw [List.forIn_cons]
    simp only [Id.run, bind, pure] at ih ⊢
    rw [ih]
    simp [List.append_assoc]

theorem correct_prependLeading :
    ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
      problem_spec_prependLeading leadCount labels terms
        (implementation_prependLeading leadCount labels terms) := by
  intro leadCount labels terms
  unfold problem_spec_prependLeading implementation_prependLeading
  simp only [Id.run, bind]
  have h := helper_prependLeading (labels.take leadCount) terms []
  simp only [Id.run] at h
  rw [h]
  show (List.map (fun t => labels.take leadCount ++ t) terms).length = terms.length ∧
      ∀ i, i < terms.length →
        (List.map (fun t => labels.take leadCount ++ t) terms)[i]! = labels.take leadCount ++ terms[i]!
  refine ⟨by simp, ?_⟩
  intro i hi
  rw [List.getElem!_eq_getElem?_getD, List.getElem!_eq_getElem?_getD]
  rw [List.getElem?_map, List.getElem?_eq_getElem hi]
  simp
-- proof-end
