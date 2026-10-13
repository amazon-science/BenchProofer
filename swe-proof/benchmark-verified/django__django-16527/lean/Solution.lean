import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee carries semantics the proof must assume: the button-flag
-- computation is concrete boolean algebra over the input flags, reproduced
-- directly. The container plumbing (copying the context and updating it with the
-- derived keys) is orthogonal to the boolean logic and is not modeled. The proof
-- agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
/-- The bundle of boolean inputs that drive the button-visibility computation on
an admin change/add form. -/
structure ButtonInput where
  add : Bool
  change : Bool
  isPopup : Bool
  saveAs : Bool
  showSave : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  hasAddPermission : Bool
  hasChangePermission : Bool
  hasViewPermission : Bool
  hasEditableInlineAdminFormsets : Bool
  hasDeletePermission : Bool
  showDelete : Bool
  deriving Repr, DecidableEq

/-- The bundle of derived button-visibility flags. -/
structure ButtonFlags where
  canChange : Bool
  showDeleteLink : Bool
  showSaveAsNew : Bool
  showSaveAndAddAnother : Bool
  showSaveAndContinue : Bool
  showSave : Bool
  showClose : Bool
  deriving Repr, DecidableEq

/-- Whether the form can be saved at all: editable with the relevant permission,
or it has editable inline formsets. -/
def canSave (i : ButtonInput) : Bool :=
  (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
    || i.hasEditableInlineAdminFormsets
-- pure-end

-- post-conditions-start
/-- The derived flags are exactly the boolean formulas over the inputs. Every
output component is pinned to its input formula (frame discipline). The "save as
new" flag requires the add permission, since it creates a new object. -/
def problem_spec_buttonFlags (i : ButtonInput) (result : ButtonFlags) : Prop :=
  let cs := canSave i
  result.canChange = (i.hasChangePermission || i.hasEditableInlineAdminFormsets) ∧
  result.showDeleteLink =
    (!i.isPopup && i.hasDeletePermission && i.change && i.showDelete) ∧
  result.showSaveAsNew =
    (!i.isPopup && i.hasAddPermission && i.change && i.saveAs) ∧
  result.showSaveAndAddAnother =
    (i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && cs
      && i.showSaveAndAddAnother) ∧
  result.showSaveAndContinue =
    (!i.isPopup && cs && i.hasViewPermission && i.showSaveAndContinue) ∧
  result.showSave = (i.showSave && cs) ∧
  result.showClose = (!(i.showSave && cs))
-- post-conditions-end

-- impl-start
def implementation_buttonFlags (i : ButtonInput) : ButtonFlags := Id.run do
  let canSaveV : Bool :=
    (i.hasChangePermission && i.change) || (i.hasAddPermission && i.add)
      || i.hasEditableInlineAdminFormsets
  let canSaveAndAddAnother : Bool :=
    i.hasAddPermission && !i.isPopup && (!i.saveAs || i.add) && canSaveV
      && i.showSaveAndAddAnother
  let canSaveAndContinue : Bool :=
    !i.isPopup && canSaveV && i.hasViewPermission && i.showSaveAndContinue
  let canChange : Bool := i.hasChangePermission || i.hasEditableInlineAdminFormsets
  return {
    canChange := canChange,
    showDeleteLink := !i.isPopup && i.hasDeletePermission && i.change && i.showDelete,
    showSaveAsNew := !i.isPopup && i.hasAddPermission && i.change && i.saveAs,
    showSaveAndAddAnother := canSaveAndAddAnother,
    showSaveAndContinue := canSaveAndContinue,
    showSave := i.showSave && canSaveV,
    showClose := !(i.showSave && canSaveV)
  }
-- impl-end

-- proof-start
theorem correct_buttonFlags :
    ∀ (i : ButtonInput),
    problem_spec_buttonFlags i (implementation_buttonFlags i) := by
  intro i
  refine ⟨rfl, rfl, rfl, rfl, rfl, rfl, rfl⟩
-- proof-end
