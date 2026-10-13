import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The grouping-column set is assembled from contributions
-- that are explicit, observable inputs of the routine: the grouping base, the
-- selected columns (already pruned of those reachable by reference), the
-- ordering terms, and the filter columns. The per-term column lists are taken
-- as given (each term already carries the columns it would contribute and a
-- flag marking it as a mere reference to the selected set); the routine does
-- not recompute them, so there is no unchanged library callee whose contract
-- the proof must assume. The whole decision is modeled DEEPLY over these inputs.
-- axioms-end

-- pure-start
/- One ordering term, abstracted to exactly the two facts that decide its
   contribution to the grouping set: the columns it would contribute
   (`cols`), and whether it is merely a reference back into the selected set
   (`isRef`). A term that is a reference contributes nothing — its columns are
   already part of the grouping set by virtue of being selected. -/
structure OrderTerm where
  cols : List Int
  isRef : Bool
deriving Inhabited

/- The grouping columns contributed by the ordering terms: each term that is
   NOT a back-reference contributes its columns, in order; a reference term
   contributes nothing. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern). -/
def orderFold : List OrderTerm → List Int
  | []      => []
  | t :: ts => (if t.isRef then [] else t.cols) ++ orderFold ts

@[grind] lemma orderFold_nil : orderFold [] = [] := rfl
@[grind] lemma orderFold_cons (t : OrderTerm) (ts : List OrderTerm) :
    orderFold (t :: ts) = (if t.isRef then [] else t.cols) ++ orderFold ts := rfl

/- The full grouping set: the grouping base, then the selected columns, then —
   only when the ordering was requested explicitly rather than derived from the
   model's default ordering — the ordering-term columns, then the filter
   columns. The single behavioural distinction this routine must honour is that
   a default-ordering-derived ordering contributes NO columns to the grouping
   set: its terms exist only to sort rows, never to widen the grouping. -/
def groupingSet (baseCols selectCols : List Int) (orderTerms : List OrderTerm)
    (havingCols : List Int) (metaOrdering : Bool) : List Int :=
  baseCols ++ selectCols
    ++ (if metaOrdering then [] else orderFold orderTerms)
    ++ havingCols
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the columns a row-grouping clause must contain. The set is built by
   concatenating four contributions, in order:

   - `baseCols`    — the explicit grouping base (the minimal set to group by);
   - `selectCols`  — the selected columns that are not reachable purely by
                     reference (already pruned by the caller);
   - the ordering-term columns — but ONLY when `metaOrdering` is `false`, i.e.
                     when the ordering was requested explicitly. When the
                     ordering is derived from the model's default ordering
                     (`metaOrdering = true`), it contributes nothing: its terms
                     order the rows without widening the grouping;
   - `havingCols`  — the columns required by row-filtering predicates.

   All five parameters are read-only (none is `mut`): the routine builds a fresh
   result and mutates none of them (directive 5). The result is the assembled
   column list, in contribution order (later de-duplication is observationally
   the identity on which columns are present and is performed downstream). -/
method groupingColumns (baseCols : List Int) (selectCols : List Int)
    (orderTerms : List OrderTerm) (havingCols : List Int) (metaOrdering : Bool)
    return (out : List Int)
  ensures out = groupingSet baseCols selectCols orderTerms havingCols metaOrdering
  ensures metaOrdering = true → out = baseCols ++ selectCols ++ havingCols
  do
    -- impl-start
    -- Pre-image skeleton: the ordering-term columns are appended to the
    -- grouping set UNCONDITIONALLY — the `metaOrdering` guard is absent. The
    -- ordering terms always widen the grouping set, even when the ordering was
    -- derived from the model's default ordering. The frozen spec adds them only
    -- when `metaOrdering = false`, so `prove_correct` MUST fail; the divergence
    -- is exactly the `metaOrdering = true → out = baseCols ++ selectCols ++
    -- havingCols` clause (the reported bug: default ordering wrongly widens the
    -- grouping, corrupting the aggregation).
    let mut order : List Int := []
    let mut i := orderTerms.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ orderTerms.length
      invariant order = orderFold (orderTerms.drop i)
      done_with i = 0
      decreasing i
    do
      let t := orderTerms[i - 1]!
      order := (if t.isRef then [] else t.cols) ++ order
      i := i - 1
    return baseCols ++ selectCols ++ order ++ havingCols
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `orderFold` peels one contribution. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma orderFold_drop_step (orderTerms : List OrderTerm) (i : Nat)
    (hi : 0 < i) (hle : i ≤ orderTerms.length) :
    orderFold (orderTerms.drop (i - 1)) =
      (if (orderTerms[i - 1]!).isRef then [] else (orderTerms[i - 1]!).cols)
        ++ orderFold (orderTerms.drop i) := by
  have hlt : i - 1 < orderTerms.length := by omega
  have hcons : orderTerms.drop (i - 1) = orderTerms[i - 1]! :: orderTerms.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, orderFold_cons]

prove_correct groupingColumns by
  loom_solve
  · rw [orderFold_drop_step orderTerms i (by omega) (by omega)]
    simp_all
  all_goals simp_all [groupingSet]
