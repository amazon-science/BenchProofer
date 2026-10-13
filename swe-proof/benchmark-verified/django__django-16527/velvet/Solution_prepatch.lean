import Velvet.Std
-- imports-end

/- Total correctness: the real flag computation is a straight-line pure boolean
   conjunction that always terminates, so a diverging implementation must NOT
   satisfy this spec. Partial correctness would let a non-terminating body
   discharge the exact-equality postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the flag is a pure boolean combination of the four
--  inputs, modeled deeply.)
-- axioms-end

-- pure-start
-- (No pure helpers needed.)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The administrative form offers a "duplicate this object as a new one"
   shortcut. Because that shortcut CREATES a brand-new object, it must be
   gated on the viewer's permission to ADD objects of this kind — holding the
   permission to merely edit an existing object is NOT sufficient to expose it.

   The shortcut is offered exactly when ALL of these hold simultaneously:
   the request is a normal (non-popup) request, the viewer may ADD objects,
   the page is the edit view of an existing object, and this admin opts into
   the duplicate-as-new affordance. If any one is absent, the shortcut is
   hidden.

   Two distinct permission inputs are observed — the right to ADD and the
   right to edit (CHANGE) — because the decision must DISCRIMINATE between
   them: the gate is the ADD permission alone. The four boolean inputs and
   the change/edit permission are read-only (not `mut`); the query computes a
   single boolean and mutates nothing (directive 5). All inputs and the
   result are modeled as `Bool`. -/
method showSaveAsNew (isPopup : Bool) (hasAddPermission : Bool) (hasChangePermission : Bool) (change : Bool) (saveAs : Bool) return (result : Bool)
  ensures result = (!isPopup && hasAddPermission && change && saveAs)
  do
    -- impl-start
    -- Pre-image: the shortcut was gated on the EDIT (change) permission, so a
    -- viewer with only edit rights could expose a create-a-new-object action.
    -- This skeleton returns the buggy combination and MUST fail the spec
    -- whenever the add and edit permissions differ.
    return (!isPopup && hasChangePermission && change && saveAs)
    -- impl-end

prove_correct showSaveAsNew by
  loom_solve
