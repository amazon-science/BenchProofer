import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here: serializing a type to its
-- source representation and the import statements that make that reference valid
-- is plain string manipulation over a small table of recognised kinds, modeled
-- DEEPLY below (no outside callee is consumed). The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An abstract view of a Python type object, carrying exactly the information
the serialization reads. A type is either one of the two specially-recognised
kinds, a built-in type (referenced by its bare name), or any other type
(referenced through its defining module and qualified name). -/
inductive TypeVal where
  | baseModel
  | noneType
  | builtin (name : String)
  | other (module qualname : String)
  deriving DecidableEq, BEq, Repr

/-- Identity comparison between a table entry and the value being serialized,
matching the reference-equality test used to recognise the special kinds. -/
def sameType (a b : TypeVal) : Bool := a == b

/-- Reference specification: the source representation of a type together with
the set of import statements required for that representation to be valid Python.
Modeled as an ordered list of import lines (each entry distinct; a set in the
real artifact). -/
def serializeSpec : TypeVal → String × List String
  | .baseModel => ("models.Model", ["from django.db import models"])
  | .noneType => ("type(None)", [])
  | .builtin name => (name, [])
  | .other module qualname => (module ++ "." ++ qualname, ["import " ++ module])
-- pure-end

-- post-conditions-start
/-- The result pairs the source text that references the given type with exactly
the import statements that make that text resolve. Every kind of type is pinned:
the two specially-recognised kinds and the built-in / module-qualified kinds each
map to their representation and the imports they require. -/
def problem_spec_serializeType (v : TypeVal) (result : String × List String) : Prop :=
  result = serializeSpec v
-- post-conditions-end

-- impl-start
def implementation_serializeType (v : TypeVal) : String × List String := Id.run do
  let specialCases : List (TypeVal × String × List String) :=
    [ (TypeVal.baseModel, "models.Model", ["from django.db import models"]),
      (TypeVal.noneType, "type(None)", []) ]
  for entry in specialCases do
    let (case, str, imports) := entry
    if sameType case v then
      return (str, imports)
  match v with
  | .builtin name => return (name, [])
  | .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])
  | _ => return ("", [])
-- impl-end

-- proof-start
theorem correct_serializeType : ∀ v : TypeVal,
    problem_spec_serializeType v (implementation_serializeType v) := by
  intro v
  cases v <;> rfl
-- proof-end
