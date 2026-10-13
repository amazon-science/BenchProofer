import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here is a pure boolean function
--  of already-resolved metadata: for each aggregate, the per-reference flags
--  recording whether a referenced annotation uses a window function. The
--  machinery that resolves an aggregate's references and each annotation's
--  flag is unchanged and shared by both branches, so it is not consumed as an
--  outside contract. There is no `axiom` declaration and no A-reference deep
--  model of an outside callee.)
-- axioms-end

-- pure-start
/- One aggregate references a window function iff any of its referenced
   annotations uses one. `refs` lists, for a single aggregate, the per-reference
   flags (true = that referenced annotation uses a window function). A reference
   whose flag cannot be determined is treated conservatively as using one
   (handled at the boundary; mapping.md §2). -/
def aggregateUsesWindow (refs : List Bool) : Bool :=
  refs.any (fun b => b)

/- Across a whole list of aggregates, the group references a window function iff
   any single aggregate does. Front-recursive so a single unfold is available
   per loop step (the backward-fold pattern, plan §5.4). `aggregates` carries, in
   order, the per-aggregate reference-flag lists. -/
def referencesWindow : List (List Bool) → Bool
  | []        => false
  | a :: rest => aggregateUsesWindow a || referencesWindow rest

@[grind] lemma referencesWindow_nil : referencesWindow [] = false := rfl
@[grind] lemma referencesWindow_cons (a : List Bool) (rest : List (List Bool)) :
    referencesWindow (a :: rest) = (aggregateUsesWindow a || referencesWindow rest) := rfl

/- The aggregation must be evaluated inside a wrapping outer query when either
   the pre-existing structural conditions already demand it (`priorConditions`,
   a shared disjunction the change does not touch — mapping.md §1) OR any
   requested aggregate references an annotation that uses a window function.
   The latter disjunct is what this bundle pins. -/
def wrappedEvaluationDecision (priorConditions : Bool)
    (aggregates : List (List Bool)) : Bool :=
  priorConditions || referencesWindow aggregates
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method wrappedEvaluationDecisionM (priorConditions : Bool) (aggregates : List (List Bool)) return (out : Bool)
  ensures out = wrappedEvaluationDecision priorConditions aggregates
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := aggregates.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ aggregates.length
      invariant acc = referencesWindow (aggregates.drop i)
      done_with i = 0
      decreasing i
    do
      let refs := aggregates[i - 1]!
      acc := aggregateUsesWindow refs || acc
      i := i - 1
    return priorConditions || acc
    -- impl-end

/- The backward-fold step: dropping one fewer aggregate exposes the aggregate at
   `i-1` on the front, so `referencesWindow` peels one `aggregateUsesWindow`.
   This is the single goal `loom_solve` leaves for the loop body. -/
lemma referencesWindow_drop_step (aggregates : List (List Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ aggregates.length) :
    referencesWindow (aggregates.drop (i - 1))
      = (aggregateUsesWindow aggregates[i - 1]! || referencesWindow (aggregates.drop i)) := by
  have hlt : i - 1 < aggregates.length := by omega
  have hcons : aggregates.drop (i - 1) = aggregates[i - 1]! :: aggregates.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, referencesWindow_cons]

prove_correct wrappedEvaluationDecisionM by
  loom_solve
  · rw [referencesWindow_drop_step aggregates i (by omega) (by omega)]
    simp_all
  · simp_all [wrappedEvaluationDecision]
