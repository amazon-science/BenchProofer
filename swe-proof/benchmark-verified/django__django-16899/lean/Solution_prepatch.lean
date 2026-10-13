import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The four resolution
-- checks that decide whether a configured admin display value is acceptable
-- (whether it is callable, an attribute of the admin object, an attribute of
-- the bound model, or a declared model field) are UNCHANGED behavior; their
-- boolean outcomes are taken as inputs (a type-only refinement, refinement.md).
-- The only changed operation — assembling the human-readable error text — is
-- modeled DEEPLY below, so no callee property is consumed. The proof agent may
-- add `_prop` axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- The identifying information carried by an admin object that appears in the
diagnostic text: the admin class name and the bound model's label. -/
structure AdminObj where
  className : String
  modelLabel : String

/-- The diagnostic text emitted when a configured display value cannot be
resolved. It cites the position label, the offending value itself, the admin
class name, and the bound model label, so the reader can see exactly which
value is at fault. -/
def errorMessage (label fieldName className modelLabel : String) : String :=
  "The value of '" ++ label ++ "' refers to '" ++ fieldName ++
  "', which is not a callable, an attribute of '" ++ className ++
  "', or an attribute of '" ++ modelLabel ++ "'."
-- pure-end

-- post-conditions-start
/-- A configured display value is acceptable when any of the four resolution
checks succeeds (it is callable, an attribute of the admin object, an attribute
of the bound model, or a declared model field); in that case no diagnostic is
produced. Otherwise exactly one diagnostic is produced, and its text is the
fully-grounded message naming the position label, the offending value, the
admin class name, and the bound model label. -/
def problem_spec_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool)
    (result : List String) : Prop :=
  if isCallable ∨ hasAttrObj ∨ hasAttrModel ∨ fieldExists then
    result = []
  else
    result = [errorMessage label fieldName obj.className obj.modelLabel]
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy) diagnostic text: it omits the offending value entirely,
so the reader cannot see which configured value is at fault. -/
def errorMessageBug (label className modelLabel : String) : String :=
  "The value of '" ++ label ++
  "' is not a callable, an attribute of '" ++ className ++
  "', or an attribute of '" ++ modelLabel ++ "'."

def implementation_checkReadonlyFieldsItem
    (obj : AdminObj) (fieldName label : String)
    (isCallable hasAttrObj hasAttrModel fieldExists : Bool) : List String :=
  Id.run do
    if isCallable then
      return []
    if hasAttrObj then
      return []
    if hasAttrModel then
      return []
    if fieldExists then
      return []
    return [errorMessageBug label obj.className obj.modelLabel]
-- impl-end

-- proof-start
theorem correct_checkReadonlyFieldsItem :
    ∀ (obj : AdminObj) (fieldName label : String)
      (isCallable hasAttrObj hasAttrModel fieldExists : Bool),
    problem_spec_checkReadonlyFieldsItem obj fieldName label
      isCallable hasAttrObj hasAttrModel fieldExists
      (implementation_checkReadonlyFieldsItem obj fieldName label
        isCallable hasAttrObj hasAttrModel fieldExists) := by
  sorry   -- carries the gold proof body; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
