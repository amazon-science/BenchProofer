import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms. The asynchronous bridge that runs the relation-managing
-- operation and returns its value (and its effect on the parent's collection)
-- is observationally the operation itself; its soundness is validated against
-- the real bridge by axiom_check.py (G-AX, an A-reference — mapping.md §3.1).
-- axioms-end

-- pure-start
-- pure-end

/- A parent owns a collection of related object identities (`related`). The
   three operations below each settle one object into that collection and
   report what they did. Each is a coroutine: it awaits the relation-managing
   step and yields its result, so the observable content is exactly that
   synchronous effect (mapping.md §2). -/

-- pre-conditions-start
-- pre-conditions-end
-- post-conditions-start
-- post-conditions-end

/- Settle a freshly produced object into the parent's collection, then report
   its identity. A fresh object is one not already owned by the parent. -/
method aCreate (mut related : List Nat) (newObj : Nat) return (out : Nat)
  require newObj ∉ related
  ensures out = newObj
  ensures related = relatedOld ++ [newObj]
  do
    -- impl-start
    -- Pre-image skeleton: the inherited coroutine produces the object but
    -- never settles it into the parent's collection, so `related` is left
    -- untouched. The frozen spec requires related = relatedOld ++ [newObj],
    -- so prove_correct MUST fail.
    return newObj
    -- impl-end

/- Return an object owned by the parent, producing and settling a new one only
   when no matching object is already owned. The second component reports
   whether a new object had to be produced. When a matching object already
   exists the parent's collection is left exactly as it was. -/
method aGetOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

/- Return an object owned by the parent — refreshing the matching one when it
   already exists, or producing and settling a new one otherwise. The second
   component reports whether a new object had to be produced. Refreshing an
   existing object leaves the parent's collection membership unchanged. -/
method aUpdateOrCreate (mut related : List Nat)
    (preexists : Bool) (existingObj : Nat) (newObj : Nat) return (out : Nat × Bool)
  require preexists → existingObj ∈ related
  require ¬ preexists → newObj ∉ related
  ensures preexists → (out = (existingObj, false) ∧ related = relatedOld)
  ensures ¬ preexists → (out = (newObj, true) ∧ related = relatedOld ++ [newObj])
  do
    -- impl-start
    if preexists then
      return (existingObj, false)
    else
      related := related ++ [newObj]
      return (newObj, true)
    -- impl-end

prove_correct aCreate by
  loom_solve

prove_correct aGetOrCreate by
  loom_solve

prove_correct aUpdateOrCreate by
  loom_solve
