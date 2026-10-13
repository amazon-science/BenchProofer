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
    let mut acc := t
    for x in lead do
      acc := x :: acc
    out := out ++ [acc]
  return out
-- impl-end

-- proof-start
theorem correct_prependLeading :
    ∀ (leadCount : Nat) (labels : List Int) (terms : List (List Int)),
      problem_spec_prependLeading leadCount labels terms
        (implementation_prependLeading leadCount labels terms) := by
  intro leadCount labels terms
  unfold problem_spec_prependLeading implementation_prependLeading
  refine ⟨?_, ?_⟩
  · simp [Id.run]
  · intro i hi
    simp [Id.run]
-- proof-end
