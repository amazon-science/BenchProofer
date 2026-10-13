import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The three-valued conjunction that the containment and
   coincidence behaviors below reduce to is modeled DEEPLY in the `pure` region
   (`tand2` / `triAll`); the per-element/per-side truth values it folds are
   supplied as inputs (computed by the unchanged membership and containment
   primitives). Its agreement with the real three-valued conjunction primitive
   is validated executably — provenance + soundness check: mapping.md §3 /
   axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- Three-valued truth, modeled as `Option Bool`: `some true` = definitely true,
   `some false` = definitely false, `none` = unknown. -/

/- Binary three-valued conjunction: a definite-false on either side forces the
   whole to false (even against an unknown); otherwise an unknown anywhere makes
   the whole unknown; only two definite-trues give true. This is the dominance
   order false ≺ none ≺ true under "and". -/
def tand2 (x y : Option Bool) : Option Bool :=
  if x = some false then some false
  else if y = some false then some false
  else if x = none then none
  else if y = none then none
  else some true

/- The conjunction of a whole list of three-valued truths. Identity is
   `some true` (the empty conjunction is true). Front-recursive so a single
   unfold is available per loop step (the backward-fold pattern, plan §5.4). -/
def triAll : List (Option Bool) → Option Bool
  | []      => some true
  | c :: cs => tand2 c (triAll cs)

@[grind] lemma triAll_nil : triAll [] = some true := rfl
@[grind] lemma triAll_cons (c : Option Bool) (cs : List (Option Bool)) :
    triAll (c :: cs) = tand2 c (triAll cs) := rfl

/- `some true` is a right identity of `tand2`: conjoining with a definite-true
   leaves the other operand unchanged (case split on the operand). Lets the
   two-element conjunction in `setsCoincide` collapse to a single `tand2`. -/
@[grind] lemma tand2_true_right (x : Option Bool) : tand2 x (some true) = x := by
  unfold tand2
  rcases x with _ | b
  · rfl
  · cases b <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Whether a finite product of values is wholly contained in a finite
   collection. The desired behavior: it is contained exactly when EVERY one of
   its elements is a member of the collection, combined under three-valued
   logic — any element definitely absent makes the whole definitely not
   contained, an unknown membership anywhere makes containment unknown, and only
   all-members gives definitely contained. `memberships` carries, in enumeration
   order, the three-valued membership verdict of each product element against
   the collection (read-only: not `mut`). -/
method everyElementMember (memberships : List (Option Bool))
    return (out : Option Bool)
  ensures out = triAll memberships
  do
    -- impl-start
    let mut result : Option Bool := some true
    let mut i := memberships.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ memberships.length
      invariant result = triAll (memberships.drop i)
      done_with i = 0
      decreasing i
    do
      let m := memberships[i - 1]!
      result := tand2 m result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `triAll` peels one `tand2`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma triAll_drop_step (xs : List (Option Bool)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ xs.length) :
    triAll (xs.drop (i - 1)) = tand2 xs[i - 1]! (triAll (xs.drop i)) := by
  have hlt : i - 1 < xs.length := by omega
  have hcons : xs.drop (i - 1) = xs[i - 1]! :: xs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, triAll_cons]

prove_correct everyElementMember by
  loom_solve
  rw [triAll_drop_step memberships i (by omega) (by omega)]
  simp_all

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Whether two collections coincide. The desired behavior: they coincide exactly
   when each is contained in the other, combined under three-valued logic — if
   either containment is definitely false the verdict is definitely "not equal",
   if either is unknown the verdict is unknown, and only mutual containment gives
   definitely "equal". `subAB` is the three-valued verdict that the first is
   contained in the second; `subBA` the reverse. Both read-only. -/
method setsCoincide (subAB : Option Bool) (subBA : Option Bool) return (out : Option Bool)
  ensures out = triAll [subAB, subBA]
  do
    -- impl-start
    return tand2 subAB subBA
    -- impl-end

prove_correct setsCoincide by
  loom_solve

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Simplifying a relation whose two operands may or may not be algebraic
   expressions. The desired behavior: only when BOTH operands are algebraic
   expressions may the general simplification proceed and return its result;
   when they are not both expressions the relation must be returned UNCHANGED
   (the general path is not applicable to such operands). `bothExpr` is the
   read-only flag stating both operands are algebraic expressions; `r` is the
   original relation; `normal` is the result of the (unchanged) general
   simplification path. The relation's identity is observed via an opaque token
   (mapping.md §2). -/
method guardedSimplify (bothExpr : Bool) (r : Int) (normal : Int) return (out : Int)
  ensures bothExpr = true  → out = normal
  ensures bothExpr = false → out = r
  do
    -- impl-start
    if bothExpr then
      return normal
    else
      return r
    -- impl-end

prove_correct guardedSimplify by
  loom_solve
