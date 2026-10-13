import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callee. Whether any store-mutation work is emitted is decided
--  entirely by the identifier-equality comparison, which is precisely the
--  behaviour under specification — modeled DEEPLY below (the equality guard),
--  NOT axiomatized or A-referenced (SPEC_GUIDE §0.7). The resolved before/after
--  identifiers are taken as free inputs; how they are looked up is an UNCHANGED
--  resolution whose internals the proof does not depend on, so no contract is
--  consumed.)
-- axioms-end

-- pure-start
/- A single unit of store-mutation work emitted when the relabeling proceeds.
   The exact code value is irrelevant — only its presence is observable to the
   layer below — so a constant marker is used. -/
def applyOp : Int := 1
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- A relabeling of a stored object is applied to its backing store, driven
   entirely by whether the stored identifier actually changes. The operation is
   handed the identifier the object carries before the relabeling (`beforeId`)
   and the one it carries after (`afterId`).

   (1) When the before- and after- identifiers are the SAME, the operation is
       observationally inert: it must issue NO store-mutation work at all. The
       emitted schedule of operations is EMPTY. (Applying a relabeling that does
       not actually change the identifier must be a no-op, so that re-applying
       it onto an already-relabeled store is harmless.)

   (2) When the two identifiers DIFFER, the operation is NOT inert: it emits at
       least one store-mutation operation. The emitted schedule is NON-EMPTY.

   The only behaviour that distinguishes a correct operation from the defect is
   this zero-vs-nonzero schedule outcome: emit nothing exactly when the
   identifier is unchanged, emit something otherwise. The exact count and order
   of the operations emitted on the proceeding branch is NOT pinned by the spec.

   The two identifiers are modeled as `Int` (only their equality is observable
   to the layer below). The emitted schedule is a `List Int` of operation codes.
   Both identifiers are read-only inputs (neither is `mut`; the decision mutates
   nothing — directive 5). -/
method relabelSchedule (beforeId : Int) (afterId : Int) return (out : List Int)
  ensures beforeId = afterId → out = []
  ensures beforeId ≠ afterId → out ≠ []
  do
    -- impl-start
    -- Don't act when the identifier is not changed: inert ⇒ empty schedule.
    if beforeId = afterId then
      return []
    else
      -- The relabeling proceeds: emit the store-mutation work (one unit here;
      -- the spec consumes only its non-emptiness).
      return [applyOp]
    -- impl-end

prove_correct relabelSchedule by
  loom_solve
