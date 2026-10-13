import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No axiomatized callees. The decision modeled here is a closed boolean function
-- of four independent observations about the parent object and the submission,
-- each abstracted to a `Bool` (an R refinement of a repo predicate; see
-- mapping.md §2). Nothing is delegated to an unchanged callee whose internal
-- behaviour the proof must assume, so there is no module-level `axiom` and no
-- axiom_check.py (meta.json G-AX skip). The refinement of the four boolean
-- observations is validated by conformance_check.py (G-CONF).
-- axioms-end

-- pure-start
/- The observable state of the parent object, restricted to the single aspect
   this operation can touch: the value of its auto-generated key attribute.

   * `keyValue` — the value currently held in that attribute: `some v` when an
     auto-generated value is present, `none` when it has been cleared so that a
     fresh value will be produced when the object is later persisted.

   Every other aspect of the parent object is untouched by this step and is
   therefore not part of this carrier (mapping.md §2). -/
structure ParentObject where
  keyValue : Option Nat
  deriving Inhabited

/- Whether the parent object's auto-generated key value must be discarded before
   the inline child form is built.

   The value is discarded only when ALL of the following hold:
   * `creatingNew`     — the parent object is being created (it does not yet
     exist), so any value carried in an auto-generated attribute is provisional
     and will be regenerated when the object is persisted;
   * `keyHasDefault`   — the attribute in question carries a model-level default
     (an auto-generated value), so there is a provisional value to discard;
   * and at least one of:
     - `keyIsPrimaryKey` — the attribute is the parent object's own primary key,
       OR
     - `noDataSubmitted` — no field data was submitted for the child form.

   When the attribute is an ALTERNATE key (not the primary key) AND field data
   WAS submitted, the value must be kept: the submitted child rows reference the
   parent through that attribute, so discarding it would sever the relation. -/
@[grind] def shouldClearKey
    (creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted : Bool) : Bool :=
  creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Prepare the parent object before an inline child form is built. The only
   effect on the parent object is on its auto-generated key attribute: that
   value is discarded EXACTLY when it is a provisional default on a parent object
   being created AND (the attribute is the parent's own primary key OR no field
   data was submitted). In every other case the attribute is left exactly as it
   was — in particular, an alternate-key default value is preserved whenever
   field data was submitted, so the submitted child rows still resolve against
   the parent.

   `inst` is the parent object and is the only mutated value; the four boolean
   observations are read-only inputs (none `mut`). Directive 5: the post-state of
   `inst` is pinned exactly on BOTH branches — cleared to `none` when the
   discard condition holds, and equal to its prior value `instOld.keyValue`
   otherwise — so no silent overwrite of the unchanged frame can slip by. -/
method prepareParentKey (mut inst : ParentObject) (creatingNew : Bool) (keyHasDefault : Bool) (keyIsPrimaryKey : Bool) (noDataSubmitted : Bool) return (u : Unit)
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = true → inst.keyValue = none
  ensures shouldClearKey creatingNew keyHasDefault keyIsPrimaryKey noDataSubmitted = false → inst.keyValue = instOld.keyValue
  do
    -- impl-start
    -- Discard the auto-generated key value only on a parent being created whose
    -- attribute carries a default, and then only when the attribute is the
    -- parent's own primary key or no field data was submitted. Otherwise leave
    -- the parent object untouched (an alternate-key value with submitted data is
    -- preserved).
    if creatingNew && keyHasDefault && (keyIsPrimaryKey || noDataSubmitted) then
      inst := { inst with keyValue := none }
    else
      return
    return
    -- impl-end

prove_correct prepareParentKey by
  loom_solve
