import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The ordinary reduction decision that applies to every
--  other pairing — the inherited, UNCHANGED behaviour delegated to the base
--  operation — is taken as a FREE INPUT `inheritedOutcome`, so the spec makes no
--  behavioural claim about it and holds for every value. Nothing here needs
--  validation against a real callee, hence no G-AX.)
-- axioms-end

-- pure-start
/- The outcome of asking whether an operation can be combined with the operation
   that immediately follows it in a plan. `cancel` denotes the empty replacement
   (the two operations annihilate and are dropped from the plan); `inherited tag`
   stands for any OTHER outcome of the ordinary, unchanged reduction decision (a
   keep / a non-empty replacement / "cannot combine"). The `tag` makes the
   non-`cancel` outcomes an open domain, so a consumer cannot conflate them with
   the empty-replacement outcome. -/
inductive Reduction where
  | cancel
  | inherited (tag : Nat)
  deriving DecidableEq, Inhabited

/- The shape of the operation that follows. `removesIndex name` is an operation
   that removes the index identified by `name`; `other` is anything else. Only
   this much of the following operation is consulted by the decision below. -/
inductive NextOp where
  | removesIndex (name : List Char)
  | other
  deriving DecidableEq, Inhabited

/- The decisive condition: the operation that follows removes the very index this
   operation adds — i.e. it is an index-removal whose target name equals the
   added index's name. -/
def removesAddedIndex (addedName : List Char) (next : NextOp) : Bool :=
  match next with
  | NextOp.removesIndex name => decide (name = addedName)
  | NextOp.other             => false
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Combine an index-addition with the operation that immediately follows it.

   Desired behaviour: when the following operation removes the very index that was
   just added (same index name), the two operations cancel and the plan keeps
   nothing in their place (`cancel`). In every other situation the result is the
   ordinary, unchanged reduction decision (`inheritedOutcome`).

   `addedName` (the added index's name), `next` (the following operation), and
   `inheritedOutcome` (the ordinary decision for every other pairing) are
   read-only inputs; nothing handed in is mutated (directive 5). -/
method reduceAddIndex (addedName : List Char) (next : NextOp) (inheritedOutcome : Reduction)
    return (out : Reduction)
  ensures out = (if removesAddedIndex addedName next then Reduction.cancel else inheritedOutcome)
  do
    -- impl-start
    if removesAddedIndex addedName next then
      return Reduction.cancel
    else
      return inheritedOutcome
    -- impl-end

prove_correct reduceAddIndex by
  loom_solve
