import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no A-reference deep models. The behaviour modeled
--  here is a pure, per-element routing decision over a list of assignment values:
--  for each value, decide whether it must be wrapped as a literal operand or
--  applied directly. The decision is a function of a property the value already
--  carries (whether it is a database-side expression). The downstream machinery
--  that turns each routed operand into a per-row conditional and finally into a
--  bulk SQL statement is an UNCHANGED shared continuation reached identically
--  regardless of the routing decision, so nothing about it is assumed: it is not
--  consumed as a contract and not deep-modeled. There is no `axiom` declaration
--  and no A-reference. See refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- An assignment value as seen by the per-element routing step, recording the two
   independent classification bits the value carries:

   * `isDbExpr` — the value is a database-side expression: it knows how to resolve
     itself to SQL on its own. Such a value must be applied directly, NOT treated
     as an opaque literal.
   * `strictMatch` — a coarser, secondary classification bit also present on the
     value. It is strictly narrower than `isDbExpr`: a value may be a genuine
     database-side expression (`isDbExpr = true`) yet not be recognised by this
     coarser bit (`strictMatch = false`). It is irrelevant to the desired
     behaviour and is recorded only because real values carry more than one
     type-classification property. -/
structure AttrVal where
  isDbExpr : Bool
  strictMatch : Bool
  deriving Inhabited, DecidableEq

/- The routing plan for a sequence of assignment values: per element, `true` means
   "wrap this value as a literal operand", `false` means "apply the value directly".

   The single behaviour that matters here: a value must be wrapped as a literal
   exactly when it is NOT a database-side expression. A value that is a
   database-side expression is applied directly so it resolves on its own; wrapping
   it as a literal would freeze its surface form instead of resolving it. Grounded
   entirely in the input (directive 8): each output bit is `! isDbExpr` of the
   corresponding input element.

   Front-recursive so a single unfold is available per loop step (the Velvet fold
   pattern, plan §5.4). -/
def wrapPlan : List AttrVal → List Bool
  | []          => []
  | a :: rest   => (! a.isDbExpr) :: wrapPlan rest

@[grind] lemma wrapPlan_nil : wrapPlan [] = [] := rfl
@[grind] lemma wrapPlan_cons (a : AttrVal) (rest : List AttrVal) :
    wrapPlan (a :: rest) = (! a.isDbExpr) :: wrapPlan rest := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the routing plan for a batch of per-element assignment values. `attrs`
   is the list of values to route; it is read-only (not `mut`) and is never
   altered. The result records, for each value in order, whether it must be wrapped
   as a literal operand (`true`) or applied directly (`false`).

   Desired behaviour: a value is wrapped as a literal exactly when it is not a
   database-side expression; a database-side expression is applied directly. The
   produced plan fully determines how each value enters the (unchanged) downstream
   per-row conditional. -/
method routeOperands (attrs : List AttrVal) return (out : List Bool)
  ensures out = wrapPlan attrs
  do
    -- impl-start
    -- Pre-image skeleton: the routing bit is decided by the coarser secondary
    -- classification (`strictMatch`) instead of the database-side-expression
    -- property. Since `strictMatch` is strictly narrower than `isDbExpr`, a value
    -- that IS a database-side expression but is not recognised by the coarser bit
    -- gets wrapped as a literal. The frozen spec requires `! isDbExpr`, so
    -- prove_correct MUST fail.
    let mut result : List Bool := []
    let mut i := attrs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ attrs.length
      invariant result = wrapPlan (attrs.drop i)
      done_with i = 0
      decreasing i
    do
      let a := attrs[i - 1]!
      result := (! a.strictMatch) :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `wrapPlan` peels one routing bit. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma wrapPlan_drop_step (attrs : List AttrVal) (i : Nat)
    (hi : 0 < i) (hle : i ≤ attrs.length) :
    wrapPlan (attrs.drop (i - 1)) = (! attrs[i - 1]!.isDbExpr) :: wrapPlan (attrs.drop i) := by
  have hlt : i - 1 < attrs.length := by omega
  have hcons : attrs.drop (i - 1) = attrs[i - 1]! :: attrs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, wrapPlan_cons]

prove_correct routeOperands by
  loom_solve
  rw [wrapPlan_drop_step attrs i (by omega) (by omega)]
  simp_all
